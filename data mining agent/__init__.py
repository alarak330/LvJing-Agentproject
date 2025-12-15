"""
数据挖掘智能体主模块。

提供类案深度报告生成功能。
"""

from .llm import (
    get_chat_model,
    get_reasoning_model,
    get_model,
    DEFAULT_CHAT_MODEL,
    DEFAULT_REASONING_MODEL,
)

__all__ = [
    "get_chat_model",
    "get_reasoning_model",
    "get_model",
    "DEFAULT_CHAT_MODEL",
    "DEFAULT_REASONING_MODEL",
]