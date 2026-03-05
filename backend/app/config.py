"""应用配置"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """从环境变量读取配置"""
    # 应用
    APP_NAME: str = "农产品价格分析与预测系统"
    DEBUG: bool = False

    # 数据库 MySQL 8.0+
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root"
    MYSQL_DATABASE: str = "agri_price_db"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # 默认管理员账号（用于初始化脚本创建）
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123456"

    # 本地数据路径（不爬虫时使用已有数据）
    DATA_CABBAGE_PATH: str = r"D:\毕设\江南果菜市场白菜价格表.xlsx"
    DATA_POTATO_PATH: str = r"D:\毕设\江南果菜市场-土豆批发价格表.xlsx"   # 若土豆在单独文件可改为土豆价格表路径
    DATA_WEATHER_PATH: str = r"D:\毕设\广东省-广州.xlsx"

    # 数据与模型
    UPLOAD_DIR: str = "uploads"
    MODEL_CACHE_DIR: str = "model_cache"
    TRAIN_TEST_SPLIT: float = 0.8
    CROSS_VALIDATION_FOLDS: int = 5

    # 预警阈值（PRD：单日涨幅≥20%、跌幅≥15%）
    ALERT_RISE_PCT: float = 20.0
    ALERT_DROP_PCT: float = 15.0
    # 异常价格区间：均值 ± 3 倍标准差
    OUTLIER_STD_MULTIPLIER: float = 3.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
