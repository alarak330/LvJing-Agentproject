"""
统计分析工具。

提供数据驱动的统计分析功能，支持趋势分析、分布分析等。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Any
import statistics

from loguru import logger
from .exceptions import StatisticsError


def calculate_trend(
    data: List[Dict[str, Any]],
    time_field: str = "date",
    value_field: str = "count",
    time_unit: str = "month"
) -> Dict[str, Any]:
    """
    计算时间趋势。
    
    :param data: 数据列表，每个元素包含时间和数值字段
    :param time_field: 时间字段名
    :param value_field: 数值字段名
    :param time_unit: 时间单位（day/month/year）
    :return: 趋势数据，包含时间序列和统计信息
    
    example:
        >>> cases = [
        ...     {"date": "2023-01", "count": 10},
        ...     {"date": "2023-02", "count": 15},
        ...     {"date": "2023-03", "count": 12}
        ... ]
        >>> calculate_trend(cases, time_field="date", value_field="count")
        {
            "time_series": [...],
            "trend": "上升",
            "growth_rate": 0.2
        }
    """
    logger.debug(f"calculate_trend called with {len(data)} items, "
                 f"time_field={time_field}, value_field={value_field}, time_unit={time_unit}")
    if not data:
        raise StatisticsError("数据为空，无法计算趋势", analysis_type="trend")
    
    # 按时间排序
    sorted_data = sorted(data, key=lambda x: x.get(time_field, ""))
    
    # 提取时间序列
    time_series = [
        {
            "time": item.get(time_field),
            "value": item.get(value_field, 0)
        }
        for item in sorted_data
    ]
    
    # 计算趋势方向
    values = [item["value"] for item in time_series]
    if len(values) < 2:
        trend = "平稳"
        growth_rate = 0.0
    else:
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        if avg_second > avg_first * 1.1:
            trend = "上升"
        elif avg_second < avg_first * 0.9:
            trend = "下降"
        else:
            trend = "平稳"
        
        growth_rate = (avg_second - avg_first) / avg_first if avg_first > 0 else 0.0
    
    result = {
        "time_series": time_series,
        "trend": trend,
        "growth_rate": growth_rate,
        "total": sum(values),
        "average": statistics.mean(values),
        "median": statistics.median(values),
    }
    logger.debug(f"calculate_trend result summary: trend={trend}, "
                 f"growth_rate={growth_rate}, total={result['total']}")
    return result


def calculate_distribution(
    data: List[Dict[str, Any]],
    by: str,
    value_field: Optional[str] = None
) -> Dict[str, Any]:
    """
    计算分布统计。
    
    :param data: 数据列表
    :param by: 分组字段名
    :param value_field: 可选的数值字段，用于计算总和/平均值
    :return: 分布统计结果
    
    example:
        >>> cases = [
        ...     {"court_level": "中级人民法院", "amount": 10000},
        ...     {"court_level": "基层人民法院", "amount": 5000}
        ... ]
        >>> calculate_distribution(cases, by="court_level", value_field="amount")
        {
            "中级人民法院": {"count": 1, "total": 10000, "percentage": 66.67},
            "基层人民法院": {"count": 1, "total": 5000, "percentage": 33.33}
        }
    """
    logger.debug(f"calculate_distribution called with {len(data)} items, by={by}, "
                 f"value_field={value_field}")
    if not data:
        raise StatisticsError("数据为空，无法计算分布", analysis_type="distribution")
    
    distribution = defaultdict(lambda: {"count": 0, "total": 0, "values": []})
    total_count = len(data)
    
    for item in data:
        key = item.get(by, "未知")
        distribution[key]["count"] += 1
        
        if value_field and value_field in item:
            value = item[value_field]
            if isinstance(value, (int, float)):
                distribution[key]["total"] += value
                distribution[key]["values"].append(value)
    
    # 计算百分比和平均值
    result = {}
    for key, stats in distribution.items():
        result[key] = {
            "count": stats["count"],
            "percentage": round(stats["count"] / total_count * 100, 2),
        }
        
        if value_field:
            result[key]["total"] = stats["total"]
            if stats["values"]:
                result[key]["average"] = statistics.mean(stats["values"])
                result[key]["median"] = statistics.median(stats["values"])
    
    logger.debug(f"calculate_distribution result keys: {list(result.keys())}")
    return result


def calculate_win_rate(
    cases: List[Dict[str, Any]],
    result_field: str = "judgment_result"
) -> Dict[str, float]:
    """
    计算胜诉率统计。
    
    :param cases: 案件列表
    :param result_field: 判决结果字段名
    :return: 胜诉率统计
    
    example:
        >>> cases = [
        ...     {"judgment_result": "支持"},
        ...     {"judgment_result": "驳回"},
        ...     {"judgment_result": "支持"}
        ... ]
        >>> calculate_win_rate(cases)
        {
            "support_rate": 66.67,
            "reject_rate": 33.33,
            "total": 3
        }
    """
    logger.debug(f"calculate_win_rate called with {len(cases)} cases, "
                 f"result_field={result_field}")
    if not cases:
        raise StatisticsError("案件数据为空，无法计算胜诉率", analysis_type="win_rate")
    
    support_count = 0
    reject_count = 0
    partial_count = 0
    
    for case in cases:
        result = str(case.get(result_field, "")).strip()
        if "支持" in result and "部分" not in result:
            support_count += 1
        elif "驳回" in result:
            reject_count += 1
        elif "部分支持" in result:
            partial_count += 1
    
    total = len(cases)
    
    result = {
        "support_rate": round(support_count / total * 100, 2) if total > 0 else 0.0,
        "reject_rate": round(reject_count / total * 100, 2) if total > 0 else 0.0,
        "partial_rate": round(partial_count / total * 100, 2) if total > 0 else 0.0,
        "total": total,
        "support_count": support_count,
        "reject_count": reject_count,
        "partial_count": partial_count,
    }
    logger.debug(f"calculate_win_rate result: {result}")
    return result


def calculate_average_amount(
    cases: List[Dict[str, Any]],
    amount_field: str = "amount"
) -> Dict[str, float]:
    """
    计算平均金额统计。
    
    :param cases: 案件列表
    :param amount_field: 金额字段名
    :return: 金额统计信息
    """
    logger.debug(f"calculate_average_amount called with {len(cases)} cases, "
                 f"amount_field={amount_field}")
    amounts = [
        case.get(amount_field, 0)
        for case in cases
        if isinstance(case.get(amount_field), (int, float)) and case.get(amount_field, 0) > 0
    ]
    
    if not amounts:
        empty_result = {
            "average": 0.0,
            "median": 0.0,
            "min": 0.0,
            "max": 0.0,
            "total": 0.0,
            "count": 0,
        }
        logger.debug("calculate_average_amount no valid amounts, returning zeros")
        return empty_result
    
    result = {
        "average": round(statistics.mean(amounts), 2),
        "median": round(statistics.median(amounts), 2),
        "min": round(min(amounts), 2),
        "max": round(max(amounts), 2),
        "total": round(sum(amounts), 2),
        "count": len(amounts),
    }
    logger.debug(f"calculate_average_amount result: {result}")
    return result


def group_by_dimension(
    data: List[Dict[str, Any]],
    dimensions: List[str]
) -> Dict[str, Any]:
    """
    多维度分组统计。
    
    :param data: 数据列表
    :param dimensions: 维度字段列表
    :return: 多维度分组结果
    
    example:
        >>> cases = [
        ...     {"court_level": "中院", "case_type": "民事", "count": 10},
        ...     {"court_level": "中院", "case_type": "刑事", "count": 5}
        ... ]
        >>> group_by_dimension(cases, ["court_level", "case_type"])
        {
            "中院": {
                "民事": {"count": 10},
                "刑事": {"count": 5}
            }
        }
    """
    logger.debug(f"group_by_dimension called with {len(data)} items, "
                 f"dimensions={dimensions}")
    if not dimensions:
        raise StatisticsError("维度列表为空", analysis_type="group_by_dimension")
    
    grouped = defaultdict(lambda: defaultdict(dict))
    
    for item in data:
        # 构建分组键
        keys = []
        for dim in dimensions:
            keys.append(str(item.get(dim, "未知")))
        
        # 递归构建嵌套字典
        current = grouped
        for i, key in enumerate(keys[:-1]):
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 最后一层存储数据
        last_key = keys[-1]
        if last_key not in current:
            current[last_key] = {"count": 0, "items": []}
        
        current[last_key]["count"] += 1
        current[last_key]["items"].append(item)
    
    result = dict(grouped)
    logger.debug(f"group_by_dimension result top-level keys: {list(result.keys())}")
    return result


