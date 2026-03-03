"""
数据挖掘智能体核心模块。

实现类案深度报告生成功能，包括法律条文搜索和数据概括。
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
import json
from loguru import logger

# LLM 模块
from .llm import get_chat_model, get_reasoning_model

# 提示词模板
from .prompts import (
    LAW_SEARCH_PROMPT,
    DATA_SUMMARY_PROMPT,
)


class DataMiningAgent:
    """
    数据挖掘智能体核心类。
    
    负责法律条文搜索、数据概括等功能。
    """
    
    def __init__(
        self,
        chat_model_name: str = "deepseek-chat",
        reasoning_model_name: str = "deepseek-reasoner",
        temperature: float = 0.2,
    ):
        """
        初始化数据挖掘智能体。
        
        :param chat_model_name: 聊天模型名称，默认且推荐使用 deepseek-chat
        :param reasoning_model_name: 推理模型名称，默认且推荐使用 deepseek-reasoner
        :param temperature: LLM 温度参数，默认 0.2（推荐）
        """
        self.name = "DataMiningAgent"
        logger.info("初始化数据挖掘智能体")
        
        self.chat_model = get_chat_model(
            model_name=chat_model_name,
            temperature=temperature
        )
        self.reasoning_model = get_reasoning_model(
            model_name=reasoning_model_name,
            temperature=temperature
        )
        
        logger.info("数据挖掘智能体初始化完成")
    
    def search_laws_by_prompt(
        self,
        query: str,
        use_reasoning_model: bool = False
    ) -> Dict[str, Any]:
        """
        根据提示词搜寻法律条文。
        
        使用 LangChain 框架调用 LLM，根据用户提供的查询提示词搜索相关的法律条文。
        暂时不使用数据库，直接基于 LLM 的知识库进行搜索。
        
        :param query: 查询提示词，描述需要搜索的法律条文内容
        :param use_reasoning_model: 是否使用推理模型（默认 False，使用聊天模型）
        :return: 包含搜索结果的字典，格式为：
            {
                "laws": [
                    {
                        "law_name": "法律名称",
                        "article_number": "条号",
                        "article_content": "条文内容",
                        "relevance": "相关性说明"
                    }
                ],
                "total_count": 条文总数,
                "search_summary": "搜索总结"
            }
        :raises ValueError: 如果查询为空或解析失败
        """
        if not query or not query.strip():
            raise ValueError("查询提示词不能为空")
        
        logger.info(f"开始搜索法律条文，查询: {query[:50]}...")
        
        # 选择使用的模型
        model = self.reasoning_model if use_reasoning_model else self.chat_model
        
        # 构建提示词消息
        messages = LAW_SEARCH_PROMPT.to_messages(
            user_input=query,
            query=query
        )
        
        # 调用 LLM 进行搜索
        logger.debug("调用 LLM 进行法律条文搜索")
        try:
            response = model.invoke(messages)
            response_text = response.content
            logger.debug(f"LLM 响应长度: {len(response_text)} 字符")
        except Exception as e:
            logger.error(f"调用 LLM 失败: {e}")
            raise RuntimeError(f"法律条文搜索失败: {e}") from e
        
        # 提取并解析 JSON 结果
        try:
            json_text = self._extract_json_from_response(response_text)
            result = json.loads(json_text)
            
            # 验证结果格式
            if not isinstance(result, dict):
                raise ValueError("返回结果不是字典格式")
            if "laws" not in result:
                raise ValueError("返回结果缺少 'laws' 字段")
            
            logger.info(f"✅ 法律条文搜索完成，找到 {result.get('total_count', len(result.get('laws', [])))} 条相关条文")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            logger.error(f"响应文本: {response_text[:500]}...")
            raise ValueError(f"无法解析搜索结果: {e}") from e
        except Exception as e:
            logger.error(f"处理搜索结果时出错: {e}")
            raise
    
    def summarize_found_data(
        self,
        law_data: Dict[str, Any],
        use_reasoning_model: bool = True
    ) -> Dict[str, Any]:
        """
        返回找到的数据概括性信息。
        
        对搜索到的法律条文数据进行概括性总结，提取关键信息和洞察。
        
        :param law_data: 法律条文数据，格式应为 search_laws_by_prompt 返回的格式
        :param use_reasoning_model: 是否使用推理模型（默认 True，用于更好的概括分析）
        :return: 包含概括性信息的字典，格式为：
            {
                "summary": {
                    "total_laws": 法律总数,
                    "total_articles": 条文总数,
                    "law_fields": ["法律领域列表"],
                    "main_topics": ["主要主题列表"]
                },
                "key_articles": [
                    {
                        "law_name": "法律名称",
                        "article_number": "条号",
                        "brief_content": "简要内容",
                        "importance": "重要性说明"
                    }
                ],
                "insights": "概括性洞察"
            }
        :raises ValueError: 如果数据格式不正确
        """
        if not law_data:
            raise ValueError("法律条文数据不能为空")
        
        if not isinstance(law_data, dict):
            raise ValueError("法律条文数据必须是字典格式")
        
        logger.info("开始生成数据概括性信息")
        
        # 将数据转换为 JSON 字符串，便于传递给 LLM
        law_data_str = json.dumps(law_data, ensure_ascii=False, indent=2)
        
        # 选择使用的模型（默认使用推理模型以获得更好的分析）
        model = self.reasoning_model if use_reasoning_model else self.chat_model
        
        # 构建提示词消息
        messages = DATA_SUMMARY_PROMPT.to_messages(
            user_input="",
            law_data=law_data_str
        )
        
        # 调用 LLM 进行概括
        logger.debug("调用 LLM 进行数据概括")
        try:
            response = model.invoke(messages)
            response_text = response.content
            logger.debug(f"LLM 响应长度: {len(response_text)} 字符")
        except Exception as e:
            logger.error(f"调用 LLM 失败: {e}")
            raise RuntimeError(f"数据概括失败: {e}") from e
        
        # 提取并解析 JSON 结果
        try:
            json_text = self._extract_json_from_response(response_text)
            summary = json.loads(json_text)
            
            # 验证结果格式
            if not isinstance(summary, dict):
                raise ValueError("返回结果不是字典格式")
            if "summary" not in summary:
                raise ValueError("返回结果缺少 'summary' 字段")
            
            logger.info("✅ 数据概括完成")
            return summary
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            logger.error(f"响应文本: {response_text[:500]}...")
            raise ValueError(f"无法解析概括结果: {e}") from e
        except Exception as e:
            logger.error(f"处理概括结果时出错: {e}")
            raise
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """
        从 LLM 响应中提取 JSON 字符串。
        
        处理可能的 markdown 代码块标记（如 ```json ... ```）。
        
        :param response_text: LLM 的原始响应文本
        :return: 清理后的 JSON 字符串
        """
        # 检查是否包含 ```json 代码块标记
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                json_text = response_text[start:end].strip()
                logger.debug(f"从 ```json 代码块中提取 JSON: {json_text[:100]}...")
                return json_text
        
        # 检查是否包含普通的 ``` 代码块标记
        if "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end != -1:
                json_text = response_text[start:end].strip()
                # 如果第一行是 "json"，跳过它
                if json_text.startswith("json"):
                    json_text = json_text[4:].strip()
                logger.debug(f"从 ``` 代码块中提取 JSON: {json_text[:100]}...")
                return json_text
        
        # 如果没有代码块，尝试查找 JSON 对象（以 { 开头，以 } 结尾）
        start_brace = response_text.find("{")
        if start_brace != -1:
            # 从第一个 { 开始，找到匹配的最后一个 }
            brace_count = 0
            for i in range(start_brace, len(response_text)):
                if response_text[i] == "{":
                    brace_count += 1
                elif response_text[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        json_text = response_text[start_brace:i+1].strip()
                        logger.debug(f"从文本中提取 JSON 对象: {json_text[:100]}...")
                        return json_text
        
        # 如果都没有找到，直接返回原文本（可能是纯 JSON）
        logger.debug("未找到代码块标记，返回原文本")
        return response_text.strip()
    
    def process_message(self, message: str, context: Dict[str, Any]) -> str:
        """
        处理来自论坛的消息。
        
        用于在论坛中与其他智能体交互。
        
        :param message: 收到的消息内容
        :param context: 消息上下文信息
        :return: 响应消息
        """
        logger.info(f"数据挖掘智能体收到消息: {message[:50]}...")
        
        # 尝试解析消息，判断是否是法律搜索请求
        try:
            # 如果消息看起来像是法律搜索请求，执行搜索
            if any(keyword in message for keyword in ["法律", "条文", "法条", "搜索", "查找"]):
                result = self.search_laws_by_prompt(message)
                summary = self.summarize_found_data(result)
                
                # 格式化响应
                response = f"已找到 {result.get('total_count', 0)} 条相关法律条文。\n"
                response += f"概括信息：{summary.get('insights', '无')}\n"
                response += f"主要涉及：{', '.join(summary.get('summary', {}).get('law_fields', []))}"
                
                return response
            else:
                return f"数据挖掘智能体已收到消息: {message}。请提供法律条文搜索请求。"
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
            return f"处理消息时出错: {str(e)}"

