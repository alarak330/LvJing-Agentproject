"""
法律相关常量定义。

定义中国法律体系中的各种常量，便于统一管理和使用。
"""

from __future__ import annotations

# 案件类型
CASE_TYPES = {
    "CIVIL": "民事",
    "CRIMINAL": "刑事",
    "ADMINISTRATIVE": "行政",
    "EXECUTION": "执行",
}

# 案件子类型（民事案件常见类型）
CIVIL_SUBTYPES = {
    "CONTRACT": "合同纠纷",
    "TORT": "侵权纠纷",
    "MARRIAGE": "婚姻家庭",
    "INHERITANCE": "继承纠纷",
    "PROPERTY": "物权纠纷",
    "LABOR": "劳动争议",
    "INTELLECTUAL_PROPERTY": "知识产权",
    "COMPANY": "公司纠纷",
    "SECURITIES": "证券纠纷",
    "INSURANCE": "保险纠纷",
}

# 法院层级
COURT_LEVELS = {
    "最高": "最高人民法院",
    "高": "高级人民法院",
    "中": "中级人民法院",
    "基层": "基层人民法院",
    # 专门的法院标识
    "军事": "军事法院",
    "海事": "海事法院",
    "知识产权": "知识产权法院",
    "金融": "金融法院",
    "铁路": "铁路运输法院",
    "互联网": "互联网法院",
    # 特殊
    "巡": "最高人民法院巡回法庭",
}

# 程序类型
PROCEDURE_TYPES = {
    "FIRST_INSTANCE": "一审",
    "SECOND_INSTANCE": "二审",
    "RETRIAL": "再审",
    "EXECUTION": "执行",
    "SPECIAL": "特别程序",
}

# 日期格式
DATE_FORMATS = [
    "%Y-%m-%d",  # 2023-01-01
    "%Y年%m月%d日",  # 2023年01月01日
    "%Y/%m/%d",  # 2023/01/01
    "%Y.%m.%d",  # 2023.01.01
]

# 案件编号格式正则（示例）
CASE_NUMBER_PATTERNS = {
    "standard": r"\((\d{4})\)([^\)\d]+?)(\d+)(民|刑|行|执)(初|终|再)(\d+)号",
    # 格式: (年份)(法院简称)(序号)(案件类型)(程序)(编号)号
    # 示例: (2023)京01民终1234号
}

# 法条引用格式
LAW_REFERENCE_PATTERNS = {
    "civil_code": r"《民法典》第(\d+)条",
    "criminal_law": r"《刑法》第(\d+)条",
    "general": r"《([^》]+)》第(\d+)条",
}

# 统计分析的维度
STATISTICS_DIMENSIONS = {
    "TIME": "时间",
    "COURT_LEVEL": "法院层级",
    "CASE_TYPE": "案件类型",
    "REGION": "地区",
    "JUDGE": "法官",
    "LAW_ARTICLE": "法条",
}

# 相似度计算权重（可根据实际需求调整）
SIMILARITY_WEIGHTS = {
    "facts": 0.4,  # 事实相似度权重
    "dispute_focus": 0.3,  # 争议焦点相似度权重
    "law_article": 0.2,  # 法条相似度权重
    "case_type": 0.1,  # 案件类型相似度权重
}

# 数据质量阈值
DATA_QUALITY_THRESHOLDS = {
    "completeness": 0.8,  # 完整度阈值
    "accuracy": 0.9,  # 准确度阈值
    "consistency": 0.85,  # 一致性阈值
}

# 报告生成相关常量
REPORT_SECTIONS = {
    "SUMMARY": "案件摘要",
    "STATISTICS": "统计分析",
    "SIMILAR_CASES": "类案检索",
    "TREND_ANALYSIS": "趋势分析",
    "COMPARISON": "对比分析",
    "INSIGHTS": "数据洞察",
    "RECOMMENDATIONS": "建议",
}
