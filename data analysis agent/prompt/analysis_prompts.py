"""
分析相关的提示词模板。

包含需求解析、任务生成、意图分类、数据理解等分析场景的提示词。
"""

from __future__ import annotations

from .base import create_prompt_template


# 需求解析提示词（从起诉状/答辩状草稿中解析用户需求）
REQUIREMENT_PARSE_PROMPT = create_prompt_template(
    name="requirement_parse",
    system_role=
"""
你是一个专业的法律文档分析助手，擅长从用户的起诉状或答辩状草稿中提取结构化的分析需求。

你的任务是：
1. 识别案件类型（民事、刑事、行政等）和案件子类型（合同纠纷、侵权纠纷、劳动争议等）
2. 提取当事人信息（原告、被告的基本信息）
3. 识别争议焦点和核心诉求
4. 提取相关法条引用
5. 识别地区信息（如果有提到法院或地区）
6. 提取时间信息（如果有提到日期）
7. 理解用户的分析需求（类案检索、胜诉率分析、赔偿金额参考等）

请严格按照 JSON 格式输出解析结果，不要包含任何额外的文本、说明或代码块标记。
""",
    template=
"""
请仔细分析以下起诉状/答辩状草稿，提取关键信息用于类案检索和分析：

文档内容：
{document_text}

可用的数据字段：
{available_fields}

请按照以下 JSON 格式输出解析结果：
{{
    "case_type": "案件类型（民事/刑事/行政/执行）",
    "case_subtype": "案件子类型（如：合同纠纷、侵权纠纷、劳动争议等）",
    "parties": {{
        "plaintiff": {{
            "name": "原告姓名或名称",
            "type": "个人/企业/其他",
            "region": "原告所在地区（如果有）"
        }},
        "defendant": {{
            "name": "被告姓名或名称",
            "type": "个人/企业/其他",
            "region": "被告所在地区（如果有）"
        }}
    }},
    "dispute_focus": "争议焦点描述",
    "claims": ["诉讼请求列表"],
    "key_facts": ["关键事实要点列表"],
    "law_references": [
        {{
            "law": "法律名称",
            "article": "条号"
        }}
    ],
    "region": "地区信息（如果有提到法院或地区）",
    "court_level": "法院层级（如果有提到）",
    "time_info": {{
        "mentioned_dates": ["文档中提到的日期列表"],
        "time_range": {{
            "start": "开始时间（如果有）",
            "end": "结束时间（如果有）"
        }}
    }},
    "analysis_requirements": {{
        "primary_goal": "主要分析目标（类案检索/胜诉率分析/赔偿参考等）",
        "secondary_goals": ["次要分析目标列表"]
    }},
    "other_info": {{
        "amount_claimed": "诉讼请求金额（如果有）",
        "case_complexity": "案件复杂程度（简单/中等/复杂）",
        "special_notes": "特殊说明或备注"
    }}
}}

如果某个字段无法从文档中提取，请使用 null 或空列表/空对象。
请只输出 JSON 格式的结果，不要包含任何额外的文本、说明或代码块标记。
""",
    examples=[
        (
            """请仔细分析以下起诉状/答辩状草稿，提取关键信息用于类案检索和分析：

文档内容：
民事起诉状

原告：张三，男，1985年3月15日出生，汉族，住址：北京市朝阳区XX街道XX号，身份证号：11010119850315XXXX。

被告：北京XX科技有限公司，住所地：北京市海淀区XX路XX号，法定代表人：李四。

诉讼请求：
1. 请求判令被告支付拖欠工资人民币50,000元；
2. 请求判令被告支付经济补偿金人民币10,000元；
3. 请求判令被告承担本案诉讼费用。

事实与理由：
原告于2020年1月入职被告公司，担任技术总监职务，月薪25,000元。2023年3月，公司以"业绩不达标"为由突然辞退原告，没有提前通知，也未支付任何补偿。根据《劳动合同法》第四十七条、第八十七条的规定，被告应当支付经济补偿金和赔偿金。

可用的数据字段：
case_id, case_type, case_date, region, court_level, procedure_type, judgment_result, amount, plaintiff, defendant

请按照以下 JSON 格式输出解析结果：
{{
    "case_type": "案件类型（民事/刑事/行政/执行）",
    "case_subtype": "案件子类型（如：合同纠纷、侵权纠纷、劳动争议等）",
    "parties": {{
        "plaintiff": {{
            "name": "原告姓名或名称",
            "type": "个人/企业/其他",
            "region": "原告所在地区（如果有）"
        }},
        "defendant": {{
            "name": "被告姓名或名称",
            "type": "个人/企业/其他",
            "region": "被告所在地区（如果有）"
        }}
    }},
    "dispute_focus": "争议焦点描述",
    "claims": ["诉讼请求列表"],
    "key_facts": ["关键事实要点列表"],
    "law_references": [
        {{
            "law": "法律名称",
            "article": "条号"
        }}
    ],
    "region": "地区信息（如果有提到法院或地区）",
    "court_level": "法院层级（如果有提到）",
    "time_info": {{
        "mentioned_dates": ["文档中提到的日期列表"],
        "time_range": {{
            "start": "开始时间（如果有）",
            "end": "结束时间（如果有）"
        }}
    }},
    "analysis_requirements": {{
        "primary_goal": "主要分析目标（类案检索/胜诉率分析/赔偿参考等）",
        "secondary_goals": ["次要分析目标列表"]
    }},
    "other_info": {{
        "amount_claimed": "诉讼请求金额（如果有）",
        "case_complexity": "案件复杂程度（简单/中等/复杂）",
        "special_notes": "特殊说明或备注"
    }}
}}

如果某个字段无法从文档中提取，请使用 null 或空列表/空对象。
请只输出 JSON 格式的结果，不要包含任何额外的文本、说明或代码块标记。""",
            """{
    "case_type": "民事",
    "case_subtype": "劳动争议",
    "parties": {
        "plaintiff": {
            "name": "张三",
            "type": "个人",
            "region": "北京"
        },
        "defendant": {
            "name": "北京XX科技有限公司",
            "type": "企业",
            "region": "北京"
        }
    },
    "dispute_focus": "公司以业绩不达标为由突然辞退员工，未支付经济补偿金和赔偿金",
    "claims": [
        "支付拖欠工资50000元",
        "支付经济补偿金10000元",
        "承担诉讼费用"
    ],
    "key_facts": [
        "2020年1月入职",
        "月薪25000元",
        "2023年3月被辞退",
        "未提前通知",
        "未支付补偿"
    ],
    "law_references": [
        {
            "law": "劳动合同法",
            "article": "第四十七条"
        },
        {
            "law": "劳动合同法",
            "article": "第八十七条"
        }
    ],
    "region": "北京",
    "court_level": null,
    "time_info": {
        "mentioned_dates": ["2020年1月", "2023年3月"],
        "time_range": {
            "start": "2020-01",
            "end": "2023-03"
        }
    },
    "analysis_requirements": {
        "primary_goal": "类案检索",
        "secondary_goals": ["胜诉率分析", "赔偿金额参考"]
    },
    "other_info": {
        "amount_claimed": "60000",
        "case_complexity": "中等",
        "special_notes": "涉及违法解除劳动合同的赔偿问题"
    }
}"""
        ),
        (
            """请仔细分析以下起诉状/答辩状草稿，提取关键信息用于类案检索和分析：

文档内容：
民事起诉状

原告：上海XX贸易有限公司，住所地：上海市浦东新区XX路XX号，法定代表人：王五。

被告：深圳XX电子科技有限公司，住所地：深圳市南山区XX街XX号，法定代表人：赵六。

诉讼请求：
1. 请求判令被告支付货款人民币1,200,000元及逾期付款利息；
2. 请求判令被告承担本案诉讼费用。

事实与理由：
2022年5月，原被告双方签订《货物买卖合同》，约定被告向原告采购电子产品，合同总金额150万元。原告按约交付货物后，被告仅支付30万元，剩余120万元货款至今未付。根据《民法典》第五百七十七条、第五百七十九条的规定，被告应当支付剩余货款及逾期利息。

可用的数据字段：
case_id, case_type, case_date, region, court_level, procedure_type, judgment_result, amount, plaintiff, defendant

请按照以下 JSON 格式输出解析结果：
{{
    "case_type": "案件类型（民事/刑事/行政/执行）",
    "case_subtype": "案件子类型（如：合同纠纷、侵权纠纷、劳动争议等）",
    "parties": {{
        "plaintiff": {{
            "name": "原告姓名或名称",
            "type": "个人/企业/其他",
            "region": "原告所在地区（如果有）"
        }},
        "defendant": {{
            "name": "被告姓名或名称",
            "type": "个人/企业/其他",
            "region": "被告所在地区（如果有）"
        }}
    }},
    "dispute_focus": "争议焦点描述",
    "claims": ["诉讼请求列表"],
    "key_facts": ["关键事实要点列表"],
    "law_references": [
        {{
            "law": "法律名称",
            "article": "条号"
        }}
    ],
    "region": "地区信息（如果有提到法院或地区）",
    "court_level": "法院层级（如果有提到）",
    "time_info": {{
        "mentioned_dates": ["文档中提到的日期列表"],
        "time_range": {{
            "start": "开始时间（如果有）",
            "end": "结束时间（如果有）"
        }}
    }},
    "analysis_requirements": {{
        "primary_goal": "主要分析目标（类案检索/胜诉率分析/赔偿参考等）",
        "secondary_goals": ["次要分析目标列表"]
    }},
    "other_info": {{
        "amount_claimed": "诉讼请求金额（如果有）",
        "case_complexity": "案件复杂程度（简单/中等/复杂）",
        "special_notes": "特殊说明或备注"
    }}
}}

如果某个字段无法从文档中提取，请使用 null 或空列表/空对象。
请只输出 JSON 格式的结果，不要包含任何额外的文本、说明或代码块标记。""",
            """{
    "case_type": "民事",
    "case_subtype": "合同纠纷",
    "parties": {
        "plaintiff": {
            "name": "上海XX贸易有限公司",
            "type": "企业",
            "region": "上海"
        },
        "defendant": {
            "name": "深圳XX电子科技有限公司",
            "type": "企业",
            "region": "深圳"
        }
    },
    "dispute_focus": "买卖合同货款支付纠纷，被告未按约支付剩余货款",
    "claims": [
        "支付货款1200000元",
        "支付逾期付款利息",
        "承担诉讼费用"
    ],
    "key_facts": [
        "2022年5月签订货物买卖合同",
        "合同总金额150万元",
        "已支付30万元",
        "剩余120万元未付"
    ],
    "law_references": [
        {
            "law": "民法典",
            "article": "第五百七十七条"
        },
        {
            "law": "民法典",
            "article": "第五百七十九条"
        }
    ],
    "region": null,
    "court_level": null,
    "time_info": {
        "mentioned_dates": ["2022年5月"],
        "time_range": {
            "start": "2022-05",
            "end": null
        }
    },
    "analysis_requirements": {
        "primary_goal": "类案检索",
        "secondary_goals": ["胜诉率分析", "利息计算参考"]
    },
    "other_info": {
        "amount_claimed": "1200000",
        "case_complexity": "简单",
        "special_notes": "涉及买卖合同货款支付及逾期利息"
    }
}"""
        )
    ]
)


