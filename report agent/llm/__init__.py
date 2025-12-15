"""
报告智能体 LLM 模块。

提供 KIMI 模型的初始化工具，便于调用智能体。
"""

from .kimimodels import (
    get_chat_model,
    get_reasoning_model,
    get_model,
    DEFAULT_CHAT_MODEL,
    DEFAULT_REASONING_MODEL,
    API_KEY_ENV,
    BASE_URL_ENV,
)

__all__ = [
    "get_chat_model",
    "get_reasoning_model",
    "get_model",
    "DEFAULT_CHAT_MODEL",
    "DEFAULT_REASONING_MODEL",
    "API_KEY_ENV",
    "BASE_URL_ENV",
]

