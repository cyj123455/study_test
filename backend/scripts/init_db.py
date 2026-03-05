"""初始化 MySQL 表结构（在配置好 DATABASE_URL 后执行）"""
import sys
from pathlib import Path

# 将项目根加入 path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine, Base
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import User, PriceRecord, PriceDatasetVersion, WeatherRecord, PredictionRecord, ModelRun, AlertRecord
from app.models.user import UserRole
from app.services.auth import get_password_hash

def main():
    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    # 初始化管理员账号（若不存在）
    with Session(engine) as db:
        exists = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not exists:
            admin = User(
                username=settings.ADMIN_USERNAME,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                role=UserRole.admin.value,
            )
            db.add(admin)
            db.commit()
            print(f"已创建管理员账号：{settings.ADMIN_USERNAME}")
        else:
            print(f"管理员账号已存在：{settings.ADMIN_USERNAME}")
    print("表结构创建完成。")


if __name__ == "__main__":
    main()
