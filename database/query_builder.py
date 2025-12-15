"""
SQL 查询构建辅助模块。

提供构建 SQL 查询语句的辅助功能。
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from loguru import logger
from .connection import DatabaseConnection


@dataclass
class QueryCondition:
    """查询条件。"""
    field: str
    operator: str  # =, >, <, >=, <=, LIKE, IN, BETWEEN 等
    value: Any
    logic: str = "AND"  # AND 或 OR


class QueryBuilder:
    """
    SQL 查询构建器。
    
    用于辅助构建 SQL 查询语句，特别是 WHERE 子句。
    """
    
    def __init__(self, table_name: str):
        """
        初始化查询构建器。
        
        :param table_name: 表名
        """
        self.table_name = table_name
        self.select_fields: List[str] = ["*"]
        self.where_conditions: List[QueryCondition] = []
        self.order_by: List[Tuple[str, str]] = []  # (field, direction)
        self.limit_value: Optional[int] = None
        self.offset_value: Optional[int] = None
    
    def select(self, fields: List[str]) -> QueryBuilder:
        """
        设置要查询的字段。
        
        :param fields: 字段名列表，如果为空列表则查询所有字段（*）
        :return: 返回自身，支持链式调用
        :raises ValueError: 如果字段列表为空或包含无效字段名
        """
        import re
        
        if not fields:
            logger.warning("字段列表为空，将查询所有字段（*）")
            self.select_fields = ["*"]
            return self
        
        # 验证字段名格式（防止 SQL 注入）
        validated_fields = []
        dangerous_keywords = [';', '--', '/*', '*/', 'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE']
        
        for field in fields:
            if not isinstance(field, str):
                raise ValueError(f"字段名必须是字符串类型，收到: {type(field)}")
            
            field = field.strip()
            if not field:
                continue
            
            # 检查是否包含危险关键字
            field_upper = field.upper()
            if any(keyword in field_upper for keyword in dangerous_keywords):
                raise ValueError(f"字段名 '{field}' 包含不安全的 SQL 关键字")
            
            # 验证字段名格式：允许字母、数字、下划线、点号（用于表别名）
            # 允许常见的 SQL 函数：COUNT(*), SUM(field) 等
            field_pattern = r'^[a-zA-Z_][a-zA-Z0-9_.]*$|^\*$|^[a-zA-Z_][a-zA-Z0-9_.]*\([^)]*\)$'
            if re.match(field_pattern, field) or field in ['*', 'COUNT(*)', 'SUM(*)', 'AVG(*)', 'MAX(*)', 'MIN(*)']:
                validated_fields.append(field)
            else:
                # 对于复杂表达式，记录警告但允许通过（由开发者负责安全性）
                logger.warning(f"字段名 '{field}' 格式不标准，请确保正确且安全")
                validated_fields.append(field)
        
        if not validated_fields:
            logger.warning("所有字段名都无效，将查询所有字段（*）")
            self.select_fields = ["*"]
        else:
            self.select_fields = validated_fields
            logger.debug(f"设置查询字段: {validated_fields}")
        
        return self
    
    def where(self, field: str, operator: str, value: Any, logic: str = "AND") -> QueryBuilder:
        """
        添加 WHERE 条件。
        
        :param field: 字段名
        :param operator: 操作符（=, >, <, >=, <=, LIKE, IN, BETWEEN, IS NULL, IS NOT NULL 等）
        :param value: 值
        :param logic: 逻辑连接符（AND 或 OR）
        :return: 返回自身，支持链式调用
        """
        # 验证操作符
        valid_operators = ['=', '>', '<', '>=', '<=', '!=', '<>', 'LIKE', 'IN', 'NOT IN', 
                          'BETWEEN', 'IS NULL', 'IS NOT NULL']
        operator_upper = operator.upper().strip()
        if operator_upper not in valid_operators:
            logger.warning(f"操作符 '{operator}' 不在标准列表中，将直接使用")
        
        # 验证逻辑连接符
        logic_upper = logic.upper().strip()
        if logic_upper not in ['AND', 'OR']:
            raise ValueError(f"逻辑连接符必须是 AND 或 OR，收到的为: {logic}")
        
        # 验证字段名（基本安全检查）
        if not isinstance(field, str) or not field.strip():
            raise ValueError("字段名不能为空")
        
        condition = QueryCondition(field.strip(), operator.upper(), value, logic_upper)
        self.where_conditions.append(condition)
        logger.debug(f"添加 WHERE 条件: {field} {operator} {value} ({logic})")
        return self
    
    def order_by_field(self, field: str, direction: str = "ASC") -> QueryBuilder:
        """
        添加排序字段。
        
        :param field: 字段名
        :param direction: 排序方向（ASC 或 DESC）
        :return: 返回自身，支持链式调用
        """
        if not isinstance(field, str) or not field.strip():
            raise ValueError("排序字段名不能为空")
        
        direction_upper = direction.upper().strip()
        if direction_upper not in ['ASC', 'DESC']:
            raise ValueError(f"排序方向必须是 ASC 或 DESC，收到: {direction}")
        
        self.order_by.append((field.strip(), direction_upper))
        logger.debug(f"添加排序: {field} {direction_upper}")
        return self
    
    def limit(self, count: int, offset: Optional[int] = None) -> QueryBuilder:
        """
        设置 LIMIT 和 OFFSET。
        
        :param count: 限制数量
        :param offset: 偏移量
        :return: 返回自身，支持链式调用
        """
        if not isinstance(count, int) or count < 0:
            raise ValueError(f"LIMIT 数量必须是大于等于 0 的整数，收到: {count}")
        
        if offset is not None and (not isinstance(offset, int) or offset < 0):
            raise ValueError(f"OFFSET 必须是大于等于 0 的整数，收到: {offset}")
        
        self.limit_value = count
        self.offset_value = offset
        logger.debug(f"设置 LIMIT: {count}, OFFSET: {offset}")
        return self
    
    def build(self) -> Tuple[str, Optional[tuple]]:
        """
        构建 SQL 查询语句。
        
        :return: (SQL 语句, 参数元组)
        """
        logger.debug(f"构建查询语句，表名: {self.table_name}")
        
        # 构建 SELECT 子句
        select_clause = ", ".join(self.select_fields)
        
        # 构建 FROM 子句
        from_clause = f"FROM {self.table_name}"
        
        # 构建 WHERE 子句和参数
        where_clause = ""
        params_list = []
        
        if self.where_conditions:
            where_parts, where_params = build_where_clause(self.where_conditions)
            where_clause = f"WHERE {where_parts}"
            params_list.extend(where_params)
        
        # 构建 ORDER BY 子句
        order_by_clause = ""
        if self.order_by:
            order_parts = [f"{field} {direction}" for field, direction in self.order_by]
            order_by_clause = f"ORDER BY {', '.join(order_parts)}"
        
        # 构建 LIMIT 和 OFFSET 子句
        limit_clause = ""
        if self.limit_value is not None:
            if self.offset_value is not None:
                limit_clause = f"LIMIT {self.offset_value}, {self.limit_value}"
            else:
                limit_clause = f"LIMIT {self.limit_value}"
        
        # 组合 SQL 语句
        sql_parts = [
            f"SELECT {select_clause}",
            from_clause
        ]
        
        if where_clause:
            sql_parts.append(where_clause)
        if order_by_clause:
            sql_parts.append(order_by_clause)
        if limit_clause:
            sql_parts.append(limit_clause)
        
        sql = " ".join(sql_parts) + ";"
        params = tuple(params_list) if params_list else None
        
        logger.debug(f"构建的 SQL: {sql}")
        logger.debug(f"参数: {params}")
        
        return sql, params
    
    def execute(self, connection: DatabaseConnection) -> List[Dict[str, Any]]:
        """
        执行构建的查询。
        
        :param connection: 数据库连接
        :return: 查询结果
        """
        query, params = self.build()
        logger.debug(f"执行查询: {query}")
        return connection.execute_query(query, params, fetch="all")


def build_select_query(
    table_name: str,
    fields: Optional[List[str]] = None,
    conditions: Optional[List[QueryCondition]] = None,
    order_by: Optional[List[Tuple[str, str]]] = None,
    limit: Optional[int] = None
) -> Tuple[str, Optional[tuple]]:
    """
    构建 SELECT 查询的便捷函数。
    
    :param table_name: 表名
    :param fields: 字段列表，如果为 None 则查询所有字段
    :param conditions: 查询条件列表
    :param order_by: 排序字段列表
    :param limit: 限制数量
    :return: (SQL 语句, 参数元组)
    """
    builder = QueryBuilder(table_name)
    if fields:
        builder.select(fields)
    if conditions:
        for cond in conditions:
            builder.where(cond.field, cond.operator, cond.value, cond.logic)
    if order_by:
        for field, direction in order_by:
            builder.order_by_field(field, direction)
    if limit:
        builder.limit(limit)
    return builder.build()


def build_where_clause(conditions: List[QueryCondition]) -> Tuple[str, tuple]:
    """
    构建 WHERE 子句。
    
    :param conditions: 条件列表
    :return: (WHERE 子句字符串, 参数元组)
    """
    if not conditions:
        return "", ()
    
    logger.debug(f"构建 WHERE 子句，条件数量: {len(conditions)}")
    
    where_parts = []
    params_list = []
    
    for i, cond in enumerate(conditions):
        field = cond.field
        operator = cond.operator.upper()
        value = cond.value
        logic = cond.logic
        
        # 构建条件片段
        if operator in ['IS NULL', 'IS NOT NULL']:
            # IS NULL 和 IS NOT NULL 不需要参数
            condition_part = f"{field} {operator}"
        elif operator == 'IN':
            # IN 操作符：需要多个参数
            if not isinstance(value, (list, tuple)):
                raise ValueError(f"IN 操作符的值必须是列表或元组，收到: {type(value)}")
            placeholders = ", ".join(["%s"] * len(value))
            condition_part = f"{field} IN ({placeholders})"
            params_list.extend(value)
        elif operator == 'NOT IN':
            # NOT IN 操作符
            if not isinstance(value, (list, tuple)):
                raise ValueError(f"NOT IN 操作符的值必须是列表或元组，收到: {type(value)}")
            placeholders = ", ".join(["%s"] * len(value))
            condition_part = f"{field} NOT IN ({placeholders})"
            params_list.extend(value)
        elif operator == 'BETWEEN':
            # BETWEEN 操作符：需要两个值
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError(f"BETWEEN 操作符的值必须是包含两个元素的列表或元组，收到: {value}")
            condition_part = f"{field} BETWEEN %s AND %s"
            params_list.extend(value)
        elif operator == 'LIKE':
            # LIKE 操作符
            condition_part = f"{field} LIKE %s"
            params_list.append(value)
        else:
            # 标准操作符：=, >, <, >=, <=, !=, <>
            condition_part = f"{field} {operator} %s"
            params_list.append(value)
        
        # 添加逻辑连接符（第一个条件不需要）
        if i == 0:
            where_parts.append(condition_part)
        else:
            where_parts.append(f"{logic} {condition_part}")
    
    where_clause = " ".join(where_parts)
    params = tuple(params_list)
    
    logger.debug(f"WHERE 子句: {where_clause}")
    logger.debug(f"参数: {params}")
    
    return where_clause, params

