"""The three readings, on a tiny random Qwen3: shapes, sums and refusals, not meanings."""

import math

import pytest
import torch

from elenchus_interp.analysis import PromptTooLongError, _common_prefix
from elenchus_interp.prompt import render
from elenchus_interp.schemas import AnalyseRequest, AttributeRequest
from tests.conftest import LAYERS


def test_a_reading_comes_back_whole(analyzer, captured):
    analysis = analyzer.analyse(AnalyseRequest(**captured))

    names = ["record_answer", "ask_follow_up", "flag_unanswerable"]
    assert [t.name for t in analysis.tools] == names
    assert math.isclose(sum(t.probability for t in analysis.tools), 1.0, rel_tol=1e-6)
    assert analysis.pick in names
    assert 0.0 <= analysis.calls_a_tool <= 1.0

    assert [layer.layer for layer in analysis.layers] == list(range(1, LAYERS + 1))
    for layer in analysis.layers:
        assert set(layer.tool_probabilities) == set(names)
        assert math.isclose(sum(layer.tool_probabilities.values()), 1.0, rel_tol=1e-6)
    for layer in analysis.attention:
        assert math.isclose(sum(layer.shares.values()), 1.0, rel_tol=1e-4)
    assert len(analysis.attention) == LAYERS
    assert all(t.section != "template" for t in analysis.attended_tokens)
    assert analysis.prompt_tokens == sum(s.tokens for s in analysis.sections)
    assert analysis.timings.total_ms >= analysis.timings.read_ms


def test_an_attribution_comes_back_whole(analyzer, captured):
    result = analyzer.attribute(AttributeRequest(**captured, target_tool="record_answer"))
    attribution = result.attribution
    assert attribution.target == "record_answer"
    shares = attribution.sections.values()
    assert math.isclose(sum(s.positive - s.negative for s in shares), 1.0, rel_tol=1e-4)
    assert "filleting" in " ".join(w.text for w in attribution.respondent_words)
    assert result.total_ms >= result.attribution_ms


def test_cached_tool_scores_match_a_fresh_read_of_each_name(analyzer, captured):
    """Each name is scored from one shared cache that is cropped back after it; a crop that
    leaked would shift every tool scored later. Checked against a full uncached read."""
    request = AnalyseRequest(**captured)
    analysis = analyzer.analyse(request)
    assert analyzer.analyse(request).tools == analysis.tools

    rendered = render(analyzer.tokenizer, request.messages, request.tools)
    names = [t.name for t in analysis.tools]
    continuations = {name: analyzer._continuation(name) for name in names}
    common = len(_common_prefix(list(continuations.values())))
    for scored in analysis.tools:
        ids = rendered.ids + continuations[scored.name]
        with torch.no_grad():
            logits = analyzer.model(input_ids=torch.tensor([ids])).logits[0].float()
        logprobs = torch.log_softmax(logits, dim=-1)
        first = len(rendered.ids) + common
        fresh = sum(float(logprobs[i - 1, ids[i]]) for i in range(first, len(ids)))
        assert math.isclose(scored.logprob, fresh, rel_tol=1e-4, abs_tol=1e-3), scored.name


def test_attribution_gives_the_same_answer_every_time_it_runs(analyzer, captured):
    """Seen in the server test: checkpointing left a hook on the embedding layer, and the
    second attribution in a process read an empty gradient."""
    request = AttributeRequest(**captured, target_tool="ask_follow_up")
    first = analyzer.attribute(request).attribution
    second = analyzer.attribute(request).attribution
    assert [w.text for w in first.respondent_words] == [w.text for w in second.respondent_words]
    for a, b in zip(first.respondent_words, second.respondent_words, strict=True):
        assert math.isclose(a.score, b.score, rel_tol=1e-4, abs_tol=1e-6)


def test_the_fused_kernel_is_back_after_the_eager_step(analyzer, captured):
    """Attention is read eagerly for a handful of tokens only; a model left eager would read
    every later prompt at the slow, memory-hungry speed this design exists to avoid."""
    analysis = analyzer.analyse(AnalyseRequest(**captured))
    assert analyzer.model.config._attn_implementation == "sdpa"
    assert len(analysis.attention) == len(analysis.layers)


def test_a_target_that_was_not_offered_is_refused(analyzer, captured):
    with pytest.raises(ValueError, match="was not offered"):
        analyzer.attribute(AttributeRequest(**captured, target_tool="delete_everything"))


def test_a_prompt_longer_than_the_limit_is_refused(analyzer, captured):
    captured["messages"][2]["content"] = "word " * 5000
    with pytest.raises(PromptTooLongError, match="at most 4096"):
        analyzer.analyse(AnalyseRequest(**captured))
