"""
数据挖掘智能体提示词模板模块。

提供各种提示词模板，用于数据挖掘智能体的各项功能。
"""

from .database_query_prompts import (
    DATABASE_QUERY_STRATEGY_PROMPT,
)
from .law_search_prompts import (
    LAW_SEARCH_PROMPT,
)
from .data_summary_prompts import (
    DATA_SUMMARY_PROMPT,
)

__all__ = [
    "DATABASE_QUERY_STRATEGY_PROMPT",
    "LAW_SEARCH_PROMPT",
    "DATA_SUMMARY_PROMPT",
]

