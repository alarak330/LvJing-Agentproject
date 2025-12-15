"""
DeepSeek 聊天模型的初始化工具。

所有帮助函数都会通过 ``python-dotenv`` 读取 ``.env`` 中的配置，并写入
``langchain-openai`` 期望的环境变量，从而让外部代码直接调用
``get_chat_model()`` / ``get_reasoning_model()``，无需重复配置密钥或地址。
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict

import dotenv
from langchain_openai import ChatOpenAI

import os


DEFAULT_CHAT_MODEL = "deepseek-chat"
DEFAULT_REASONING_MODEL = "deepseek-reason"
API_KEY_ENV = "DEEPSEEK_API_KEY"
BASE_URL_ENV = "DEEPSEEK_BASE_URL"


def _prepare_environment(
    api_key_env: str = API_KEY_ENV,
    base_url_env: str = BASE_URL_ENV,
) -> Dict[str, str]:
    """
    从 ".env" 加载密钥与 Base URL,设置到 "langchain-openai" 所需的环境变量。
    
    :param api_key_env: API 密钥的环境变量名，默认为 "DEEPSEEK_API_KEY"
    :param base_url_env: Base URL 的环境变量名，默认为 "DEEPSEEK_BASE_URL"
    :return: 包含 api_key 和 base_url 的字典
    :raises RuntimeError: 如果缺少必要的环境变量
    """
    dotenv.load_dotenv()

    api_key = os.getenv(api_key_env)
    if not api_key:
        raise RuntimeError(f"Missing API key env: {api_key_env}")

    base_url = os.getenv(base_url_env)
    if not base_url:
        raise RuntimeError(f"Missing base url env: {base_url_env}")

    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_BASE_URL"] = base_url
    return {"api_key": api_key, "base_url": base_url}


def _build_chat_model(
    model_name: str,
    temperature: float = 0.2,
    **kwargs: Any,
) -> ChatOpenAI:
    """
    在确保环境就绪后构建一个 ``ChatOpenAI`` 实例。
    
    :param model_name: 模型名称
    :param temperature: 温度参数，控制输出的随机性
    :param kwargs: 其他传递给 ChatOpenAI 的参数
    :return: ChatOpenAI 实例
    """
    _prepare_environment()
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        **kwargs,
    )


@lru_cache(maxsize=2)
def get_chat_model(
    *,
    temperature: float = 0.2,
    model_name: str = DEFAULT_CHAT_MODEL,
    **kwargs: Any,
) -> ChatOpenAI:
    """
    返回通用问答/分析场景使用的 DeepSeek 聊天模型，内部做了缓存，避免频繁重建。
    可通过参数覆盖模型名称、temperature 等解码配置。
    
    :param temperature: 温度参数，默认 0.2（推荐用于类案分析）
    :param model_name: 模型名称，默认为 "deepseek-chat"
    :param kwargs: 其他传递给 ChatOpenAI 的参数
    :return: ChatOpenAI 实例
    
    Example:
        >>> model = get_chat_model()
        >>> response = model.invoke([{"role": "user", "content": "你好"}])
    """
    return _build_chat_model(model_name, temperature=temperature, **kwargs)


@lru_cache(maxsize=2)
def get_reasoning_model(
    *,
    temperature: float = 0.1,
    model_name: str = DEFAULT_REASONING_MODEL,
    **kwargs: Any,
) -> ChatOpenAI:
    """
    返回适用于复杂推理/深度分析任务的 DeepSeek 推理模型，同样带缓存。
    
    用于类案深度分析、相似度计算、报告生成等需要复杂推理的任务。
    
    :param temperature: 温度参数，默认 0.1（较低温度用于更稳定的推理）
    :param model_name: 模型名称，默认为 "deepseek-reason"
    :param kwargs: 其他传递给 ChatOpenAI 的参数
    :return: ChatOpenAI 实例
    
    Example:
        >>> model = get_reasoning_model()
        >>> response = model.invoke([{"role": "user", "content": "分析这两个案件的相似度"}])
    """
    return _build_chat_model(model_name, temperature=temperature, **kwargs)


def get_model(
    model_name: str,
    *,
    temperature: float = 0.2,
    **kwargs: Any,
) -> ChatOpenAI:
    """
    当调用方想显式指定任意模型名称时使用的通用工厂方法。
    
    :param model_name: 模型名称
    :param temperature: 温度参数，默认 0.2
    :param kwargs: 其他传递给 ChatOpenAI 的参数
    :return: ChatOpenAI 实例
    
    Example:
        >>> model = get_model("deepseek-chat", temperature=0.3)
    """
    return _build_chat_model(model_name, temperature=temperature, **kwargs)

