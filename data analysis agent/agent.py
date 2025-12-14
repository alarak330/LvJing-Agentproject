"""
数据分析智能体核心模块。

实现数据分析智能体的主要功能，包括需求解析、任务生成、数据过滤、统计分析等。
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
import json
import os
import subprocess
from pathlib import Path

from loguru import logger

# LLM 模块
from llm import get_chat_model, get_reasoning_model

# 提示词模板
from prompt import (
    REQUIREMENT_PARSE_PROMPT,
    NL_REQUIREMENT_PARSE_PROMPT,
)


# 数据格式化工具
from utils.formatter import (
    format_case_summary,
    format_statistics,
    format_table_data,
    format_chart_data,
)

# 异常类
from utils.expand_exceptions import (
    LegalDataError,
    DataValidationError,
    StatisticsError,
)

# 数据库模块
from database import (
    DatabaseConnection,
    DatabaseConfig,
    SchemaInspector,
    get_db_context,
)

from utils.legal_parser import (
    parse_case_number,
    parse_court_name,
    parse_law_reference,
    parse_date,
)

from utils.constants import (
    CASE_TYPES,
    COURT_LEVELS,
    PROCEDURE_TYPES,
)

class DataAnalysisAgent:
    """
    数据分析智能体核心类。
    
    负责解析用户需求、生成分析任务、过滤数据、执行统计分析等核心功能。
    """
    
    def __init__(
        self,
        chat_model_name: str = "deepseek-chat",
        reasoning_model_name: str = "deepseek-reasoner",
        temperature: float = 0.2,
    ):
        """
        初始化数据分析智能体。
        
        :param chat_model_name: 聊天模型名称，默认且推荐使用 deepseek-chat
        :param reasoning_model_name: 推理模型名称，默认且推荐使用 deepseek-reasoner
        :param temperature: LLM 温度参数，默认 0.2（推荐）
        """
        logger.info("初始化数据分析智能体")
        self.chat_model = get_chat_model(
            model_name=chat_model_name,
            temperature=temperature
        )
        self.reasoning_model = get_reasoning_model(
            model_name=reasoning_model_name,
            temperature=temperature
        )
        
        # TODO: 初始化数据库连接（预留接口）
        # 当数据库连接后，使用以下代码：
        self.db_config = DatabaseConfig.from_env()
        # self.schema_inspector = SchemaInspector(self.db_config)
        
        # TODO: 初始化状态管理
        self.state = {
            "current_task": None,
            "analysis_history": [],
            "data_cache": {},
        }
        
        logger.info("数据分析智能体初始化完成")
    
    def NL_parse_requirement(self, user_query: str) -> Dict[str, Any]:
        """
        使用自然语言提示词模板解析用户需求。
        
        从用户的自然语言描述中提取结构化的分析需求。
        
        :param user_query: 用户的自然语言查询
        :return: 解析后的需求字典（JSON 格式）
        :raises LegalDataError: 如果解析失败
        """
        logger.info(f"开始解析用户需求: {user_query[:50]}...")
        
        # 获取可用字段列表
        available_fields = self._get_available_fields()
        
        # 调用 LLM 进行需求解析
        messages = NL_REQUIREMENT_PARSE_PROMPT.to_messages(
            user_input=user_query,
            user_query=user_query,
            available_fields=", ".join(available_fields)
        )
        
        logger.debug("调用 LLM 进行需求解析")
        response = self.chat_model.invoke(messages)
        response_text = response.content
        
        # 提取并解析 JSON 结果
        try:
            json_text = self._extract_json_from_response(response_text)
            requirement = json.loads(json_text)
            logger.info("✅ 需求解析成功完成")
            logger.debug(f"需求解析完成: {requirement}")
            return requirement
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            logger.error(f"响应文本: {response_text[:200]}...")
            raise LegalDataError(f"无法解析需求: {e}", {"user_query": user_query}) from e

    def parse_requirement_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        从 Word 或 PDF 文件中解析用户需求。
        
        支持的文件格式：
        - .docx (Word 文档)
        - .pdf (PDF 文档)
        
        :param file_path: 文件路径
        :return: 解析后的需求字典（JSON 格式）
        :raises LegalDataError: 如果文件读取失败或解析失败
        """
        logger.info(f"开始从文件解析需求: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise LegalDataError(f"文件不存在: {file_path}", {"file_path": file_path})
        
        # 提取文件文本内容
        file_ext = Path(file_path).suffix.lower()
        try:
            if file_ext == '.docx':
                document_text = self._read_docx(file_path)
            elif file_ext == '.doc':
                document_text = self._read_doc(file_path)
            elif file_ext == '.pdf':
                document_text = self._read_pdf(file_path)
            else:
                raise LegalDataError(
                    f"不支持的文件格式: {file_ext}。支持格式: .doc, .docx, .pdf",
                    {"file_path": file_path, "file_ext": file_ext}
                )
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            raise LegalDataError(f"读取文件失败: {e}", {"file_path": file_path}) from e
        
        if not document_text or not document_text.strip():
            raise LegalDataError("文件内容为空", {"file_path": file_path})
        
        logger.debug(f"成功读取文件，文本长度: {len(document_text)} 字符")
        
        # 获取可用字段列表
        available_fields = self._get_available_fields()
        
        # 调用 LLM 进行需求解析（使用 REQUIREMENT_PARSE_PROMPT，因为这是用于起诉状/答辩状的）
        messages = REQUIREMENT_PARSE_PROMPT.to_messages(
            user_input="",
            document_text=document_text,
            available_fields=", ".join(available_fields)
        )
        
        logger.debug("调用 LLM 进行需求解析")
        response = self.chat_model.invoke(messages)
        response_text = response.content
        
        # 提取并解析 JSON 结果
        try:
            json_text = self._extract_json_from_response(response_text)
            requirement = json.loads(json_text)
            logger.info("✅ 需求解析成功完成")
            logger.debug(f"需求解析完成: {requirement}")
            return requirement
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            logger.error(f"响应文本: {response_text[:200]}...")
            raise LegalDataError(f"无法解析需求: {e}", {"file_path": file_path}) from e

    def _read_docx(self, file_path: str) -> str:
        """
        读取 Word 文档内容（.docx 格式）。
        
        :param file_path: Word 文件路径
        :return: 文档文本内容
        """
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "需要安装 python-docx 库来读取 Word 文件。"
                "请运行: pip install python-docx"
            )
 
        try:
            doc = Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(paragraphs)
        except Exception as e:
            logger.error(f"读取 Word 文件失败: {e}")
            raise

    def _read_doc(self, file_path: str) -> str:
        """
        读取 Word 文档内容（.doc 格式，旧版 Word 格式）。
        
        :param file_path: Word 文件路径
        :return: 文档文本内容
        """
        errors = []
        
        # Windows 系统：优先尝试使用 win32com（需要安装 pywin32）
        if os.name == 'nt':  # Windows
            try:
                import win32com.client
                try:
                    word = win32com.client.Dispatch("Word.Application")
                    word.Visible = False
                    doc = word.Documents.Open(os.path.abspath(file_path))
                    text = doc.Content.Text
                    doc.Close()
                    word.Quit()
                    logger.debug("使用 win32com 成功读取 .doc 文件")
                    return text
                except Exception as e:
                    errors.append(f"win32com: {str(e)}")
                    logger.debug(f"使用 win32com 读取 .doc 文件失败: {e}")
            except ImportError:
                errors.append("win32com 未安装")
                logger.debug("win32com 未安装，跳过")
        
        # 优先尝试使用 textract（支持多种格式）
        try:
            import textract
            try:
                text = textract.process(file_path).decode('utf-8')
                logger.debug("使用 textract 成功读取 .doc 文件")
                return text
            except Exception as e:
                errors.append(f"textract: {str(e)}")
                logger.debug(f"使用 textract 读取 .doc 文件失败: {e}")
        except ImportError:
            errors.append("textract 未安装")
            logger.debug("textract 未安装，跳过")
        
        # 尝试使用 docx2txt（注意：docx2txt 主要用于 .docx，但可以尝试）
        try:
            import docx2txt
            try:
                # docx2txt 主要用于 .docx，但可以尝试处理 .doc
                text = docx2txt.process(file_path)
                if text and text.strip():
                    logger.debug("使用 docx2txt 成功读取 .doc 文件")
                    return text
                else:
                    errors.append("docx2txt: 返回空内容")
                    logger.debug("docx2txt 返回空内容")
            except Exception as e:
                errors.append(f"docx2txt: {str(e)}")
                logger.debug(f"使用 docx2txt 读取 .doc 文件失败: {e}")
        except ImportError:
            errors.append("docx2txt 未安装")
            logger.debug("docx2txt 未安装，跳过")
        
        # 尝试使用 antiword（需要系统安装 antiword，Linux/Mac）
        if os.name != 'nt':  # 非 Windows 系统
            try:
                result = subprocess.run(
                    ['antiword', file_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0 and result.stdout.strip():
                    logger.debug("使用 antiword 成功读取 .doc 文件")
                    return result.stdout
                else:
                    errors.append(f"antiword: {result.stderr}")
                    logger.debug(f"使用 antiword 读取 .doc 文件失败: {result.stderr}")
            except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                errors.append(f"antiword: {str(e)}")
                logger.debug(f"antiword 不可用: {e}")
        
        # 如果所有方法都失败，抛出详细的错误信息
        error_msg = "无法读取 .doc 文件。尝试的方法和错误：\n"
        for i, error in enumerate(errors, 1):
            error_msg += f"{i}. {error}\n"
        error_msg += "\n请尝试安装以下库之一：\n"
        if os.name == 'nt':
            error_msg += "1. pywin32: pip install pywin32 (Windows 推荐)\n"
        error_msg += "2. textract: pip install textract\n"
        error_msg += "3. docx2txt: pip install docx2txt (主要用于 .docx)\n"
        if os.name != 'nt':
            error_msg += "4. 或安装系统工具 antiword（Linux/Mac）\n"
        
        raise ImportError(error_msg)

    def _read_pdf(self, file_path: str) -> str:
        """
        读取 PDF 文档内容。
        
        :param file_path: PDF 文件路径
        :return: 文档文本内容
        """
        try:
            import PyPDF2
        except ImportError:
            try:
                import pdfplumber
            except ImportError:
                raise ImportError(
                    "需要安装 PyPDF2 或 pdfplumber 库来读取 PDF 文件。"
                    "请运行: pip install PyPDF2 或 pip install pdfplumber"
                )
            else:
                # 使用 pdfplumber
                try:
                    text_content = []
                    with pdfplumber.open(file_path) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                text_content.append(text)
                    return "\n".join(text_content)
                except Exception as e:
                    logger.error(f"使用 pdfplumber 读取 PDF 文件失败: {e}")
                    raise
        else:
            # 使用 PyPDF2
            try:
                text_content = []
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                return "\n".join(text_content)
            except Exception as e:
                logger.error(f"使用 PyPDF2 读取 PDF 文件失败: {e}")
                raise

    
    def _get_available_fields(self) -> List[str]:
        """
        获取可用的数据字段列表。
        
        :return: 字段名称列表
        """
        # TODO: 从数据库 schema 获取可用字段
        # 当数据库连接后，使用以下代码：
        # if self.schema_inspector:
        #     tables = self.schema_inspector.get_all_tables()
        #     fields = []
        #     for table in tables:
        #         columns = self.schema_inspector.get_columns(table)
        #         fields.extend([col["column_name"] for col in columns])
        #     return fields
        
        # 当前：返回模拟字段列表
        logger.debug("使用模拟字段列表")
        return [
            "case_id",
            "case_type",
            "case_date",
            "region",
            "court_level",
            "procedure_type",
            "judgment_result",
            "amount",
            "plaintiff",
            "defendant",
        ]
    
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