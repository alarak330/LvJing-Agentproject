"""
过滤相关的提示词模板。

包含条件提取、匹配判断、数据验证等过滤场景的提示词。
"""

from __future__ import annotations

from .base import PromptTemplate, create_prompt_template


# 过滤条件提取提示词
FILTER_CRITERIA_EXTRACT_PROMPT = create_prompt_template(
    name="filter_criteria_extract",
    system_role="""
你是一个法律数据过滤条件提取专家，擅长从用户输入中提取精确的过滤条件。

你的任务是：
1. 识别所有过滤条件（案件类型、时间、地区、法院层级等）
2. 处理模糊条件和精确条件
3. 识别条件之间的逻辑关系（AND/OR）
4. 转换为可执行的过滤规则""",
    template="""请从以下用户输入中提取过滤条件：

用户输入：{user_input}

可用的过滤字段：
{available_fields}

请按照以下 JSON 格式输出过滤条件：
{{
    "conditions": [
        {{
            "field": "字段名",
            "operator": "操作符（=, !=, >, <, >=, <=, IN, LIKE, BETWEEN）",
            "value": "值或值列表",
            "match_type": "精确/模糊"
        }}
    ],
    "logic": "AND/OR（条件之间的逻辑关系）",
    "time_range": {{
        "start": "开始时间",
        "end": "结束时间"
    }},
    "fuzzy_fields": ["需要模糊匹配的字段列表"]
}}""",
    examples=[
        (
            "筛选2023年北京地区的合同纠纷案件",
            """{
    "conditions": [
        {
            "field": "case_type",
            "operator": "=",
            "value": "民事",
            "match_type": "精确"
        },
        {
            "field": "subtype",
            "operator": "=",
            "value": "合同纠纷",
            "match_type": "精确"
        },
        {
            "field": "region",
            "operator": "=",
            "value": "北京",
            "match_type": "精确"
        },
        {
            "field": "case_date",
            "operator": "BETWEEN",
            "value": ["2023-01-01", "2023-12-31"],
            "match_type": "精确"
        }
    ],
    "logic": "AND",
    "time_range": {
        "start": "2023-01-01",
        "end": "2023-12-31"
    },
    "fuzzy_fields": []
}"""
        ),
        (
            "查找包含'知识产权'关键词的案件，时间在2022年到2023年之间",
            """{
    "conditions": [
        {
            "field": "case_description",
            "operator": "LIKE",
            "value": "%知识产权%",
            "match_type": "模糊"
        },
        {
            "field": "case_date",
            "operator": "BETWEEN",
            "value": ["2022-01-01", "2023-12-31"],
            "match_type": "精确"
        }
    ],
    "logic": "AND",
    "time_range": {
        "start": "2022-01-01",
        "end": "2023-12-31"
    },
    "fuzzy_fields": ["case_description"]
}"""
        )
    ]
)


