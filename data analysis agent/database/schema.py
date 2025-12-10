"""
数据库结构信息查询模块。

提供获取数据库表结构、字段信息、索引等功能。
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from loguru import logger
from .connection import DatabaseConnection


@dataclass
class ColumnInfo:
    """字段信息。"""
    name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    comment: Optional[str] = None


@dataclass
class TableInfo:
    """表信息。"""
    name: str
    columns: List[ColumnInfo]
    primary_keys: List[str]
    indexes: List[Dict[str, Any]]
    comment: Optional[str] = None


class SchemaInspector:
    """
    数据库结构检查器。
    
    用于获取数据库的表结构、字段信息等。
    """
    
    def __init__(self, connection: DatabaseConnection):
        """
        初始化结构检查器。
        
        :param connection: 数据库连接对象
        """
        self.connection = connection
    
    def get_all_tables(self, database: Optional[str] = None) -> List[str]:
        """
        获取所有表名。
        
        :param database: 数据库名，如果为 None 则使用连接配置的数据库
        :return: 表名列表
        """
        if database is None:
            database = self.connection.config.database
        
        logger.debug(f"获取数据库 {database} 中的所有表")
        
        query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """
        
        result = self.connection.execute_query(query, (database,), fetch="all")
        tables = [row["TABLE_NAME"] for row in result]
        
        logger.debug(f"找到 {len(tables)} 个表: {tables}")
        return tables
    
    def get_table_schema(self, table_name: str, database: Optional[str] = None) -> TableInfo:
        """
        获取指定表的结构信息。
        
        :param table_name: 表名
        :param database: 数据库名
        :return: 表结构信息
        """
        if database is None:
            database = self.connection.config.database
        
        logger.debug(f"获取表 {table_name} 的完整结构信息")
        
        # 获取表注释
        table_comment = None
        query_comment = """
            SELECT TABLE_COMMENT
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = %s
        """
        result = self.connection.execute_query(query_comment, (database, table_name), fetch="one")
        if result:
            table_comment = result["TABLE_COMMENT"] or None
        
        # 获取所有信息
        columns = self.get_columns(table_name, database)
        primary_keys = self.get_primary_keys(table_name, database)
        indexes = self.get_indexes(table_name, database)
        
        table_info = TableInfo(
            name=table_name,
            columns=columns,
            primary_keys=primary_keys,
            indexes=indexes,
            comment=table_comment
        )
        
        logger.debug(f"成功获取表 {table_name} 的结构信息: {len(columns)} 个字段, {len(primary_keys)} 个主键, {len(indexes)} 个索引")
        return table_info
    
    def get_columns(self, table_name: str, database: Optional[str] = None) -> List[ColumnInfo]:
        """
        获取指定表的所有字段信息。
        
        :param table_name: 表名
        :param database: 数据库名
        :return: 字段信息列表
        """
        if database is None:
            database = self.connection.config.database
        
        logger.debug(f"获取表 {table_name} 的字段信息")
        
        query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COLUMN_COMMENT,
                COLUMN_KEY
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """
        
        result = self.connection.execute_query(query, (database, table_name), fetch="all")
        
        # 获取主键字段列表
        primary_keys = self.get_primary_keys(table_name, database)
        
        # 获取外键字段列表
        foreign_keys_info = self.get_foreign_keys(table_name, database)
        foreign_key_columns = {fk["column_name"] for fk in foreign_keys_info}
        
        columns = []
        for row in result:
            column = ColumnInfo(
                name=row["COLUMN_NAME"],
                data_type=row["DATA_TYPE"],
                is_nullable=row["IS_NULLABLE"] == "YES",
                default_value=row["COLUMN_DEFAULT"],
                is_primary_key=row["COLUMN_NAME"] in primary_keys,
                is_foreign_key=row["COLUMN_NAME"] in foreign_key_columns,
                comment=row["COLUMN_COMMENT"] or None
            )
            columns.append(column)
        
        logger.debug(f"表 {table_name} 共有 {len(columns)} 个字段")
        return columns
    
    def get_primary_keys(self, table_name: str, database: Optional[str] = None) -> List[str]:
        """
        获取表的主键字段名。
        
        :param table_name: 表名
        :param database: 数据库名
        :return: 主键字段名列表
        """
        if database is None:
            database = self.connection.config.database
        
        logger.debug(f"获取表 {table_name} 的主键字段")
        
        query = """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = %s
            AND CONSTRAINT_NAME = 'PRIMARY'
            ORDER BY ORDINAL_POSITION
        """
        
        result = self.connection.execute_query(query, (database, table_name), fetch="all")
        primary_keys = [row["COLUMN_NAME"] for row in result]
        
        logger.debug(f"表 {table_name} 的主键字段: {primary_keys}")
        return primary_keys
    
    def get_foreign_keys(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取表的外键信息。
        
        :param table_name: 表名
        :param database: 数据库名
        :return: 外键信息列表，每个元素包含字段名、引用表、引用字段等
        """
        if database is None:
            database = self.connection.config.database
        
        logger.debug(f"获取表 {table_name} 的外键信息")
        
        query = """
            SELECT 
                kcu.COLUMN_NAME,
                kcu.REFERENCED_TABLE_NAME,
                kcu.REFERENCED_COLUMN_NAME,
                kcu.CONSTRAINT_NAME,
                rc.UPDATE_RULE,
                rc.DELETE_RULE
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            INNER JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
                ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
                AND kcu.TABLE_SCHEMA = rc.CONSTRAINT_SCHEMA
            WHERE kcu.TABLE_SCHEMA = %s
            AND kcu.TABLE_NAME = %s
            AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY kcu.ORDINAL_POSITION
        """
        
        result = self.connection.execute_query(query, (database, table_name), fetch="all")
        
        foreign_keys = []
        for row in result:
            fk_info = {
                "column_name": row["COLUMN_NAME"],
                "referenced_table": row["REFERENCED_TABLE_NAME"],
                "referenced_column": row["REFERENCED_COLUMN_NAME"],
                "constraint_name": row["CONSTRAINT_NAME"],
                "update_rule": row["UPDATE_RULE"],
                "delete_rule": row["DELETE_RULE"]
            }
            foreign_keys.append(fk_info)
        
        logger.debug(f"表 {table_name} 共有 {len(foreign_keys)} 个外键")
        return foreign_keys
    
    def get_indexes(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取表的索引信息。
        
        :param table_name: 表名
        :param database: 数据库名
        :return: 索引信息列表
        """
        if database is None:
            database = self.connection.config.database
        
        logger.debug(f"获取表 {table_name} 的索引信息")
        
        query = """
            SELECT 
                INDEX_NAME,
                COLUMN_NAME,
                SEQ_IN_INDEX,
                NON_UNIQUE,
                INDEX_TYPE,
                INDEX_COMMENT
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = %s
            AND INDEX_NAME != 'PRIMARY'
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """
        
        result = self.connection.execute_query(query, (database, table_name), fetch="all")
        
        # 将索引信息按索引名分组
        indexes_dict: Dict[str, Dict[str, Any]] = {}
        for row in result:
            index_name = row["INDEX_NAME"]
            if index_name not in indexes_dict:
                indexes_dict[index_name] = {
                    "name": index_name,
                    "columns": [],
                    "is_unique": row["NON_UNIQUE"] == 0,
                    "type": row["INDEX_TYPE"],
                    "comment": row["INDEX_COMMENT"] or None
                }
            indexes_dict[index_name]["columns"].append(row["COLUMN_NAME"])
        
        indexes = list(indexes_dict.values())
        
        logger.debug(f"表 {table_name} 共有 {len(indexes)} 个索引（不包括主键）")
        return indexes


def get_all_tables(connection: DatabaseConnection, database: Optional[str] = None) -> List[str]:
    """
    获取所有表名的便捷函数。
    
    :param connection: 数据库连接
    :param database: 数据库名
    :return: 表名列表
    """
    inspector = SchemaInspector(connection)
    return inspector.get_all_tables(database)


def get_table_schema(
    connection: DatabaseConnection,
    table_name: str,
    database: Optional[str] = None
) -> TableInfo:
    """
    获取表结构的便捷函数。
    
    :param connection: 数据库连接
    :param table_name: 表名
    :param database: 数据库名
    :return: 表结构信息
    """
    inspector = SchemaInspector(connection)
    return inspector.get_table_schema(table_name, database)

