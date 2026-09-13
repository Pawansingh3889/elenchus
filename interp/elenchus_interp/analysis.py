"""What Qwen3-0.6B does with a captured conduct prompt, in two separate requests.

A reading (``Analyzer.analyse``):

1. The prompt is read once with the fused attention kernel, and cached. Then only the
   shared start of a tool call (``<tool_call>`` and ``{"name": "``) is read on top of that
   cache with eager attention, stopping at the moment the tool's name is about to be
   written. That short step is where the logit lens reads every layer's leaning between
   the offered tools, and where a hook on every attention module keeps that moment's
   attention row as a share per section.

   Why two kernels: reading the whole prompt eagerly materialises every layer's full
   attention matrix. Measured on one layer at 3,500 tokens, the fused kernel reads about
   three times faster in a sixth of the memory, and the eager step over a handful of
   tokens costs next to nothing while still handing its weights to the hooks. On the
   whole model the change took a 3,492-token prompt from 103 s and 7.1 GB to 81 s and
   4.8 GB on this laptop's CPU, where the feed-forward layers, not attention, are most of
   the remaining time.
2. The name of each offered tool is scored from that cache, token by token, cropping the
   cache back after each, so every tool costs a few tokens, not a prompt.

An attribution (``Analyzer.attribute``): gradient times input toward the tool the hosted
model actually called, on the fused kernel, with gradient checkpointing so a backward pass
over a long prompt fits in a laptop's memory. It is its own request because it is most of
the cost (285 s against the reading's 85 s for that prompt), so the pages that need only
the reading are never kept waiting for it.

Nothing here is about the hosted model's internals. It is how a small open model reads the
same prompt, and how often it picks the same tool is reported so a reader knows how far to
trust it as a stand-in.
"""

import math
import time
from typing import Any

import torch

from elenchus_interp.prompt import TEMPLATE, Rendered, render
from elenchus_interp.schemas import (
    AnalyseRequest,
    Analysis,
    AttributeRequest,
    Attribution,
    AttributionResult,
    LayerAttention,
    LayerReading,
    ReadTimings,
    Section,
    SectionAttribution,
    TokenWeight,
    ToolScore,
    WordScore,
)

TOP_TOKENS = 20
# The attention kernel every pass uses except the short step whose attention is kept.
FUSED = "sdpa"


class PromptTooLongError(ValueError):
    """Longer than the service is configured to read on this machine."""


def _ms(since: float) -> int:
    return int((time.monotonic() - since) * 1000)


def _common_prefix(sequences: list[list[int]]) -> list[int]:
    shortest = min(sequences, key=len)
    for index, token in enumerate(shortest):
        if any(sequence[index] != token for sequence in sequences):
            return shortest[:index]
    return list(shortest)


def _softmax(values: dict[str, float]) -> dict[str, float]:
    peak = max(values.values())
    weights = {name: math.exp(value - peak) for name, value in values.items()}
    total = sum(weights.values())
    return {name: weight / total for name, weight in weights.items()}