# 条件匹配提示词
CRITERIA_MATCH_PROMPT = create_prompt_template(
    name="criteria_match",
    system_role="""
你是一个数据匹配判断专家，擅长判断数据记录是否满足给定的过滤条件。
你的任务是：
1. 精确匹配：判断字段值是否完全符合条件
2. 模糊匹配：判断字段值是否包含关键词或符合模式
3. 范围匹配：判断数值或日期是否在指定范围内
4. 组合条件：处理多个条件的逻辑组合（AND/OR）""",
    template="""请判断以下数据记录是否满足给定的过滤条件：

数据记录：
{data_record}

过滤条件：
{filter_criteria}

请按照以下 JSON 格式输出判断结果：
{{
    "matches": true/false,
    "matched_conditions": ["匹配的条件列表"],
    "unmatched_conditions": ["不匹配的条件列表"],
    "match_score": 0.95,
    "reasoning": "判断理由"
}}""",
    examples=[
        (
            """数据记录：
{
    "case_id": 1,
    "case_type": "民事",
    "subtype": "合同纠纷",
    "region": "北京",
    "case_date": "2023-06-15",
    "court_level": "中级"
}

过滤条件：
{
    "conditions": [
        {"field": "case_type", "operator": "=", "value": "民事"},
        {"field": "region", "operator": "=", "value": "北京"},
        {"field": "case_date", "operator": "BETWEEN", "value": ["2023-01-01", "2023-12-31"]}
    ],
    "logic": "AND"
}""",
            """{
    "matches": true,
    "matched_conditions": [
        "case_type = 民事",
        "region = 北京",
        "case_date BETWEEN 2023-01-01 AND 2023-12-31"
    ],
    "unmatched_conditions": [],
    "match_score": 1.0,
    "reasoning": "所有条件都满足：案件类型是民事，地区是北京，日期在2023年内"
}"""
        ),
        (
            """数据记录：
{
    "case_id": 2,
    "case_type": "刑事",
    "region": "上海",
    "case_date": "2023-05-20"
}

过滤条件：
{
    "conditions": [
        {"field": "case_type", "operator": "=", "value": "民事"},
        {"field": "region", "operator": "=", "value": "北京"}
    ],
    "logic": "AND"
}""",
            """{
    "matches": false,
    "matched_conditions": [],
    "unmatched_conditions": [
        "case_type = 民事（实际是刑事）",
        "region = 北京（实际是上海）"
    ],
    "match_score": 0.0,
    "reasoning": "案件类型和地区都不匹配，不满足条件"
}"""
        )
    ]
)


# 数据验证提示词
DATA_VALIDATION_PROMPT = create_prompt_template(
    name="data_validation",
    system_role="""你是一个数据质量验证专家，擅长检查数据的完整性、准确性和一致性。

你的任务是：
1. 检查必需字段是否缺失
2. 验证字段值的格式和范围
3. 检查数据的一致性（如日期逻辑、关联关系）
4. 识别异常值和错误数据
5. 评估数据质量分数""",
    template="""请验证以下数据的质量和完整性：

数据记录：
{data_record}

数据表结构：
{schema_info}

验证规则：
{validation_rules}

请按照以下 JSON 格式输出验证结果：
{{
    "is_valid": true/false,
    "quality_score": 0.95,
    "missing_fields": ["缺失字段列表"],
    "invalid_fields": [
        {{
            "field": "字段名",
            "issue": "问题描述",
            "expected": "期望值或格式",
            "actual": "实际值"
        }}
    ],
    "warnings": ["警告信息列表"],
    "suggestions": ["改进建议列表"]
}}""",
    examples=[
        (
            """数据记录：
{
    "case_id": 1,
    "case_type": "民事",
    "case_date": "2023-13-45",
    "region": "北京",
    "judgment_result": null
}

数据表结构：
{
    "case_id": {"type": "int", "required": true},
    "case_type": {"type": "string", "required": true, "values": ["民事", "刑事", "行政"]},
    "case_date": {"type": "date", "required": true, "format": "YYYY-MM-DD"},
    "region": {"type": "string", "required": true},
    "judgment_result": {"type": "string", "required": false}
}

验证规则：
{
    "required_fields": ["case_id", "case_type", "case_date", "region"],
    "date_format": "YYYY-MM-DD",
    "case_type_values": ["民事", "刑事", "行政"]
}""",
            """{
    "is_valid": false,
    "quality_score": 0.6,
    "missing_fields": [],
    "invalid_fields": [
        {
            "field": "case_date",
            "issue": "日期格式错误",
            "expected": "YYYY-MM-DD（如 2023-06-15）",
            "actual": "2023-13-45（月份和日期超出范围）"
        },
        {
            "field": "judgment_result",
            "issue": "字段值为空（虽然非必需，但建议填充）",
            "expected": "字符串值",
            "actual": "null"
        }
    ],
    "warnings": [
        "日期字段格式错误，无法进行时间相关的分析",
        "判决结果字段为空，可能影响分析完整性"
    ],
    "suggestions": [
        "修正 case_date 字段为有效日期格式",
        "如果 judgment_result 可用，建议填充该字段"
    ]
}"""
        )
    ]
)

