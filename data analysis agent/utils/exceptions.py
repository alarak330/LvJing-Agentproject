"""
自定义异常类定义。

定义项目特定的异常类，便于错误处理和调试。
"""

from __future__ import annotations


class LegalDataError(Exception):
    """法律数据错误基类。"""
    
    def __init__(self, message: str, data: dict | None = None):
        """
        初始化异常。
        
        :param message: 错误消息
        :param data: 相关的数据上下文
        """
        super().__init__(message)
        self.message = message
        self.data = data or {}
    
    def __str__(self) -> str:
        if self.data:
            return f"{self.message} | 数据上下文: {self.data}"
        return self.message


class CaseParseError(LegalDataError):
    """案件解析错误。"""
    
    def __init__(self, message: str, case_text: str | None = None):
        """
        初始化案件解析错误。
        
        :param message: 错误消息
        :param case_text: 无法解析的案件文本
        """
        super().__init__(message, {"case_text": case_text} if case_text else None)
        self.case_text = case_text


class DataValidationError(LegalDataError):
    """数据验证错误。"""
    
    def __init__(self, message: str, field: str | None = None, value: any = None):
        """
        初始化数据验证错误。
        
        :param message: 错误消息
        :param field: 验证失败的字段名
        :param value: 验证失败的值
        """
        data = {}
        if field:
            data["field"] = field
        if value is not None:
            data["value"] = value
        super().__init__(message, data if data else None)
        self.field = field
        self.value = value


class SimilarityCalculationError(LegalDataError):
    """相似度计算错误。"""
    
    def __init__(self, message: str, case1_id: str | None = None, case2_id: str | None = None):
        """
        初始化相似度计算错误。
        
        :param message: 错误消息
        :param case1_id: 第一个案件ID
        :param case2_id: 第二个案件ID
        """
        data = {}
        if case1_id:
            data["case1_id"] = case1_id
        if case2_id:
            data["case2_id"] = case2_id
        super().__init__(message, data if data else None)
        self.case1_id = case1_id
        self.case2_id = case2_id


class StatisticsError(LegalDataError):
    """统计分析错误。"""
    
    def __init__(self, message: str, analysis_type: str | None = None):
        """
        初始化统计分析错误。
        
        :param message: 错误消息
        :param analysis_type: 分析类型
        """
        super().__init__(message, {"analysis_type": analysis_type} if analysis_type else None)
        self.analysis_type = analysis_type


