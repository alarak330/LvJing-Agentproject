"""
数据格式化工具。

提供格式化数据用于报告生成和展示的功能。
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Any, Optional

from loguru import logger


def format_case_summary(case: Dict[str, Any]) -> str:
    """
    格式化案件摘要。
    案件的数据字典必须包括以下键：
    case_number: 案件编号
    court_name: 审理法院
    case_type: 案件类型
    judgement_data: 判决日期
    :param case: 案件数据字典
    :return: 格式化后的案件摘要字符串
    """
    logger.debug(f"format_case_summary called with case keys: {list(case.keys())}")
    parts = []
    
    if case.get("case_number"):
        parts.append(f"案件编号: {case['case_number']}")
    
    if case.get("court_name"):
        parts.append(f"审理法院: {case['court_name']}")
    
    if case.get("case_type"):
        parts.append(f"案件类型: {case['case_type']}")
    
    if case.get("judgment_date"):
        parts.append(f"判决日期: {case['judgment_date']}")
    
    summary = "\n".join(parts)
    logger.debug(f"format_case_summary result: {summary}")
    return summary


def format_statistics(stats: Dict[str, Any], precision: int = 2) -> Dict[str, Any]:
    """
    格式化统计数据。
    
    :param stats: 统计数据字典
    :param precision: 小数精度
    :return: 格式化后的统计数据
    """
    logger.debug(f"format_statistics called with keys: {list(stats.keys())}, "
                 f"precision={precision}")
    formatted: Dict[str, Any] = {}
    
    for key, value in stats.items():
        if isinstance(value, float):
            formatted[key] = round(value, precision)
        elif isinstance(value, dict):
            formatted[key] = format_statistics(value, precision)
        else:
            formatted[key] = value
    
    logger.debug("format_statistics finished formatting")
    return formatted


def format_table_data(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None
) -> List[Dict[str, str]]:
    """
    格式化表格数据。
    
    :param data: 数据列表
    :param columns: 要包含的列名列表，如果为None则包含所有列
    :return: 格式化后的表格数据
    """
    logger.debug(f"format_table_data called with {len(data)} rows, columns={columns}")
    if not data:
        return []
    
    if columns is None:
        columns = list(data[0].keys())
    
    formatted_data = []
    for item in data:
        formatted_item = {}
        for col in columns:
            value = item.get(col, "")
            # 格式化不同类型的值
            if isinstance(value, float):
                formatted_item[col] = f"{value:.2f}"
            elif isinstance(value, datetime):
                formatted_item[col] = value.strftime("%Y-%m-%d")
            else:
                formatted_item[col] = str(value)
        formatted_data.append(formatted_item)
    
    logger.debug(f"format_table_data produced {len(formatted_data)} rows")
    return formatted_data


def format_chart_data(
    data: Dict[str, Any],
    chart_type: str = "line"
) -> Dict[str, Any]:
    """
    格式化图表数据（用于前端可视化）。
    
    :param data: 原始数据
    :param chart_type: 图表类型（line/bar/pie等）
    :return: 格式化后的图表数据
    
    example:
        >>> trend_data = {
        ...     "time_series": [
        ...         {"time": "2023-01", "value": 10},
        ...         {"time": "2023-02", "value": 15}
        ...     ]
        ... }
        >>> format_chart_data(trend_data, "line")
        {
            "labels": ["2023-01", "2023-02"],
            "datasets": [{"data": [10, 15]}]
        }
    """
    logger.debug(f"format_chart_data called with chart_type={chart_type}")
    if chart_type == "line" or chart_type == "bar":
        if "time_series" in data:
            labels = [item["time"] for item in data["time_series"]]
            values = [item["value"] for item in data["time_series"]]
            result = {
                "labels": labels,
                "datasets": [{"data": values, "label": "数值"}]
            }
            logger.debug(f"format_chart_data line/bar result: labels={len(labels)}")
            return result
    
    elif chart_type == "pie":
        labels = list(data.keys())
        values = [data[key].get("count", 0) for key in labels]
        result = {
            "labels": labels,
            "datasets": [{"data": values}]
        }
        logger.debug(f"format_chart_data pie result: labels={labels}")
        return result
    
    logger.debug("format_chart_data fallback, returning original data")
    return data


def format_law_reference(law: str, article: str) -> str:
    """
    格式化法条引用。
    
    :param law: 法律名称
    :param article: 条号
    :return: 格式化后的法条引用字符串
    
    example:
        >>> format_law_reference("民法典", "123")
        "《民法典》第123条"
    """
    result = f"《{law}》第{article}条"
    logger.debug(f"format_law_reference: {result}")
    return result


def format_date_range(start_date: str, end_date: str) -> str:
    """
    格式化日期范围。
    
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: 格式化后的日期范围字符串
    
    example:
        >>> format_date_range("2023-01-01", "2023-12-31")
        "2023年1月1日至2023年12月31日"
    """
    logger.debug(f"format_date_range called with start_date={start_date}, "
                 f"end_date={end_date}")
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        result = f"{start.year}年{start.month}月{start.day}日至{end.year}年{end.month}月{end.day}日"
        logger.debug(f"format_date_range result: {result}")
        return result
    except ValueError:
        result = f"{start_date} 至 {end_date}"
        logger.debug(f"format_date_range fallback result: {result}")
        return result


def format_percentage(value: float, precision: int = 2) -> str:
    """
    格式化百分比。
    
    :param value: 数值（0-1之间或0-100之间）
    :param precision: 小数精度
    :return: 格式化后的百分比字符串
    
    example:
        >>> format_percentage(0.6667)
        "66.67%"
        >>> format_percentage(66.67)
        "66.67%"
    """
    logger.debug(f"format_percentage called with value={value}, precision={precision}")
    if value > 1:
        value = value / 100
    result = f"{value * 100:.{precision}f}%"
    logger.debug(f"format_percentage result: {result}")
    return result


def format_amount(amount: float, unit: str = "元") -> str:
    """
    格式化金额。
    
    :param amount: 金额数值
    :param unit: 单位
    :return: 格式化后的金额字符串
    
    example:
        >>> format_amount(1234567.89)
        "1,234,567.89元"
    """
    logger.debug(f"format_amount called with amount={amount}, unit={unit}")
    if amount >= 10000:
        result = f"{amount/10000:.2f}万元"
    else:
        result = f"{amount:,.2f}{unit}"
    logger.debug(f"format_amount result: {result}")
    return result


