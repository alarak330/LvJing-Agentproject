"""
法律数据分析工具模块。

提供面向中国法律的数据驱动类案分析所需的各种工具函数。
"""

from .expand_exceptions import (
    LegalDataError,
    CaseParseError,
    DataValidationError,
    SimilarityCalculationError,
    StatisticsError,
)

from .constants import (
    CASE_TYPES,
    COURT_LEVELS,
    PROCEDURE_TYPES,
    DATE_FORMATS,
    CIVIL_SUBTYPES,
    STATISTICS_DIMENSIONS,
    SIMILARITY_WEIGHTS,
)

# 法律文本解析工具
from .legal_parser import (
    parse_case_number,
    parse_court_name,
    parse_law_reference,
    parse_date,
)

# 统计分析工具
from .statistics_analyzer import (
    calculate_trend,
    calculate_distribution,
    calculate_win_rate,
    calculate_average_amount,
    group_by_dimension,
)

# 数据格式化工具
from .formatter import (
    format_case_summary,
    format_statistics,
    format_table_data,
    format_chart_data,
    format_law_reference,
    format_date_range,
    format_percentage,
    format_amount,
)

__all__ = [
    # 异常类
    "LegalDataError",
    "CaseParseError",
    "DataValidationError",
    "SimilarityCalculationError",
    "StatisticsError",
    # 常量
    "CASE_TYPES",
    "COURT_LEVELS",
    "PROCEDURE_TYPES",
    "DATE_FORMATS",
    "CIVIL_SUBTYPES",
    "STATISTICS_DIMENSIONS",
    "SIMILARITY_WEIGHTS",
    # 法律文本解析
    "parse_case_number",
    "parse_court_name",
    "parse_law_reference",
    "parse_date",
    # 统计分析
    "calculate_trend",
    "calculate_distribution",
    "calculate_win_rate",
    "calculate_average_amount",
    "group_by_dimension",
    # 数据格式化
    "format_case_summary",
    "format_statistics",
    "format_table_data",
    "format_chart_data",
    "format_law_reference",
    "format_date_range",
    "format_percentage",
    "format_amount",
]

