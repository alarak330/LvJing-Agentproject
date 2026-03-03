"""
报告智能体核心模块。

实现法律类案深度报告生成功能，接收论坛辩论结果并生成专业报告。
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime
from loguru import logger
from json import JSONDecodeError

from langchain_core.messages import SystemMessage, HumanMessage

# 加载环境变量（确保 KIMI API 配置可用）
import dotenv
dotenv.load_dotenv()

# LLM 模块（KIMI 大模型）
from .llm import get_chat_model, get_reasoning_model

# 提示词模板
from .prompt import (
    REPORT_GENERATION_PROMPT,
    REPORT_FORMAT_PROMPT,
)


class ReportAgent:
    """
    报告智能体核心类。
    
    负责接收论坛辩论结果，生成专业的法律类案深度报告。
    """
    
    def __init__(
        self,
        chat_model_name: str = "moonshot-v1-8k",
        reasoning_model_name: str = "moonshot-v1-32k",
        temperature: float = 0.2,
    ):
        """
        初始化报告智能体。
        
        :param chat_model_name: KIMI 聊天模型名称，默认 "moonshot-v1-8k"
        :param reasoning_model_name: KIMI 推理模型名称，默认 "moonshot-v1-32k"
        :param temperature: LLM 温度参数，默认 0.2
        """
        self.name = "ReportAgent"
        logger.info("初始化报告智能体")
        
        self.chat_model = get_chat_model(
            model_name=chat_model_name,
            temperature=temperature
        )
        self.reasoning_model = get_reasoning_model(
            model_name=reasoning_model_name,
            temperature=temperature
        )
        
        logger.info("报告智能体初始化完成")
    
    def generate_report(
        self,
        forum_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        根据论坛辩论结果生成法律类案深度报告。
        
        :param forum_result: 论坛辩论结果，包含以下字段：
            - user_requirement: 用户原始需求
            - debate_history: 辩论历史
            - total_rounds: 辩论轮次
            - final_data: 最终数据（包含 law_data 和 summary）
            - analysis_result: 分析结果
        :return: 生成的报告字典，包含结构化的报告内容和格式化文本
        """
        logger.info("开始生成法律类案深度报告")
        
        # 提取论坛结果中的数据
        user_requirement = forum_result.get("user_requirement", "")
        debate_history = forum_result.get("debate_history", [])
        total_rounds = forum_result.get("total_rounds", 0)
        final_data = forum_result.get("final_data", {})
        analysis_result = forum_result.get("analysis_result", {})
        
        # 提取法律条文数据
        law_data = final_data.get("law_data", {})
        data_summary = final_data.get("summary", {})
        
        # 构建辩论摘要
        debate_summary = self._build_debate_summary(debate_history, total_rounds)
        
        # 格式化数据为字符串
        law_data_str = json.dumps(law_data, ensure_ascii=False, indent=2)
        analysis_result_str = json.dumps(analysis_result, ensure_ascii=False, indent=2)
        debate_summary_str = json.dumps(debate_summary, ensure_ascii=False, indent=2)
        
        # 使用推理模型生成报告
        messages = REPORT_GENERATION_PROMPT.to_messages(
            user_input="",
            user_requirement=user_requirement,
            debate_summary=debate_summary_str,
            law_data=law_data_str,
            analysis_result=analysis_result_str
        )
        
        try:
            logger.debug("调用 KIMI 推理模型生成报告")
            response = self.reasoning_model.invoke(messages)
            response_text = response.content
            
            # 提取 JSON
            json_text = self._extract_json_from_response(response_text)
            try:
                report_data = json.loads(json_text)
            except JSONDecodeError as e:
                logger.warning(f"首次解析报告 JSON 失败，尝试自动修复后重试: {e}")
                fixed_json_text = self._repair_to_strict_json(response_text)
                report_data = json.loads(fixed_json_text)
            
            # 添加元数据
            if "metadata" not in report_data:
                report_data["metadata"] = {}
            report_data["metadata"]["generation_time"] = datetime.now().isoformat()
            report_data["metadata"]["total_laws"] = len(law_data.get("laws", []))
            report_data["metadata"]["debate_rounds"] = total_rounds
            
            # 生成格式化文本
            formatted_text = self._format_report_text(report_data)
            
            logger.info("✅ 报告生成完成")
            
            return {
                "structured_report": report_data,
                "formatted_text": formatted_text,
                "metadata": report_data.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 返回基础报告
            return self._generate_fallback_report(
                user_requirement,
                law_data,
                analysis_result,
                total_rounds
            )

    def _repair_to_strict_json(self, raw_response_text: str) -> str:
        """
        将可能包含不严格 JSON（比如未闭合字符串、夹杂说明文本、代码块等）的模型输出，
        修复为可被 json.loads() 解析的严格 JSON 字符串。
        """
        # 先做一次本地提取（尽量拿到 {...}）
        extracted = self._extract_json_from_response(raw_response_text)
        try:
            json.loads(extracted)
            return extracted
        except Exception:
            pass

        # 再让模型做一次“严格 JSON 修复”
        system = SystemMessage(
            content=(
                "你是一个严格的 JSON 修复器。"
                "你必须把用户提供的内容转换为【严格 JSON】。"
                "要求：只输出一个 JSON 对象，不要输出任何解释、不要使用 Markdown 代码块。"
                "确保所有字符串正确转义，所有引号成对出现。"
            )
        )
        human = HumanMessage(
            content=(
                "请将下面内容修复为严格 JSON（只输出 JSON）：\n\n"
                f"{raw_response_text}"
            )
        )
        response = self.chat_model.invoke([system, human])
        fixed_text = getattr(response, "content", "") or ""
        fixed_json = self._extract_json_from_response(fixed_text)
        return fixed_json
    
    def _build_debate_summary(
        self,
        debate_history: List[Dict[str, Any]],
        total_rounds: int
    ) -> Dict[str, Any]:
        """
        构建辩论摘要。
        
        :param debate_history: 辩论历史
        :param total_rounds: 总轮次
        :return: 辩论摘要
        """
        summary = {
            "total_rounds": total_rounds,
            "key_actions": [],
            "data_flow": []
        }
        
        for entry in debate_history:
            action = entry.get("action", "")
            agent = entry.get("agent", "")
            summary["key_actions"].append(f"{agent}: {action}")
            
            if action == "search_data":
                summary["data_flow"].append("数据挖掘智能体搜索法律条文")
            elif action == "evaluate_data":
                summary["data_flow"].append("数据分析智能体评估数据")
        
        return summary
    
    def _format_report_text(self, report_data: Dict[str, Any]) -> str:
        """
        将结构化的报告数据格式化为易读的文本。
        
        :param report_data: 结构化的报告数据
        :return: 格式化后的文本（Markdown 格式）
        """
        try:
            report = report_data.get("report", {})
            
            # 构建 Markdown 格式的报告
            lines = []
            
            # 标题
            title = report.get("title", "法律分析报告")
            lines.append(f"# {title}\n\n")
            
            # 分析报告（这是主体内容）
            analysis_report = report.get("analysis_report", "")
            if analysis_report:
                lines.append(f"{analysis_report}\n\n")
            
            # 支撑法律条文（作为附录，支撑分析报告中的观点）
            supporting_laws = report.get("supporting_laws", [])
            if supporting_laws:
                lines.append("---\n\n")
                lines.append("## 支撑法律条文\n\n")
                lines.append("以下法律条文作为上述分析报告的支撑依据：\n\n")
                for i, law in enumerate(supporting_laws, 1):
                    law_name = law.get('law_name', '')
                    article_number = law.get('article_number', '')
                    article_content = law.get('article_content', '')
                    how_it_supports = law.get('how_it_supports', '')
                    
                    if law_name and article_number:
                        lines.append(f"### {i}. {law_name} 第{article_number}条\n\n")
                    
                    if article_content:
                        lines.append(f"**条文内容**：{article_content}\n\n")
                    
                    if how_it_supports:
                        lines.append(f"**如何支撑分析**：{how_it_supports}\n\n")
                    
                    lines.append("---\n\n")
            
            return "".join(lines)
            
        except Exception as e:
            logger.error(f"格式化报告文本失败: {e}")
            return f"报告格式化失败: {str(e)}"
    
    def _generate_fallback_report(
        self,
        user_requirement: str,
        law_data: Dict[str, Any],
        analysis_result: Dict[str, Any],
        total_rounds: int
    ) -> Dict[str, Any]:
        """
        生成备用报告（当 LLM 生成失败时使用）。
        
        :param user_requirement: 用户需求
        :param law_data: 法律条文数据
        :param analysis_result: 分析结果
        :param total_rounds: 辩论轮次
        :return: 备用报告
        """
        laws = law_data.get("laws", [])
        
        report_data = {
            "report": {
                "title": "法律类案报告",
                "requirement_summary": {
                    "user_requirement": user_requirement,
                    "case_type": "未知",
                    "dispute_focus": "待分析",
                    "key_facts": []
                },
                "relevant_laws": [
                    {
                        "law_name": law.get("law_name", "未知"),
                        "article_number": law.get("article_number", "未知"),
                        "article_content": law.get("article_content", "未知"),
                        "relevance_analysis": law.get("relevance", "待分析"),
                        "application": "待分析"
                    }
                    for law in laws
                ],
                "data_analysis": {
                    "laws_count": len(laws),
                    "data_quality": analysis_result.get("data_quality", "未知"),
                    "analysis_summary": analysis_result.get("evaluation", "待分析")
                },
                "comprehensive_analysis": "基于找到的法律条文进行综合分析",
                "recommendations": "请参考相关法律条文",
                "conclusion": f"找到 {len(laws)} 条相关法律条文"
            },
            "metadata": {
                "generation_time": datetime.now().isoformat(),
                "total_laws": len(laws),
                "debate_rounds": total_rounds
            }
        }
        
        formatted_text = self._format_report_text(report_data)
        
        return {
            "structured_report": report_data,
            "formatted_text": formatted_text,
            "metadata": report_data["metadata"]
        }
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """
        从 LLM 响应中提取 JSON 字符串。
        
        :param response_text: LLM 的原始响应文本
        :return: 清理后的 JSON 字符串
        """
        # 检查是否包含 ```json 代码块标记
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                return response_text[start:end].strip()
        
        # 检查是否包含普通的 ``` 代码块标记
        if "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end != -1:
                json_text = response_text[start:end].strip()
                if json_text.startswith("json"):
                    json_text = json_text[4:].strip()
                return json_text
        
        # 如果没有代码块，尝试查找 JSON 对象
        start_brace = response_text.find("{")
        if start_brace != -1:
            brace_count = 0
            for i in range(start_brace, len(response_text)):
                if response_text[i] == "{":
                    brace_count += 1
                elif response_text[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        return response_text[start_brace:i+1].strip()
        
        return response_text.strip()
