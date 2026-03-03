"""
论坛模块。

提供智能体论坛功能，协调数据分析智能体和数据挖掘智能体进行法律类案报告生成。
"""

from .agent import ForumAgent
from .llm import (
    get_chat_model,
    get_reasoning_model,
    get_model,
    DEFAULT_CHAT_MODEL,
    DEFAULT_REASONING_MODEL,
)

__all__ = [
    "ForumAgent",
    "get_chat_model",
    "get_reasoning_model",
    "get_model",
    "DEFAULT_CHAT_MODEL",
    "DEFAULT_REASONING_MODEL",
]

