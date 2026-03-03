"""
论坛辩论提示词模板。

用于论坛主持人协调两个智能体进行类案报告相关的辩论。
"""

from .base import create_prompt_template

# 论坛主持人系统提示词（已简化，实际不使用，保留作为参考）
DEBATE_MODERATOR_PROMPT = create_prompt_template(
    name="debate_moderator",
    system_role="""你是一个专业的法律智能体论坛主持人，负责协调数据分析智能体和数据挖掘智能体之间的辩论，生成法律类案报告。""",
    template="""法律类案报告论坛主持人提示词模板（保留作为参考）"""
)

# 辩论轮次提示词
DEBATE_ROUND_PROMPT = create_prompt_template(
    name="debate_round",
    system_role="""你是论坛主持人，正在协调两个智能体进行法律类案报告的辩论。

当前任务：{task_description}

辩论历史：
{debate_history}

请评估当前状态并决定下一步：
1. 如果数据分析智能体需要提出数据要求，引导它
2. 如果数据挖掘智能体需要搜索数据，引导它
3. 如果数据需要进一步筛选，继续辩论
4. 如果数据已满足要求，结束辩论""",
    template="""当前辩论状态：
- 用户需求：{user_requirement}
- 当前轮次：第 {round_number} 轮
- 数据分析智能体的要求：{analysis_requirement}
- 数据挖掘智能体返回的数据：{mining_data}
- 数据评估结果：{evaluation_result}

请决定下一步行动并给出指令。"""
)

# 辩论总结提示词
DEBATE_SUMMARY_PROMPT = create_prompt_template(
    name="debate_summary",
    system_role="""你是论坛主持人，需要总结辩论结果并生成最终的法律类案报告。

你已经协调数据分析智能体和数据挖掘智能体完成了数据筛选和分析，现在需要：
1. 总结辩论过程中找到的关键法律条文
2. 总结数据分析智能体的分析结果
3. 整合生成完整的类案报告""",
    template="""辩论已完成，请总结并生成最终报告。

用户需求：
{user_requirement}

辩论过程：
{debate_history}

最终数据：
{final_data}

分析结果：
{analysis_result}

请生成完整的法律类案报告，包括：
1. 案件需求概述
2. 相关法律条文（从数据挖掘智能体获取）
3. 数据分析结果（从数据分析智能体获取）
4. 综合分析和建议

报告格式应为结构化的 JSON：
{{
    "report": {{
        "title": "报告标题",
        "requirement_summary": "需求概述",
        "relevant_laws": [
            {{
                "law_name": "法律名称",
                "article_number": "条号",
                "article_content": "条文内容",
                "relevance": "相关性说明"
            }}
        ],
        "data_analysis": "数据分析结果",
        "comprehensive_analysis": "综合分析",
        "recommendations": "建议"
    }},
    "summary": "报告摘要"
}}"""
)