# 自然语言需求解析提示词
NL_REQUIREMENT_PARSE_PROMPT = create_prompt_template(
    name="nl_requirement_parse",
    system_role=
"""
你是一个专业的法律数据分析助手，擅长从用户的自然语言描述中提取结构化的分析需求。

你的任务是：
1. 识别用户想要分析的案件类型（民事、刑事、行政等）
2. 提取时间范围（年份、月份、日期区间）
3. 识别地区信息（省份、城市、法院）
4. 识别其他过滤条件（法院层级、程序类型等）
5. 理解分析目标（趋势分析、对比分析、统计等）

请严格按照 JSON 格式输出解析结果，不要包含任何额外的文本、说明或代码块标记。
""",
    template=
"""
请解析以下用户需求，提取关键信息：

用户需求：{user_query}
可用的数据字段：{available_fields}

请按照以下 JSON 格式输出解析结果：
{{
    "case_types": ["案件类型列表"],
    "time_range": {{
        "start": "开始时间（YYYY-MM-DD 或 YYYY）",
        "end": "结束时间（YYYY-MM-DD 或 YYYY）"
    }},
    "regions": ["地区列表"],
    "court_levels": ["法院层级列表"],
    "procedure_types": ["程序类型列表"],
    "analysis_goal": "分析目标描述",
    "other_filters": {{
        "key": "value"
    }}
}}

如果某个字段无法从用户需求中提取，请使用 null 或空列表。

请只输出 JSON 格式的结果，不要包含任何额外的文本、说明或代码块标记。
""",
    examples=[
        (
            """请解析以下用户需求，提取关键信息：

用户需求：分析2023年北京地区的合同纠纷案件趋势
可用的数据字段：case_id, case_type, case_date, region, court_level, procedure_type, judgment_result, amount, plaintiff, defendant

请按照以下 JSON 格式输出解析结果：
{{
    "case_types": ["案件类型列表"],
    "time_range": {{
        "start": "开始时间（YYYY-MM-DD 或 YYYY）",
        "end": "结束时间（YYYY-MM-DD 或 YYYY）"
    }},
    "regions": ["地区列表"],
    "court_levels": ["法院层级列表"],
    "procedure_types": ["程序类型列表"],
    "analysis_goal": "分析目标描述",
    "other_filters": {{
        "key": "value"
    }}
}}

如果某个字段无法从用户需求中提取，请使用 null 或空列表。

请只输出 JSON 格式的结果，不要包含任何额外的文本、说明或代码块标记。""",
            """{
    "case_types": ["民事"],
    "time_range": {
        "start": "2023-01-01",
        "end": "2023-12-31"
    },
    "regions": ["北京"],
    "court_levels": [],
    "procedure_types": [],
    "analysis_goal": "趋势分析",
    "other_filters": {
        "subtype": "合同纠纷"
    }
}"""
        ),
        (
            """请解析以下用户需求，提取关键信息：

用户需求：对比2022年和2023年上海地区知识产权案件的胜诉率
可用的数据字段：case_id, case_type, case_date, region, court_level, procedure_type, judgment_result, amount, plaintiff, defendant

请按照以下 JSON 格式输出解析结果：
{{
    "case_types": ["案件类型列表"],
    "time_range": {{
        "start": "开始时间（YYYY-MM-DD 或 YYYY）",
        "end": "结束时间（YYYY-MM-DD 或 YYYY）"
    }},
    "regions": ["地区列表"],
    "court_levels": ["法院层级列表"],
    "procedure_types": ["程序类型列表"],
    "analysis_goal": "分析目标描述",
    "other_filters": {{
        "key": "value"
    }}
}}

如果某个字段无法从用户需求中提取，请使用 null 或空列表。

请只输出 JSON 格式的结果，不要包含任何额外的文本、说明或代码块标记。""",
            """{
    "case_types": ["民事"],
    "time_range": {
        "start": "2022-01-01",
        "end": "2023-12-31"
    },
    "regions": ["上海"],
    "court_levels": [],
    "procedure_types": [],
    "analysis_goal": "对比分析-胜诉率",
    "other_filters": {
        "subtype": "知识产权"
    }
}"""
        )
    ]
)

