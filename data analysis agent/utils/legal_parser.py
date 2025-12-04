"""
法律文本解析工具。

提供解析法律文本、提取结构化信息的功能。
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger
from .constants import (
    CASE_NUMBER_PATTERNS,
    LAW_REFERENCE_PATTERNS,
    DATE_FORMATS,
    COURT_LEVELS,
)
from .exceptions import CaseParseError


def parse_case_number(case_number: str) -> Dict[str, str]:
    """
    解析案件编号。
    
    支持格式: (2023)京01民终1234号
    
    :param case_number: 案件编号字符串
    :return: 解析后的字典，包含年份、法院、序号、类型、程序、编号
    :raises CaseParseError: 当无法解析案件编号时
    
    example:
        >>> parse_case_number("(2023)京01民终1234号")
        {
            "year": "2023",
            "court": "京",
            "sequence": "01",
            "case_type": "民",
            "procedure": "终",
            "number": "1234"
        }
    """

    pattern = CASE_NUMBER_PATTERNS["standard"]
    match = re.search(pattern, case_number)

    if not match:
        raise CaseParseError(
            f"无法解析案件编号: {case_number}",
            case_text=case_number
        )
    parsed_dict = {
        "year": match.group(1),
        "court": match.group(2),
        "sequence": match.group(3),
        "case_type": match.group(4),
        "procedure": match.group(5),
        "number": match.group(6),
    }

    logger.debug(parsed_dict)
    return parsed_dict


def parse_court_name(court_name: str) -> Dict[str, str]:
    """
    解析法院名称，识别法院层级和地区。
    
    :param court_name: 法院名称
    :return: 包含层级、地区、完整名称的字典
    
    example:
        >>> parse_court_name("北京市第一中级人民法院")
        {
            "level": "中级人民法院",
            "region": "北京",
            "full_name": "北京市第一中级人民法院"
        }
    """

    result = {
        "full_name": court_name,
        "level": None,
        "region": None,
    }

    # 识别法院层级
    for level_key, level_name in COURT_LEVELS.items():
        if level_name in court_name:
            result["level"] = level_name
            break

    # 提取地区
    # 匹配省/市/自治区名称
    region_pattern = r"([^省市区县]+)(?:省|市|自治区|特别行政区)"
    match = re.search(region_pattern, court_name)
    if match:
        result["region"] = match.group(1)
        logger.debug(match)
    return result


def parse_law_reference(text: str) -> List[Dict[str, str]]:
    """
    提取文本中的法条引用。
    
    :param text: 包含法条引用的文本
    :return: 法条引用列表，每个元素包含法律名称和条号
    
    example:
        >>> parse_law_reference("根据《民法典》第123条和《合同法》第45条")
        [
            {"law": "民法典", "article": "123"},
            {"law": "合同法", "article": "45"}
        ]
    """
    references = []

    # 匹配通用法条引用格式
    pattern = LAW_REFERENCE_PATTERNS["general"]
    matches = re.finditer(pattern, text)

    for match in matches:
        references.append({
            "law": match.group(1),
            "article": match.group(2),
            "full_text": match.group(0),
        })
    logger.debug(references)
    return references


def parse_date(date_str: str) -> Optional[datetime]:
    """
    解析法律日期格式。
    
    支持多种日期格式: 2023-01-01, 2023年01月01日, 2023/01/01
    
    :param date_str: 日期字符串
    :return: datetime对象，如果无法解析则返回None
    """
    logger.debug(f"parse_date called with date_str={date_str}")
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(date_str, fmt)
            logger.debug(f"parse_date parsed using format={fmt}: {parsed}")
            return parsed
        except ValueError:
            continue
    logger.debug("parse_date failed to parse date_str")
    return None


def extract_dispute_focus(text: str) -> List[str]:
    """
    提取争议焦点。
    
    :param text: 包含争议焦点的文本
    :return: 争议焦点列表
    
    example:
        >>> extract_dispute_focus("争议焦点：1.合同是否有效 2.违约责任")
        ["合同是否有效", "违约责任"]
    """
    focus_list = []

    # 匹配"争议焦点"后的内容
    pattern = r"争议焦点[：:]\s*(.+?)(?=\n|$)"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        content = match.group(1)
        # 提取编号列表项
        items = re.findall(r"[0-9一二三四五六七八九十]+[.、]\s*([^0-9一二三四五六七八九十]+)", content)
        focus_list.extend([item.strip() for item in items])
    return focus_list


def extract_judgment_result(text: str) -> Dict[str, any]:
    """
    提取判决结果。
    
    :param text: 包含判决结果的文本
    :return: 包含判决类型、金额、支持/驳回等信息的字典
    """
    logger.debug("extract_judgment_result called")
    result = {
        "judgment_type": '?',  # 支持/驳回/部分支持等
        "amount": -1.0,  # 金额
    }

    # 匹配判决类型
    if "支持" in text and "驳回" not in text:
        result["judgment_type"] = "支持"
    elif "驳回" in text and "支持" not in text:
        result["judgment_type"] = "驳回"
    elif "部分支持" in text:
        result["judgment_type"] = "部分支持"

    # 提取金额（简单匹配，实际可能需要更复杂的处理）
    amount_pattern = r"([0-9,，]+\.?\d*)\s*元"
    match = re.search(amount_pattern, text)
    if match:
        amount_str: str = match.group(1).replace(",", "").replace("，", "")
        try:
            result["amount"] = float(amount_str)
        except ValueError:
            pass

    logger.debug(f"extract_judgment_result result: {result}")
    return result