class Analyzer:
    def __init__(
        self, model: Any, tokenizer: Any, *, name: str, revision: str, max_prompt_tokens: int
    ) -> None:
        self.model = model.eval()
        # Only the input embeddings need a gradient for attribution; the weights never do,
        # and leaving them trainable would double the backward pass's memory.
        self.model.requires_grad_(False)
        self.tokenizer = tokenizer
        self.name = name
        self.revision = revision
        self.max_prompt_tokens = max_prompt_tokens
        parameter = next(model.parameters())
        self.device = parameter.device
        self.dtype = parameter.dtype
        self.tool_call_id = tokenizer.convert_tokens_to_ids("<tool_call>")
        if not isinstance(self.tool_call_id, int) or self.tool_call_id == tokenizer.unk_token_id:
            raise ValueError("this tokenizer has no <tool_call> token; it is not a Qwen tokenizer")

    def _continuation(self, name: str) -> list[int]:
        ids: list[int] = self.tokenizer.encode(
            f'<tool_call>\n{{"name": "{name}"', add_special_tokens=False
        )
        return ids

    def _prepare(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> tuple[Rendered, list[str], int]:
        started = time.monotonic()
        rendered = render(self.tokenizer, messages, tools)
        render_ms = _ms(started)
        if len(rendered.ids) > self.max_prompt_tokens:
            raise PromptTooLongError(
                f"the prompt is {len(rendered.ids)} tokens; this service reads at most "
                f"{self.max_prompt_tokens}"
            )
        return rendered, [str(tool["function"]["name"]) for tool in tools], render_ms

    def analyse(self, request: AnalyseRequest) -> Analysis:
        started = time.monotonic()
        rendered, names, render_ms = self._prepare(request.messages, request.tools)
        continuations = {name: self._continuation(name) for name in names}
        common = _common_prefix(list(continuations.values()))
        if not common or any(len(ids) <= len(common) for ids in continuations.values()):
            raise ValueError("two offered tools tokenize identically; they cannot be told apart")

        reading = time.monotonic()
        layers, attention, attended, calls_a_tool, cache, last_logprobs, base_len = self._read(
            rendered, common, continuations, names
        )
        read_ms = _ms(reading)

        scoring = time.monotonic()
        scores = self._score(continuations, common, cache, last_logprobs, base_len)
        tools_ms = _ms(scoring)
        del cache
        probabilities = _softmax(scores)

        return Analysis(
            model=self.name,
            revision=self.revision,
            device=str(self.device),
            dtype=str(self.dtype).removeprefix("torch."),
            prompt_tokens=len(rendered.ids),
            sections=self._sections(rendered),
            calls_a_tool=calls_a_tool,
            tools=[
                ToolScore(name=name, logprob=scores[name], probability=probabilities[name])
                for name in names
            ],
            pick=max(names, key=lambda name: scores[name]),
            layers=layers,
            attention=attention,
            attended_tokens=attended,
            timings=ReadTimings(
                render_ms=render_ms, read_ms=read_ms, tools_ms=tools_ms, total_ms=_ms(started)
            ),
        )

    def attribute(self, request: AttributeRequest) -> AttributionResult:
        started = time.monotonic()
        rendered, names, render_ms = self._prepare(request.messages, request.tools)
        if request.target_tool not in names:
            raise ValueError(f"target tool {request.target_tool!r} was not offered: {names}")
        attributing = time.monotonic()
        attribution = self._attribute(
            rendered, self._continuation(request.target_tool), request.target_tool
        )
        return AttributionResult(
            model=self.name,
            revision=self.revision,
            device=str(self.device),
            prompt_tokens=len(rendered.ids),
            attribution=attribution,
            render_ms=render_ms,
            attribution_ms=_ms(attributing),
            total_ms=_ms(started),
        )

    def _sections(self, rendered: Rendered) -> list[Section]:
        counted = {key: rendered.token_sections.count(key) for key in set(rendered.token_sections)}
        sections = [
            Section(
                key=s.key, label=s.label, kind=s.kind, role=s.role, tokens=counted.get(s.key, 0)
            )
            for s in rendered.sections
        ]
        sections.append(
            Section(
                key=TEMPLATE,
                label="Chat template",
                kind="template",
                role=None,
                tokens=counted.get(TEMPLATE, 0),
            )
        )
        return sections

    def _token_text(self, token_id: int) -> str:
        text: str = self.tokenizer.decode([token_id])
        return text

    def _read(
        self,
        rendered: Rendered,
        common: list[int],
        continuations: dict[str, list[int]],
        names: list[str],
    ) -> tuple[
        list[LayerReading], list[LayerAttention], list[TokenWeight], float, Any, torch.Tensor, int
    ]:
        prompt_len = len(rendered.ids)
        rows: list[torch.Tensor] = []

        def keep_last_row(_module: Any, _args: Any, output: Any) -> Any:
            weights = output[1]
            if weights is None:
                raise RuntimeError("no attention weights: the decision step must run eagerly")
            rows.append(weights[0, :, -1, :prompt_len].float().mean(dim=0).cpu())
            return (output[0], None, *output[2:])

        with torch.no_grad():
            prompt_out = self.model(
                input_ids=torch.tensor([rendered.ids], device=self.device),
                use_cache=True,
                logits_to_keep=1,
            )
        calls_a_tool = float(
            torch.softmax(prompt_out.logits[0, -1].float(), dim=-1)[self.tool_call_id]
        )
        cache = prompt_out.past_key_values
        del prompt_out

        handles = [
            layer.self_attn.register_forward_hook(keep_last_row)
            for layer in self.model.model.layers
        ]
        self.model.set_attn_implementation("eager")
        try:
            with torch.no_grad():
                out = self.model(
                    input_ids=torch.tensor([common], device=self.device),
                    past_key_values=cache,
                    use_cache=True,
                    output_hidden_states=True,
                    logits_to_keep=1,
                )
        finally:
            self.model.set_attn_implementation(FUSED)
            for handle in handles:
                handle.remove()

        logits = out.logits[0].float()
        last_logprobs = torch.log_softmax(logits[-1], dim=-1)

        hidden = out.hidden_states
        norm = self.model.model.norm
        head = self.model.lm_head
        # Whether the last hidden state is already normalised differs between versions of
        # the library, so it is checked against the real logits rather than assumed.
        with torch.no_grad():
            final = hidden[-1][0, -1]
            final_is_normed = bool(torch.allclose(head(final).float(), logits[-1], atol=1e-3))
            first_ids = {name: continuations[name][len(common)] for name in names}
            layers = []
            for index in range(1, len(hidden)):
                state = hidden[index][0, -1]
                normed = state if (index == len(hidden) - 1 and final_is_normed) else norm(state)
                lens = head(normed).float()
                tool_logits = {name: float(lens[token]) for name, token in first_ids.items()}
                layers.append(
                    LayerReading(
                        layer=index,
                        norm=float(state.float().norm()),
                        tool_probabilities=_softmax(tool_logits),
                        top_token=self._token_text(int(lens.argmax())),
                    )
                )

        attention = []
        for index, row in enumerate(rows, start=1):
            total = float(row.sum())
            shares: dict[str, float] = {}
            for position, weight in enumerate(row.tolist()):
                key = rendered.token_sections[position]
                shares[key] = shares.get(key, 0.0) + weight / total
            attention.append(LayerAttention(layer=index, shares=shares))

        mean_row = torch.stack(rows).mean(dim=0)
        order = torch.argsort(mean_row, descending=True).tolist()
        attended = [
            TokenWeight(
                position=position,
                text=self._token_text(rendered.ids[position]),
                section=rendered.token_sections[position],
                weight=float(mean_row[position]),
            )
            for position in order
            # The template's own tokens soak up attention as a resting place; the words
            # worth reading are the ones the prompt's authors and respondents wrote.
            if rendered.token_sections[position] != TEMPLATE
        ][:TOP_TOKENS]
        base_len = prompt_len + len(common)
        return layers, attention, attended, calls_a_tool, cache, last_logprobs, base_len

    def _score(
        self,
        continuations: dict[str, list[int]],
        common: list[int],
        cache: Any,
        last_logprobs: torch.Tensor,
        base_len: int,
    ) -> dict[str, float]:
        scores = {}
        for name, ids in continuations.items():
            rest = ids[len(common) :]
            total = float(last_logprobs[rest[0]])
            if len(rest) > 1:
                with torch.no_grad():
                    step = self.model(
                        input_ids=torch.tensor([rest[:-1]], device=self.device),
                        past_key_values=cache,
                        use_cache=True,
                    )
                logprobs = torch.log_softmax(step.logits[0].float(), dim=-1)
                total += sum(float(logprobs[i, rest[i + 1]]) for i in range(len(rest) - 1))
                # A negative count removes that many tokens; the positive form goes in 5.18.
                cache.crop(-(len(rest) - 1))
                assert cache.get_seq_length() == base_len
            scores[name] = total
        return scores

    def _attribute(self, rendered: Rendered, continuation: list[int], target: str) -> Attribution:
        prompt_len = len(rendered.ids)
        ids = torch.tensor([rendered.ids + continuation], device=self.device)
        embedding = self.model.get_input_embeddings()
        with torch.no_grad():
            base = embedding(ids)
        # Detached, so the gradient lands here whatever hooks the library left on the
        # embedding layer: enabling checkpointing installs one that marks the embedding
        # output as needing a gradient, and it outlives disabling checkpointing. Without
        # this, every attribution after the first reads an empty gradient.
        inputs = base.detach().clone().requires_grad_(True)
        self.model.gradient_checkpointing_enable()
        # Checkpointing only engages in training mode. Qwen3 has no dropout, so this changes
        # memory, not the numbers.
        self.model.train()
        try:
            out = self.model(
                inputs_embeds=inputs, use_cache=False, logits_to_keep=len(continuation) + 1
            )
            logprobs = torch.log_softmax(out.logits[0, :-1].float(), dim=-1)
            target_logprob = sum(logprobs[index, token] for index, token in enumerate(continuation))
            assert isinstance(target_logprob, torch.Tensor)
            # torch ships Tensor.backward without annotations: an external gap, not ours.
            target_logprob.backward()  # type: ignore[no-untyped-call]
        finally:
            self.model.eval()
            self.model.gradient_checkpointing_disable()
        assert inputs.grad is not None
        scores = (inputs.grad[0, :prompt_len].float() * base[0, :prompt_len].float()).sum(dim=-1)
        values: list[float] = scores.tolist()
        magnitude = sum(abs(value) for value in values) or 1.0

        sections: dict[str, SectionAttribution] = {}
        for position, value in enumerate(values):
            key = rendered.token_sections[position]
            current = sections.get(key, SectionAttribution(positive=0.0, negative=0.0))
            share = value / magnitude
            sections[key] = SectionAttribution(
                positive=current.positive + max(share, 0.0),
                negative=current.negative + min(share, 0.0),
            )

        order = sorted(range(prompt_len), key=lambda i: abs(values[i]), reverse=True)
        tokens = [
            TokenWeight(
                position=i,
                text=self._token_text(rendered.ids[i]),
                section=rendered.token_sections[i],
                weight=values[i],
            )
            for i in order
            if rendered.token_sections[i] != TEMPLATE
        ][:TOP_TOKENS]

        return Attribution(
            target=target,
            sections=sections,
            tokens=tokens,
            respondent_words=self._respondent_words(rendered, values),
        )

    def _respondent_words(self, rendered: Rendered, values: list[float]) -> list[WordScore]:
        """The last thing the respondent said, word by word, with each word's attribution."""
        last = next(
            (
                s.key
                for s in reversed(rendered.sections)
                if s.kind == "message" and s.role == "user"
            ),
            None,
        )
        if last is None:
            return []
        words: list[WordScore] = []
        for position, key in enumerate(rendered.token_sections):
            if key != last:
                continue
            piece = self._token_text(rendered.ids[position])
            if not words or piece[:1].isspace():
                words.append(WordScore(text=piece.strip(), score=values[position]))
            else:
                previous = words[-1]
                words[-1] = WordScore(
                    text=previous.text + piece, score=previous.score + values[position]
                )
        return [word for word in words if word.text]


def load(name: str, revision: str, max_prompt_tokens: int) -> Analyzer:
    """The pinned model and tokenizer, on the fastest device this machine has."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    tokenizer = AutoTokenizer.from_pretrained(name, revision=revision)
    # The fused kernel for reading; the analyser switches to eager only for the few tokens
    # whose attention it keeps. Full precision, because a CPU without bfloat16 kernels runs
    # half precision slower, not faster.
    model = AutoModelForCausalLM.from_pretrained(
        name, revision=revision, dtype=torch.float32, attn_implementation=FUSED
    )
    # transformers types PreTrainedModel.to through a decorator whose signature expects the
    # model where the device goes, so moving it to a named device reads as a type error;
    # the call is the library's documented one.
    model = model.to(device)  # type: ignore[arg-type]
    return Analyzer(
        model, tokenizer, name=name, revision=revision, max_prompt_tokens=max_prompt_tokens
    )
