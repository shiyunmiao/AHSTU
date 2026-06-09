# config.py - 数据库和应用配置（部署版）
import os

class Config:
    """所有配置项集中在这里"""
    # SECRET_KEY：生产环境从环境变量读取，本地用默认值
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # 数据库连接地址：优先使用 DATABASE_PUBLIC_URL（Railway 外部地址），
    # 其次 DATABASE_URL（内部地址），最后用本地数据库
    raw_db_url = (
        os.environ.get('DATABASE_PUBLIC_URL')
        or os.environ.get('DATABASE_URL')
        or 'postgresql+pg8000://postgres:admin@localhost/message_board'
    )

    # 不同平台提供的 DATABASE_URL 格式不同，统一转为 pg8000 驱动格式：
    #   Render:  postgres://...   → postgresql+pg8000://...
    #   Railway: postgresql://... → postgresql+pg8000://...
    if raw_db_url:
        if raw_db_url.startswith('postgres://'):
            raw_db_url = raw_db_url.replace('postgres://', 'postgresql+pg8000://', 1)
        elif raw_db_url.startswith('postgresql://'):
            raw_db_url = raw_db_url.replace('postgresql://', 'postgresql+pg8000://', 1)

    SQLALCHEMY_DATABASE_URI = raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
