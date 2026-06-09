# config.py - 数据库和应用配置（部署版）
import os

class Config:
    """所有配置项集中在这里"""
    # SECRET_KEY：生产环境从环境变量读取，本地用默认值
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # 数据库连接地址：优先使用环境变量（部署时用），没有则用本地数据库
    raw_db_url = os.environ.get('DATABASE_URL', 'postgresql+pg8000://postgres:admin@localhost/message_board')
    import sys
    print(f"[DEBUG] RAW DATABASE_URL from env: {raw_db_url!r}", file=sys.stderr)
    DATABASE_URL = raw_db_url

    # 不同平台提供的 DATABASE_URL 格式不同，统一转为 pg8000 驱动格式：
    #   Render:  postgres://...   → postgresql+pg8000://...
    #   Railway: postgresql://... → postgresql+pg8000://...
    if DATABASE_URL:
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+pg8000://', 1)
        elif DATABASE_URL.startswith('postgresql://'):
            DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+pg8000://', 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    print(f"[DEBUG] Final SQLALCHEMY_DATABASE_URI: {SQLALCHEMY_DATABASE_URI!r}", file=sys.stderr)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
