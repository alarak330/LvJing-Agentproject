"""
论坛 LLM 模块。

提供千问大模型的初始化工具，用于论坛主持人功能。
"""

from .qwenmodels import (
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

