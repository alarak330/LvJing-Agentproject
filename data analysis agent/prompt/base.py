"""
基础提示词模板系统。

提供 PromptTemplate 类，支持模板变量替换、Few-shot 示例、系统角色定义，
以及与 LangChain 消息格式的转换。
"""

from __future__ import annotations

from typing import List, Any, Optional, Tuple
from dataclasses import dataclass, field

from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage


@dataclass
class PromptTemplate:
    """
    提示词模板类。
    
    支持模板变量替换、Few-shot 示例管理、系统角色定义，
    以及转换为 LangChain 消息格式。
    """
    
    template: str   # 提示词模板字符串，支持 {variable_name} 格式的变量。
    system_role: Optional[str] = None
    examples: List[Tuple[str, str]] = field(default_factory=list)   #Few-shot 示例列表，每个示例是 (input, output) 元组。
    name: Optional[str] = None  # 模板名称，用于日志记录。
    
    def format(self, **kwargs: Any) -> str:
        """
        替换模板中的变量。
        
        :param kwargs: 模板变量及其值
        :return: 格式化后的提示词字符串
        """
        try:
            formatted = self.template.format(**kwargs)
            logger.debug(f"格式化提示词模板 '{self.name or 'unnamed'}': 替换了 {len(kwargs)} 个变量")
            return formatted
        except KeyError as e:
            logger.error(f"提示词模板缺少必需的变量: {e}")
            raise ValueError(f"模板缺少必需的变量: {e}") from e
        except Exception as e:
            logger.error(f"格式化提示词模板时出错: {e}")
            raise
    
    def add_example(self, input_text: str, output_text: str) -> None:
        """
        添加 Few-shot 示例。
        
        :param input_text: 示例输入
        :param output_text: 示例输出
        """
        self.examples.append((input_text, output_text))
        logger.debug(f"为提示词模板 '{self.name or 'unnamed'}' 添加示例: 输入长度={len(input_text)}, 输出长度={len(output_text)}")
    
    def set_system_role(self, role: str) -> None:
        """
        设置系统角色。
        一般不使用这个函数，因为目前是做法律分析智能体，功能职责单一不需要频繁创建智能体
        :param role: 系统角色描述
        """
        self.system_role = role
        logger.debug(f"为提示词模板 '{self.name or 'unnamed'}' 设置系统角色")

    
    def to_messages(
        self,
        user_input: str,
        include_examples: bool = True,
        **kwargs: Any
    ) -> List[BaseMessage]:
        """
        将提示词转换为 LangChain 消息列表。
        
        :param user_input: 用户输入
        :param include_examples: 是否包含 Few-shot 示例
        :param kwargs: 模板变量及其值
        :return: LangChain 消息列表
        """
        messages: List[BaseMessage] = []
        
        # 添加系统消息（如果定义了系统角色）
        if self.system_role:
            system_content = self.system_role
            # 如果模板中有变量，也需要格式化系统角色
            try:
                system_content = system_content.format(**kwargs)
            except (KeyError, ValueError):
                # 如果系统角色中没有变量或格式化失败，使用原始内容
                pass
            messages.append(SystemMessage(content=system_content))
            logger.debug(f"添加系统消息: 角色已定义")
        
        # 添加 Few-shot 示例
        if include_examples and self.examples:
            for example_input, example_output in self.examples:
                messages.append(HumanMessage(content=example_input))
                messages.append(AIMessage(content=example_output))
            logger.debug(f"添加 {len(self.examples)} 个 Few-shot 示例")
        
        # 格式化用户提示词并添加
        try:
            formatted_prompt = self.format(**kwargs)
            # 将用户输入和格式化后的提示词组合
            if user_input:
                user_content = f"{formatted_prompt}\n\n用户输入: {user_input}"
            else:
                user_content = formatted_prompt
            messages.append(HumanMessage(content=user_content))
            logger.debug(f"添加用户消息: 提示词已格式化")
        except Exception as e:
            logger.error(f"格式化提示词时出错: {e}")
            raise
        
        logger.debug(f"成功将提示词模板转换为 {len(messages)} 条消息")
        return messages



def create_prompt_template(
    template: str,
    name: Optional[str] = None,
    system_role: Optional[str] = None,
    examples: Optional[List[Tuple[str, str]]] = None
) -> PromptTemplate:
    """
    创建提示词模板的便捷函数。
    
    :param template: 提示词模板字符串
    :param name: 模板名称
    :param examples: Few-shot 示例列表
    :return: PromptTemplate 实例
    """
    prompt = PromptTemplate(
        template=template,
        system_role=system_role,
        name=name,
        examples=examples or []
    )
    return prompt