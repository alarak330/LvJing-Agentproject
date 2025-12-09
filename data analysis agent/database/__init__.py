"""
数据库交互模块。

提供与 MySQL 数据库的连接、结构查询、SQL 构建等功能。
"""

from .connection import (
    DatabaseConnection,
    DatabaseConfig,
    ConnectionPool,
    PooledConnection,
    get_connection,
    get_connection_pool,
    get_db_context,
)

from .schema import (
    SchemaInspector,
    get_table_schema,
    get_all_tables,
)

from .query_builder import (
    QueryBuilder,
    build_select_query,
    build_where_clause,
)

__all__ = [
    # 连接管理
    "DatabaseConnection",
    "DatabaseConfig",
    "ConnectionPool",
    "PooledConnection",
    "get_connection",
    "get_connection_pool",
    "get_db_context",
    # Schema 查询
    "SchemaInspector",
    "get_table_schema",
    "get_all_tables",
    # 查询构建
    "QueryBuilder",
    "build_select_query",
    "build_where_clause",
]

