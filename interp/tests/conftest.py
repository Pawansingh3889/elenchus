"""A real Qwen tokenizer and a tiny random Qwen3, so the suite never downloads weights.

The tokenizer is the real one, pinned, because the chat template and the <tool_call> token
are what the prompt parsing depends on; it is about 15 MB and cached. The model has the
real architecture at a size that runs in milliseconds, so every reading is exercised
without a gigabyte of weights.
"""

import pytest
import torch
from transformers import AutoTokenizer, Qwen3Config, Qwen3ForCausalLM

from elenchus_interp.__main__ import MODEL, REVISION
from elenchus_interp.analysis import Analyzer

LAYERS = 2


@pytest.fixture(scope="session")
def tokenizer():
    return AutoTokenizer.from_pretrained(MODEL, revision=REVISION)


@pytest.fixture(scope="session")
def analyzer(tokenizer):
    torch.manual_seed(13)
    config = Qwen3Config(
        vocab_size=len(tokenizer),
        hidden_size=32,
        intermediate_size=64,
        num_hidden_layers=LAYERS,
        num_attention_heads=4,
        num_key_value_heads=2,
        head_dim=8,
        max_position_embeddings=8192,
        tie_word_embeddings=True,
    )
    config._attn_implementation = "sdpa"
    model = Qwen3ForCausalLM(config)
    return Analyzer(model, tokenizer, name="tiny-qwen3", revision="test", max_prompt_tokens=4096)


def tool(name: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": f"Use {name}.",
            "parameters": {"type": "object", "properties": {}},
        },
    }


@pytest.fixture
def captured() -> dict:
    """A conduct request in the shape the backend captures it."""
    return {
        "messages": [
            {
                "role": "system",
                "content": "You conduct a short workplace survey. ENGINE STATE: question 1.",
            },
            {"role": "assistant", "content": "Which department do you work in?"},
            {"role": "user", "content": "these days I work on the filleting line"},
        ],
        "tools": [tool("record_answer"), tool("ask_follow_up"), tool("flag_unanswerable")],
        "tool_choice": "required",
    }
