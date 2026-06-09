# config.py - 数据库和应用配置（部署版）
import os

class Config:
    """所有配置项集中在这里"""
    # SECRET_KEY：生产环境从环境变量读取，本地用默认值
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # 数据库连接地址：优先使用环境变量（部署时用），没有则用本地数据库
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql+pg8000://postgres:admin@localhost/message_board')

    # Render 提供的 PostgreSQL 连接地址以 postgres:// 开头，需要转成 postgresql+pg8000://
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+pg8000://', 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
