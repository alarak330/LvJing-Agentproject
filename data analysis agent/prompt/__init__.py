"""
提示词模板模块。

提供结构化的提示词管理功能，支持模板变量替换、Few-shot 示例、系统角色定义。
"""

from .base import (
    PromptTemplate,
    create_prompt_template,
)

# 分析相关提示词
from .analysis_prompts import (
    REQUIREMENT_PARSE_PROMPT,
    NL_REQUIREMENT_PARSE_PROMPT,
)

# 过滤相关提示词
from .filter_prompts import (
    FILTER_CRITERIA_EXTRACT_PROMPT,
    CRITERIA_MATCH_PROMPT,
    DATA_VALIDATION_PROMPT,
)

# 辩论相关提示词

__all__ = [
    # 基础类
    "PromptTemplate",
    "create_prompt_template",
    # 分析提示词
    "REQUIREMENT_PARSE_PROMPT",
    "NL_REQUIREMENT_PARSE_PROMPT",
    # 过滤提示词
    "FILTER_CRITERIA_EXTRACT_PROMPT",
    "CRITERIA_MATCH_PROMPT",
    "DATA_VALIDATION_PROMPT",

]


# 便捷函数：根据名称获取提示词模板
_PROMPT_REGISTRY = {
    "requirement_parse": REQUIREMENT_PARSE_PROMPT,
    "filter_criteria_extract": FILTER_CRITERIA_EXTRACT_PROMPT,
    "criteria_match": CRITERIA_MATCH_PROMPT,
    "data_validation": DATA_VALIDATION_PROMPT,
}


def get_prompt(name: str) -> PromptTemplate:
    """
    根据名称获取提示词模板。
    
    :param name: 提示词模板名称
    :return: PromptTemplate 实例
    :raises ValueError: 如果名称不存在
    """
    if name not in _PROMPT_REGISTRY:
        available = ", ".join(_PROMPT_REGISTRY.keys())
        raise ValueError(
            f"提示词模板 '{name}' 不存在。可用的模板: {available}"
        )
    return _PROMPT_REGISTRY[name]


def list_prompts() -> list[str]:
    """
    列出所有可用的提示词模板名称。
    
    :return: 提示词模板名称列表
    """
    return list(_PROMPT_REGISTRY.keys())

