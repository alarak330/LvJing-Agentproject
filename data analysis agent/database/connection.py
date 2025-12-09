"""
数据库连接管理模块。

提供数据库连接的创建、管理和配置功能。
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Optional, Dict, Any
from dataclasses import dataclass
import dotenv
from loguru import logger
import os
import mysql.connector
from mysql.connector import pooling, Error


@dataclass
class DatabaseConfig:
    """
    数据库配置类。
    
    包含连接 MySQL 所需的所有配置信息。
    """
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: Optional[str] = None
    charset: str = "utf8mb4"
    # 连接池配置
    pool_size: int = 5  # 连接池大小
    max_overflow: int = 10  # 最大溢出连接数
    pool_timeout: int = 30  # 获取连接超时时间（秒）
    pool_recycle: int = 3600  # 连接回收时间（秒）

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """
        从环境变量加载配置。
        
        需要环境变量(数据库端口默认为3306，不做修改)：
        - MYSQL_HOST
        - MYSQL_USER
        - MYSQL_PASSWORD
        - MYSQL_DATABASE
        - MYSQL_CHARSET
        """
        dotenv.load_dotenv()
        dbconfig = DatabaseConfig()
        dbconfig.host = os.getenv("MYSQL_HOST")
        dbconfig.user = os.getenv("MYSQL_USER")
        dbconfig.password = os.getenv("MYSQL_PASSWORD")
        dbconfig.database = os.getenv("MYSQL_DATABASE")
        dbconfig.charset = os.getenv("MYSQL_CHARSET")

        logger.debug(f" \n MYSQL_HOST: {dbconfig.host}\n"
                     f" MYSQL_USER: {dbconfig.user}\n"
                     f" MYSQL_PASSWORD: {dbconfig.password}\n"
                     f" MYSQL_DATABASE: {dbconfig.database}")
        return dbconfig

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于连接参数。"""

        config_dict = {"host": self.host,
                       "port": self.port,
                       "user": self.user,
                       "password": self.password,
                       "database": self.database,
                       "charset": self.charset}
        logger.debug(f" \nconfig_dict: {config_dict}")
        return config_dict


class DatabaseConnection:
    """
    数据库连接管理类。
    
    提供连接的创建、复用、关闭等功能。
    支持上下文管理器协议。
    """

    def __init__(self, config: DatabaseConfig):
        """
        初始化数据库连接。
        
        :param config: 数据库配置
        """
        self.config = config
        self._connection: Optional[Any] = None  # 实际的数据库连接对象

    def connect(self) -> None:
        """
        建立数据库连接。
        
        :raises ConnectionError: 连接失败时抛出
        """

        if self.is_connected():
            logger.debug("连接已经存在且有效")
            return

        try:
            logger.debug(f"连接MySQL数据库中 {self.config.host}:{self.config.port}")
            self._connection = mysql.connector.connect(**self.config.to_dict())
            logger.info(f"成功连接到MySQL数据库: {self.config.database}")
        except Error as e:
            logger.error(f"连接出错: {e}")
            raise ConnectionError(f"没有连接到MySQL: {e}") from e

    def disconnect(self) -> None:
        """关闭数据库连接。"""
        if self._connection and self.is_connected():
            try:
                self._connection.close()
                logger.debug("关闭MySQL连接")
            except Error as e:
                logger.warning(f"错误连接： {e}")
            finally:
                self._connection = None

    def is_connected(self) -> bool:
        """
        检查连接是否有效。
        
        :return: 连接是否有效
        """
        if self._connection is None:
            return False
        try:
            return self._connection.is_connected()
        except Exception:
            return False

    def execute_query(
            self,
            query: str,
            params: Optional[tuple] = None,
            fetch: str = "all"
    ) -> Any:
        """
        执行 SQL 查询。
        
        :param query: SQL 查询语句
        :param params: 查询参数（用于参数化查询）
        :param fetch: 获取方式，"all" 返回所有行，"one" 返回单行，None 不返回
        :return: 查询结果
        """
        if not self.is_connected():
            self.connect()

        cursor = None
        try:
            logger.debug(f"执行查询: {query}...")
            cursor = self._connection.cursor(dictionary=True)
            cursor.execute(query, params or ())

            if fetch == "all":
                result = cursor.fetchall()
                logger.debug(f"查询返回 {len(result)} 行数据")
                return result
            elif fetch == "one":
                result = cursor.fetchone()
                logger.debug("查询返回 1 行数据")
                return result
            else:
                # 不返回结果，用于执行 DDL 等
                return None
        except Error as e:
            logger.error(f"查询执行失败: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def execute_update(
            self,
            query: str,
            params: Optional[tuple] = None
    ) -> int:
        """
        执行更新操作（INSERT/UPDATE/DELETE）。
        
        :param query: SQL 语句
        :param params: 查询参数
        :return: 受影响的行数
        """
        if not self.is_connected():
            self.connect()

        cursor = None
        try:
            logger.debug(f"执行更新: {query}...")
            cursor = self._connection.cursor()
            cursor.execute(query, params or ())
            affected_rows = cursor.rowcount
            self._connection.commit()
            logger.debug(f"更新影响了 {affected_rows} 行数据")
            return affected_rows
        except Error as e:
            logger.error(f"更新执行失败: {e}")
            if self._connection:
                self._connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()

    def __enter__(self):
        """上下文管理器入口。"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口。"""
        self.disconnect()
        return False


