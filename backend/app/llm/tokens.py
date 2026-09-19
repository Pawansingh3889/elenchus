"""One approximate token count, shared by everything that needs to size a prompt.

No tokenizer is vendored here for the same reason no provider SDK is: four tiers can
mean four different tokenizers (tiktoken for OpenAI is already the wrong answer for
Groq's Llama or a self-hosted model), and getting one exactly right would not make the
other three correct. ~4 characters per token is the usual rule of thumb for English and
is treated everywhere as a bound to catch the case that actually happens — a long_text
answer, or several of them, pushing a small tier past its window — never as a precise
accounting. Both callers (the context-window guard in ``openai_compatible`` and the
transcript window in ``conduct.engine``) import this rather than each keeping their own
copy of the same magic number, so the two estimates cannot drift apart.
"""

CHARS_PER_TOKEN_ESTIMATE = 4


def estimate_tokens(text: str) -> int:
    """A rough, deliberately conservative token count for ``text``."""
    return len(text) // CHARS_PER_TOKEN_ESTIMATE
