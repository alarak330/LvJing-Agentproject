"""
MySQL connection manager utilities.

提供一个上下文管理器 'MySQLConnectionManager' 和简单的 'execute' helper
用于执行查询并支持字典游标返回。
"""
from dataclasses import dataclass
from typing import Optional, Any, Tuple, List
import mysql.connector
from mysql.connector import Error

@dataclass
class DBConfig:
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: Optional[str] = None
    charset: str = "utf8mb4"

class MySQLConnectionManager:
    """上下文管理器，维护单一连接并提供 execute 辅助方法。

    example:
        cfg = DBConfig(user='me', password='pw', database='mydb')
        with MySQLConnectionManager(cfg) as db:
            rows = db.execute('SELECT * FROM users WHERE id=%s', (1,))
    """

    def __init__(self, config: DBConfig, autocommit: bool = False):
        self.config = config
        self.autocommit = autocommit
        self.conn: Optional[mysql.connector.connection_cext.CMySQLConnection] = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self) -> None:
        if self.conn and self.conn.is_connected():
            return
        try:
            self.conn = mysql.connector.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                charset=self.config.charset,
                use_pure=True,
            )
            self.conn.autocommit = self.autocommit
        except Error as e:
            raise ConnectionError(f"Failed to connect to MySQL: {e}")

    def close(self) -> None:
        try:
            if self.conn and self.conn.is_connected():
                self.conn.close()
        finally:
            self.conn = None

    def execute(self, query: str, params: Optional[Tuple[Any, ...]] = None, fetch: str = "all") -> Any:
        """执行 SQL 并返回结果。

        fetch 参数：'all' 返回所有行列表，'one' 返回单行，其他任意值则提交并返回受影响行数。
        返回结果为列表字典（cursor 设置 dictionary=True）。
        """
        if not self.conn or not self.conn.is_connected():
            self.connect()

        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            if fetch == "all":
                return cursor.fetchall()
            if fetch == "one":
                return cursor.fetchone()
            # commit for non-fetch operations
            self.conn.commit()
            return cursor.rowcount
        finally:
            cursor.close()


