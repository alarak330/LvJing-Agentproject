"""
论坛智能体核心模块。

实现论坛辩论功能，协调数据分析智能体和数据挖掘智能体进行法律类案报告生成。
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
import json
from loguru import logger

# LLM 模块（千问大模型）
from .llm import get_chat_model, get_reasoning_model

# 提示词模板
from .prompt import (
    DEBATE_MODERATOR_PROMPT,
    DEBATE_SUMMARY_PROMPT,
)

# 导入两个智能体
import sys
from pathlib import Path
import importlib.util

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 动态导入包含空格的模块
def _import_module_from_path(module_name: str, file_path: Path, parent_dir: Path):
    """从文件路径动态导入模块，处理相对导入"""
    # 将父目录添加到 sys.path 以便处理相对导入
    parent_str = str(parent_dir)
    if parent_str not in sys.path:
        sys.path.insert(0, parent_str)
    
    # 将项目根目录添加到 sys.path（用于绝对导入）
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    # 创建包名（替换空格为下划线）
    package_name = parent_dir.name.replace(" ", "_")
    
    # 先创建并注册包模块，以便相对导入可以工作
    if package_name not in sys.modules:
        # 创建包模块
        package_module = type(sys)(package_name)
        package_module.__path__ = [str(parent_dir)]
        package_module.__file__ = str(parent_dir / "__init__.py") if (parent_dir / "__init__.py").exists() else None
        package_module.__package__ = package_name
        sys.modules[package_name] = package_module
    
    # 在执行主模块之前，先尝试导入可能需要的子模块
    # 这样可以确保相对导入能够工作
    submodules_to_preload = []
    if (parent_dir / "llm").exists():
        submodules_to_preload.append("llm")
    if (parent_dir / "prompts").exists():
        submodules_to_preload.append("prompts")
    if (parent_dir / "prompt").exists():
        submodules_to_preload.append("prompt")
    
    for submod_name in submodules_to_preload:
        submod_path = parent_dir / submod_name
        if f"{package_name}.{submod_name}" not in sys.modules:
            try:
                if submod_path.is_dir():
                    init_file = submod_path / "__init__.py"
                    if init_file.exists():
                        submod_spec = importlib.util.spec_from_file_location(
                            f"{package_name}.{submod_name}",
                            init_file,
                            submodule_search_locations=[str(submod_path)]
                        )
                        if submod_spec and submod_spec.loader:
                            submod_module = importlib.util.module_from_spec(submod_spec)
                            submod_module.__package__ = package_name
                            submod_module.__name__ = f"{package_name}.{submod_name}"
                            submod_spec.loader.exec_module(submod_module)
                            sys.modules[f"{package_name}.{submod_name}"] = submod_module
            except Exception:
                pass  # 忽略子模块导入错误，继续
    
    # 现在导入主模块
    spec = importlib.util.spec_from_file_location(
        f"{package_name}.{module_name}",
        file_path,
        submodule_search_locations=[str(parent_dir)]
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {file_path}")
    
    module = importlib.util.module_from_spec(spec)
    module.__package__ = package_name
    module.__name__ = f"{package_name}.{module_name}"
    
    # 执行模块
    spec.loader.exec_module(module)
    
    # 注册到 sys.modules
    sys.modules[f"{package_name}.{module_name}"] = module
    
    return module

# 导入数据分析智能体
analysis_agent_dir = project_root / "data analysis agent"
analysis_agent_path = analysis_agent_dir / "agent.py"
analysis_module = _import_module_from_path("data_analysis_agent", analysis_agent_path, analysis_agent_dir)
DataAnalysisAgent = analysis_module.DataAnalysisAgent

# 导入数据挖掘智能体
mining_agent_dir = project_root / "data mining agent"
mining_agent_path = mining_agent_dir / "agent.py"
mining_module = _import_module_from_path("data_mining_agent", mining_agent_path, mining_agent_dir)
DataMiningAgent = mining_module.DataMiningAgent


class ForumAgent:
    """
    论坛智能体核心类。
    
    负责协调数据分析智能体和数据挖掘智能体进行法律类案报告的辩论和生成。
    使用千问大模型作为主持人，引导两个智能体不断筛选数据直到满足要求。
    """
    
    def __init__(
        self,
        chat_model_name: str = "qwen-turbo",
        reasoning_model_name: str = "qwen-plus",
        temperature: float = 0.3,
        max_rounds: int = 10,
    ):
        """
        初始化论坛智能体。
        
        :param chat_model_name: 千问聊天模型名称，默认 "qwen-turbo"
        :param reasoning_model_name: 千问推理模型名称，默认 "qwen-plus"
        :param temperature: LLM 温度参数，默认 0.3
        :param max_rounds: 最大辩论轮次，默认 10 轮
        """
        self.name = "ForumAgent"
        logger.info("初始化论坛智能体")
        
        # 初始化千问大模型（主持人）
        self.moderator_model = get_chat_model(
            model_name=chat_model_name,
            temperature=temperature
        )
        self.reasoning_model = get_reasoning_model(
            model_name=reasoning_model_name,
            temperature=temperature
        )
        
        # 初始化两个智能体
        self.analysis_agent = DataAnalysisAgent()
        self.mining_agent = DataMiningAgent()
        
        # 确保两个智能体有 name 属性
        if not hasattr(self.analysis_agent, 'name'):
            self.analysis_agent.name = "DataAnalysisAgent"
        if not hasattr(self.mining_agent, 'name'):
            self.mining_agent.name = "DataMiningAgent"
        
        self.max_rounds = max_rounds
        
        logger.info("论坛智能体初始化完成")
    
    def conduct_debate(
        self,
        user_requirement: str,
    ) -> Dict[str, Any]:
        """
        执行辩论，协调两个智能体完成类案报告生成。
        
        辩论流程：
        1. 数据分析智能体分析用户需求，提出数据要求
        2. 数据挖掘智能体根据要求搜索法律条文数据
        3. 数据分析智能体评估数据，如果不满足要求则提出更精确的要求
        4. 循环步骤2-3直到数据满足要求
        5. 生成最终报告
        
        :param user_requirement: 用户的类案报告需求
        :return: 包含最终报告和辩论历史的字典
        """
        logger.info(f"开始论坛辩论，用户需求: {user_requirement[:50]}...")
        
        # 初始化辩论状态
        debate_state = {
            "round": 0,
            "user_requirement": user_requirement,
            "analysis_requirement": None,  # 数据分析智能体提出的数据要求
            "mining_data": None,  # 数据挖掘智能体返回的数据
            "evaluation_result": None,  # 数据分析智能体对数据的评估
            "debate_history": [],  # 辩论历史记录
            "is_satisfied": False,  # 数据是否满足要求
        }
        
        # 辩论循环
        while debate_state["round"] < self.max_rounds and not debate_state["is_satisfied"]:
            debate_state["round"] += 1
            logger.info(f"开始第 {debate_state['round']} 轮辩论")
            
            # 根据当前状态决定下一步行动
            if debate_state["analysis_requirement"] is None:
                # 第一轮：数据分析智能体分析需求
                logger.info("引导数据分析智能体分析需求")
                analysis_result = self._analyze_requirement(user_requirement)
                debate_state["analysis_requirement"] = analysis_result
                debate_state["debate_history"].append({
                    "round": debate_state["round"],
                    "agent": "DataAnalysisAgent",
                    "action": "analyze_requirement",
                    "content": analysis_result
                })
            
            elif debate_state["mining_data"] is None:
                # 第二轮：数据挖掘智能体搜索数据
                logger.info("引导数据挖掘智能体搜索数据")
                search_query = self._build_search_query(debate_state["analysis_requirement"])
                mining_result = self._search_data(search_query)
                debate_state["mining_data"] = mining_result
                debate_state["debate_history"].append({
                    "round": debate_state["round"],
                    "agent": "DataMiningAgent",
                    "action": "search_data",
                    "content": mining_result
                })
            
            else:
                # 后续轮次：数据分析智能体评估数据
                logger.info("引导数据分析智能体评估数据")
                evaluation = self._evaluate_data(
                    debate_state["mining_data"],
                    debate_state["analysis_requirement"]
                )
                debate_state["evaluation_result"] = evaluation
                debate_state["debate_history"].append({
                    "round": debate_state["round"],
                    "agent": "DataAnalysisAgent",
                    "action": "evaluate_data",
                    "content": evaluation
                })
                
                # 检查是否满足要求
                if evaluation.get("satisfied", False):
                    debate_state["is_satisfied"] = True
                    logger.info("数据已满足要求")
                    break
                else:
                    # 更新数据要求，准备下一轮
                    refined_requirement = evaluation.get("refined_requirement")
                    if refined_requirement:
                        debate_state["analysis_requirement"] = refined_requirement
                    # 清空当前数据，准备重新搜索
                    debate_state["mining_data"] = None
                    logger.info("数据不满足要求，继续辩论")
        
        # 生成最终报告
        logger.info("辩论完成，生成最终报告")
        final_report = self._generate_final_report(debate_state)
        
        return {
            "report": final_report,
            "debate_history": debate_state["debate_history"],
            "total_rounds": debate_state["round"],
            "final_data": debate_state["mining_data"],
            "analysis_result": debate_state["evaluation_result"],
        }
    
    def _analyze_requirement(self, user_requirement: str) -> Dict[str, Any]:
        """
        引导数据分析智能体分析需求。
        
        :param user_requirement: 用户需求
        :return: 分析结果，包含数据要求
        """
        try:
            # 使用数据分析智能体的需求解析功能
            requirement = self.analysis_agent.NL_parse_requirement(user_requirement)
            
            # 转换为数据要求格式
            data_requirement = {
                "requirement_analysis": requirement,
                "data_needs": {
                    "law_types": requirement.get("law_references", []),
                    "case_types": requirement.get("case_type"),
                    "key_facts": requirement.get("key_facts", []),
                    "dispute_focus": requirement.get("dispute_focus"),
                },
                "search_query": self._build_search_query(requirement)
            }
            
            return data_requirement
        except Exception as e:
            logger.error(f"分析需求失败: {e}")
            return {
                "requirement_analysis": {"error": str(e)},
                "data_needs": {},
                "search_query": user_requirement
            }
    
    def _build_search_query(self, requirement: Dict[str, Any]) -> str:
        """
        根据需求构建搜索查询。
        
        优化：优先识别罪名、关键法律概念等核心要素，构建精确的搜索查询。
        
        :param requirement: 需求字典
        :return: 搜索查询字符串
        """
        # 优先提取核心要素
        core_elements = []
        
        # 1. 争议焦点（通常包含罪名或关键法律概念）
        dispute_focus = requirement.get("dispute_focus", "")
        if dispute_focus:
            core_elements.append(dispute_focus)
        
        # 2. 关键事实（可能包含罪名或法律概念）
        key_facts = requirement.get("key_facts", [])
        if key_facts:
            # 提取可能包含罪名或法律概念的关键词
            for fact in key_facts:
                if any(keyword in fact for keyword in ["罪", "罪", "违约", "侵权", "解除", "赔偿"]):
                    core_elements.append(fact)
        
        # 3. 案件类型（帮助确定法律领域）
        case_type = requirement.get("case_type", "")
        
        # 4. 法律引用（如果用户已经提到了具体法条）
        law_refs = requirement.get("law_references", [])
        if isinstance(law_refs, list) and len(law_refs) > 0:
            for ref in law_refs:
                if isinstance(ref, dict):
                    law_name = ref.get("law", "")
                    article = ref.get("article", "")
                    if law_name and article:
                        core_elements.append(f"{law_name}第{article}条")
        
        # 构建查询：优先使用核心要素
        if core_elements:
            query = "；".join(core_elements)
            # 如果案件类型有助于理解，可以添加
            if case_type and case_type not in query:
                query = f"{case_type}案件：{query}"
            return query
        elif case_type:
            return f"{case_type}案件相关法律条文"
        else:
            return "法律条文搜索"
    
    def _search_data(self, search_query: str) -> Dict[str, Any]:
        """
        引导数据挖掘智能体搜索数据。
        
        :param search_query: 搜索查询
        :return: 搜索到的法律条文数据
        """
        try:
            # 使用数据挖掘智能体的搜索功能
            if isinstance(search_query, dict):
                query_str = search_query.get("search_query", str(search_query))
            else:
                query_str = str(search_query)
            
            law_data = self.mining_agent.search_laws_by_prompt(query_str)
            
            # 获取数据概括
            summary = self.mining_agent.summarize_found_data(law_data)
            
            return {
                "law_data": law_data,
                "summary": summary
            }
        except Exception as e:
            logger.error(f"搜索数据失败: {e}")
            return {
                "law_data": {"laws": [], "total_count": 0},
                "summary": {"error": str(e)}
            }
    
    def _evaluate_data(
        self,
        mining_data: Dict[str, Any],
        analysis_requirement: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        引导数据分析智能体评估数据。
        
        :param mining_data: 数据挖掘智能体返回的数据
        :param analysis_requirement: 数据分析智能体的要求
        :return: 评估结果
        """
        try:
            law_data = mining_data.get("law_data", {})
            laws = law_data.get("laws", [])
            
            # 简单的评估逻辑：检查是否有相关法律条文
            satisfied = len(laws) > 0
            
            # 如果数据不满足要求，生成更精确的要求
            refined_requirement = None
            if not satisfied and analysis_requirement:
                refined_requirement = analysis_requirement.copy()
                refined_requirement["refinement_note"] = "需要更精确的搜索条件，请提供更具体的法律领域或条文关键词"
            
            return {
                "satisfied": satisfied,
                "data_quality": "good" if len(laws) >= 3 else "needs_improvement",
                "laws_count": len(laws),
                "evaluation": f"找到 {len(laws)} 条相关法律条文",
                "refined_requirement": refined_requirement
            }
        except Exception as e:
            logger.error(f"评估数据失败: {e}")
            return {
                "satisfied": False,
                "data_quality": "error",
                "error": str(e)
            }
    
    def _generate_final_report(self, debate_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成最终报告。
        
        :param debate_state: 辩论状态
        :return: 最终报告
        """
        logger.info("生成最终报告")
        
        law_data = debate_state.get("mining_data", {}).get("law_data", {})
        summary = debate_state.get("mining_data", {}).get("summary", {})
        evaluation = debate_state.get("evaluation_result", {})
        
        # 使用主持人模型生成报告
        debate_history_str = json.dumps(debate_state["debate_history"], ensure_ascii=False, indent=2)
        final_data_str = json.dumps(law_data, ensure_ascii=False, indent=2)
        analysis_result_str = json.dumps(evaluation, ensure_ascii=False, indent=2)
        
        messages = DEBATE_SUMMARY_PROMPT.to_messages(
            user_input="",
            user_requirement=debate_state["user_requirement"],
            debate_history=debate_history_str,
            final_data=final_data_str,
            analysis_result=analysis_result_str
        )
        
        try:
            response = self.reasoning_model.invoke(messages)
            response_text = response.content
            
            # 提取 JSON
            json_text = self._extract_json_from_response(response_text)
            report = json.loads(json_text)
            
            return report
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            # 返回基础报告
            return {
                "report": {
                    "title": "法律类案报告",
                    "requirement_summary": debate_state["user_requirement"],
                    "relevant_laws": law_data.get("laws", []),
                    "data_analysis": analysis_result_str,
                    "comprehensive_analysis": "基于找到的法律条文进行分析",
                    "recommendations": "请参考相关法律条文"
                },
                "summary": f"找到 {law_data.get('total_count', 0)} 条相关法律条文"
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


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == "__main__":
    """
    运行测试
    
    使用方法：
        python forum/agent.py
    """
    import os
    from unittest.mock import Mock, patch
    
    print("=" * 70)
    print("ForumAgent 功能测试")
    print("=" * 70)
    
    # 测试 1: 初始化
    print("\n[测试 1] ForumAgent 初始化...")
    try:
        with patch('forum.agent.get_chat_model') as mock_chat, \
             patch('forum.agent.get_reasoning_model') as mock_reasoning, \
             patch('forum.agent.DataAnalysisAgent') as mock_analysis, \
             patch('forum.agent.DataMiningAgent') as mock_mining:
            
            mock_chat.return_value = Mock()
            mock_reasoning.return_value = Mock()
            
            mock_analysis_instance = Mock()
            mock_analysis_instance.name = "DataAnalysisAgent"
            mock_analysis.return_value = mock_analysis_instance
            
            mock_mining_instance = Mock()
            mock_mining_instance.name = "DataMiningAgent"
            mock_mining.return_value = mock_mining_instance
            
            agent = ForumAgent(max_rounds=5)
            assert agent.name == "ForumAgent"
            assert agent.max_rounds == 5
            assert agent.analysis_agent.name == "DataAnalysisAgent"
            assert agent.mining_agent.name == "DataMiningAgent"
            print("✅ 初始化测试通过")
    except Exception as e:
        print(f"❌ 初始化测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 2: 构建搜索查询
    print("\n[测试 2] 构建搜索查询...")
    try:
        with patch('forum.agent.get_chat_model') as mock_chat, \
             patch('forum.agent.get_reasoning_model') as mock_reasoning, \
             patch('forum.agent.DataAnalysisAgent') as mock_analysis, \
             patch('forum.agent.DataMiningAgent') as mock_mining:
            
            mock_chat.return_value = Mock()
            mock_reasoning.return_value = Mock()
            
            mock_analysis_instance = Mock()
            mock_analysis_instance.name = "DataAnalysisAgent"
            mock_analysis.return_value = mock_analysis_instance
            
            mock_mining_instance = Mock()
            mock_mining_instance.name = "DataMiningAgent"
            mock_mining.return_value = mock_mining_instance
            
            agent = ForumAgent()
            
            requirement = {
                "dispute_focus": "合同违约",
                "case_type": "民事",
                "key_facts": ["合同", "违约"],
                "law_references": [{"law": "民法典", "article": "第五百七十七条"}]
            }
            
            query = agent._build_search_query(requirement)
            assert isinstance(query, str)
            assert "合同违约" in query
            assert "民事" in query
            print(f"✅ 构建搜索查询测试通过: {query[:60]}...")
    except Exception as e:
        print(f"❌ 构建搜索查询测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 3: 提取 JSON 响应
    print("\n[测试 3] 提取 JSON 响应...")
    try:
        with patch('forum.agent.get_chat_model') as mock_chat, \
             patch('forum.agent.get_reasoning_model') as mock_reasoning, \
             patch('forum.agent.DataAnalysisAgent') as mock_analysis, \
             patch('forum.agent.DataMiningAgent') as mock_mining:
            
            mock_chat.return_value = Mock()
            mock_reasoning.return_value = Mock()
            
            mock_analysis_instance = Mock()
            mock_analysis_instance.name = "DataAnalysisAgent"
            mock_analysis.return_value = mock_analysis_instance
            
            mock_mining_instance = Mock()
            mock_mining_instance.name = "DataMiningAgent"
            mock_mining.return_value = mock_mining_instance
            
            agent = ForumAgent()
            
            # 测试包含 ```json 代码块
            response1 = '```json\n{"key": "value"}\n```'
            result1 = agent._extract_json_from_response(response1)
            assert result1 == '{"key": "value"}'
            
            # 测试包含普通代码块
            response2 = '```\n{"key": "value"}\n```'
            result2 = agent._extract_json_from_response(response2)
            assert result2 == '{"key": "value"}'
            
            # 测试纯 JSON
            response3 = '{"key": "value"}'
            result3 = agent._extract_json_from_response(response3)
            assert result3 == '{"key": "value"}'
            
            print("✅ 提取 JSON 响应测试通过")
    except Exception as e:
        print(f"❌ 提取 JSON 响应测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 4: 分析需求
    print("\n[测试 4] 分析需求...")
    try:
        with patch('forum.agent.get_chat_model') as mock_chat, \
             patch('forum.agent.get_reasoning_model') as mock_reasoning, \
             patch('forum.agent.DataAnalysisAgent') as mock_analysis, \
             patch('forum.agent.DataMiningAgent') as mock_mining:
            
            mock_chat.return_value = Mock()
            mock_reasoning.return_value = Mock()
            
            mock_analysis_instance = Mock()
            mock_analysis_instance.name = "DataAnalysisAgent"
            mock_analysis_instance.NL_parse_requirement = Mock(return_value={
                "case_type": "民事",
                "dispute_focus": "合同违约",
                "key_facts": ["合同", "违约"],
                "law_references": []
            })
            mock_analysis.return_value = mock_analysis_instance
            
            mock_mining_instance = Mock()
            mock_mining_instance.name = "DataMiningAgent"
            mock_mining.return_value = mock_mining_instance
            
            agent = ForumAgent()
            
            result = agent._analyze_requirement("我需要关于合同违约的法律条文")
            assert isinstance(result, dict)
            assert "requirement_analysis" in result
            assert "data_needs" in result
            assert "search_query" in result
            print("✅ 分析需求测试通过")
    except Exception as e:
        print(f"❌ 分析需求测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 5: 搜索数据
    print("\n[测试 5] 搜索数据...")
    try:
        with patch('forum.agent.get_chat_model') as mock_chat, \
             patch('forum.agent.get_reasoning_model') as mock_reasoning, \
             patch('forum.agent.DataAnalysisAgent') as mock_analysis, \
             patch('forum.agent.DataMiningAgent') as mock_mining:
            
            mock_chat.return_value = Mock()
            mock_reasoning.return_value = Mock()
            
            mock_analysis_instance = Mock()
            mock_analysis_instance.name = "DataAnalysisAgent"
            mock_analysis.return_value = mock_analysis_instance
            
            mock_mining_instance = Mock()
            mock_mining_instance.name = "DataMiningAgent"
            mock_mining_instance.search_laws_by_prompt = Mock(return_value={
                "laws": [{"law_name": "民法典", "article_number": "第五百七十七条"}],
                "total_count": 1
            })
            mock_mining_instance.summarize_found_data = Mock(return_value={
                "summary": {"total_laws": 1},
                "insights": "找到法律条文"
            })
            mock_mining.return_value = mock_mining_instance
            
            agent = ForumAgent()
            
            result = agent._search_data("合同违约")
            assert isinstance(result, dict)
            assert "law_data" in result
            assert "summary" in result
            print("✅ 搜索数据测试通过")
    except Exception as e:
        print(f"❌ 搜索数据测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 6: 评估数据
    print("\n[测试 6] 评估数据...")
    try:
        with patch('forum.agent.get_chat_model') as mock_chat, \
             patch('forum.agent.get_reasoning_model') as mock_reasoning, \
             patch('forum.agent.DataAnalysisAgent') as mock_analysis, \
             patch('forum.agent.DataMiningAgent') as mock_mining:
            
            mock_chat.return_value = Mock()
            mock_reasoning.return_value = Mock()
            
            mock_analysis_instance = Mock()
            mock_analysis_instance.name = "DataAnalysisAgent"
            mock_analysis.return_value = mock_analysis_instance
            
            mock_mining_instance = Mock()
            mock_mining_instance.name = "DataMiningAgent"
            mock_mining.return_value = mock_mining_instance
            
            agent = ForumAgent()
            
            mining_data = {
                "law_data": {
                    "laws": [{"law_name": "民法典", "article_number": "第五百七十七条"}],
                    "total_count": 1
                },
                "summary": {}
            }
            
            result = agent._evaluate_data(mining_data, {"data_needs": {}})
            assert isinstance(result, dict)
            assert "satisfied" in result
            assert "data_quality" in result
            assert "laws_count" in result
            print("✅ 评估数据测试通过")
    except Exception as e:
        print(f"❌ 评估数据测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 7: API 可用性测试（需要真实环境变量）
    print("\n[测试 7] API 可用性测试...")
    try:
        # 检查环境变量
        qwen_key = os.getenv("QWEN_API_KEY")
        qwen_url = os.getenv("QWEN_BASE_URL")
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        deepseek_url = os.getenv("DEEPSEEK_BASE_URL")
        
        if not qwen_key or not qwen_url:
            print("⚠️  跳过 API 测试：QWEN_API_KEY 或 QWEN_BASE_URL 未设置")
        elif not deepseek_key or not deepseek_url:
            print("⚠️  跳过 API 测试：DEEPSEEK_API_KEY 或 DEEPSEEK_BASE_URL 未设置")
        else:
            print("正在测试 API 连接...")
            
            # 测试千问 API
            try:
                from forum.llm import get_chat_model
                qwen_model = get_chat_model(model_name="qwen-turbo", temperature=0.1)
                test_response = qwen_model.invoke([{"role": "user", "content": "你好"}])
                if test_response and test_response.content:
                    print("✅ 千问 API 连接成功")
                else:
                    print("⚠️  千问 API 响应为空")
            except Exception as e:
                print(f"❌ 千问 API 连接失败: {e}")
            
            # 测试 DeepSeek API（通过已导入的智能体）
            try:
                # 使用已初始化的智能体的模型来测试
                agent = ForumAgent()
                deepseek_model = agent.mining_agent.chat_model
                test_response = deepseek_model.invoke([{"role": "user", "content": "你好"}])
                if test_response and test_response.content:
                    print("✅ DeepSeek API 连接成功")
                else:
                    print("⚠️  DeepSeek API 响应为空")
            except Exception as e:
                print(f"❌ DeepSeek API 连接失败: {e}")
            
            # 测试完整的辩论流程（简短版本）
            print("\n正在测试完整辩论流程（简短版本）...")
            try:
                agent = ForumAgent(max_rounds=2)
                user_requirement = "关于违法解除劳动合同的赔偿标准"
                result = agent.conduct_debate(user_requirement)
                
                assert isinstance(result, dict)
                assert "report" in result
                assert "debate_history" in result
                assert "total_rounds" in result
                assert result["total_rounds"] > 0
                
                laws_count = len(result.get('final_data', {}).get('law_data', {}).get('laws', []))
                print(f"✅ 完整辩论流程测试通过（共 {result['total_rounds']} 轮）")
                print(f"   找到 {laws_count} 条法律条文")
                if result.get("report"):
                    report = result["report"]
                    if isinstance(report, dict) and "report" in report:
                        print(f"   报告标题: {report['report'].get('title', 'N/A')}")
            except Exception as e:
                print(f"❌ 完整辩论流程测试失败: {e}")
                import traceback
                traceback.print_exc()
    except Exception as e:
        print(f"❌ API 可用性测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
