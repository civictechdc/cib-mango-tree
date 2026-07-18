"""
Basic tokenizer implementation.

This module exports the BasicTokenizer implementation that provides
fundamental Unicode-aware tokenization capabilities for social media text.
"""

from ..core.types import TokenizerConfig
from .patterns import get_patterns
from .tokenizer import BasicTokenizer


# Convenience factory functions
def create_basic_tokenizer(config: TokenizerConfig | None = None) -> BasicTokenizer:
    """Create a BasicTokenizer with optional configuration."""
    if config is None:
        config = TokenizerConfig()
    return BasicTokenizer(config)


# Single-entry memo for the last (config object -> tokenizer) pair. Callers that
# tokenize a corpus pass the same config instance for every message, so this turns
# one tokenizer construction per message into one per corpus. Keyed on object
# identity: a config mutated in place after first use will not invalidate it.
_last_config: TokenizerConfig | None = None
_last_tokenizer: BasicTokenizer | None = None


def tokenize_text(text: str, config: TokenizerConfig | None = None) -> list[str]:
    """Simple convenience function for basic text tokenization."""
    global _last_config, _last_tokenizer

    if _last_tokenizer is not None and config is _last_config:
        return _last_tokenizer.tokenize(text)

    tokenizer = create_basic_tokenizer(config)
    _last_config, _last_tokenizer = config, tokenizer
    return tokenizer.tokenize(text)


__all__ = [
    "BasicTokenizer",
    "TokenizerConfig",
    "get_patterns",
    "create_basic_tokenizer",
    "tokenize_text",
]