class PooledConnection(DatabaseConnection):
    """
    从连接池获取的连接包装类。
    
    自动管理连接的获取和归还。
    """

    def __init__(self, pool: ConnectionPool):
        """
        初始化池化连接。
        
        :param pool: 连接池对象
        """
        self.pool = pool
        self._pool_conn = None  # 从池中获取的实际连接
        super().__init__(pool.config)

    def connect(self) -> None:
        """从连接池获取连接。"""
        if self._pool_conn is None:
            self._pool_conn = self.pool.get_connection()
            self._connection = self._pool_conn
            logger.debug("从连接池获取连接")

    def disconnect(self) -> None:
        """归还连接到连接池。"""
        if self._pool_conn:
            self.pool.return_connection(self._pool_conn)
            self._pool_conn = None
            self._connection = None
            logger.debug("连接已归还到连接池")

    def is_connected(self) -> bool:
        """检查连接是否有效。"""
        if self._pool_conn is None:
            return False
        try:
            return self._pool_conn.is_connected()
        except Exception:
            return False


class ConnectionPool:
    """
    数据库连接池。
    
    管理多个数据库连接，提供连接的获取和归还功能。
    """

    _pools: Dict[str, Any] = {}  # 全局连接池字典，key 为配置的 hash

    def __init__(self, config: DatabaseConfig):
        """
        初始化连接池。
        
        :param config: 数据库配置
        """
        self.config = config
        self._pool: Optional[Any] = None
        self._pool_key = self._get_pool_key(config)

    @staticmethod
    def _get_pool_key(config: DatabaseConfig) -> str:
        """
        生成连接池的唯一标识。
        
        :param config: 数据库配置
        :return: 连接池标识字符串
        """
        return f"{config.host}:{config.port}:{config.user}:{config.database}"

    def get_pool(self) -> Any:
        """
        获取或创建连接池。
        
        :return: 连接池对象
        """

        if self._pool_key not in ConnectionPool._pools:
            logger.debug(f"创建新连接池: {self._pool_key}")
            try:
                pool_config = {
                    'pool_name': self._pool_key,
                    'pool_size': self.config.pool_size,
                    'pool_reset_session': True,
                    **self.config.to_dict()
                }
                self._pool = pooling.MySQLConnectionPool(**pool_config)
                ConnectionPool._pools[self._pool_key] = self._pool
                logger.info(f"连接池创建成功: {self._pool_key} (size: {self.config.pool_size})")
            except Error as e:
                logger.error(f"创建连接池失败: {e}")
                raise
        else:
            self._pool = ConnectionPool._pools[self._pool_key]
            logger.debug(f"使用已有连接池: {self._pool_key}")
        return self._pool

    def get_connection(self) -> Any:
        """
        从连接池获取一个连接。
        
        :return: 数据库连接对象
        :raises PoolError: 连接池已满或获取超时时抛出
        """
        pool = self.get_pool()
        try:
            logger.debug(f"从连接池获取连接: {self._pool_key}")
            conn = pool.get_connection()
            logger.debug("成功从连接池获取连接")
            return conn
        except Error as e:
            logger.error(f"从连接池获取连接失败: {e}")
            raise

    def return_connection(self, conn: Any) -> None:
        """
        归还连接到连接池。
        
        注意：mysql.connector.pooling 的连接在使用完毕后会自动归还，
        但显式调用此方法可以确保连接正确关闭。
        
        :param conn: 数据库连接对象
        """
        if conn and conn.is_connected():
            try:
                conn.close()
                logger.debug(f"连接已归还到连接池: {self._pool_key}")
            except Error as e:
                logger.warning(f"归还连接到连接池时出错: {e}")

    @classmethod
    def close_all_pools(cls) -> None:
        """关闭所有连接池。"""
        logger.debug(f"正在关闭 {len(cls._pools)} 个连接池")
        for pool_key, pool in list(cls._pools.items()):
            try:
                # mysql.connector.pooling 的连接池会在程序退出时自动关闭
                # 这里主要是清理引用
                logger.debug(f"移除连接池: {pool_key}")
            except Exception as e:
                logger.warning(f"关闭连接池 {pool_key} 时出错: {e}")
        cls._pools.clear()
        logger.info("所有连接池已关闭")


def get_connection(
        config: Optional[DatabaseConfig] = None,
        use_pool: bool = True
) -> DatabaseConnection:
    """
    获取数据库连接的便捷函数。

    :param config: 数据库配置，如果为 None 则从环境变量加载，推荐从环境变量加载
    :param use_pool: 是否使用连接池，默认为 True
    :return: 一个 DatabaseConnection 对象
    """
    if config is None:
        config = DatabaseConfig.from_env()

    if use_pool:
        logger.debug("使用连接池模式")
        pool = get_connection_pool(config)
        return PooledConnection(pool)
    else:
        logger.debug("使用直接连接模式")
        return DatabaseConnection(config)


@contextmanager
def get_db_context(config: Optional[DatabaseConfig] = None, use_pool: bool = True):
    """
    数据库连接上下文管理器。

    使用示例：
        with get_db_context() as db:
            results = db.execute_query("SELECT * FROM cases")

    :param config: 数据库配置
    :param use_pool: 是否使用连接池
    :yield: 数据库连接对象
    """
    conn = get_connection(config, use_pool=use_pool)
    try:
        conn.connect()
        yield conn
    finally:
        conn.disconnect()


def get_connection_pool(config: Optional[DatabaseConfig] = None) -> ConnectionPool:
    """
    获取连接池的便捷函数。
    
    :param config: 数据库配置，如果为 None 则从环境变量加载
    :return: 连接池对象(ConnectionPool)
    """
    if config is None:
        config = DatabaseConfig.from_env()
    return ConnectionPool(config)
