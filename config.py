# config.py - 数据库和应用配置（部署版）
import os

class Config:
    """所有配置项集中在这里"""
    # SECRET_KEY：生产环境从环境变量读取，本地用默认值
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Railway PostgreSQL 连接地址（硬编码，确保能连上）
    SQLALCHEMY_DATABASE_URI = 'postgresql+pg8000://postgres:ANGGWXissMcnSCmhDwObuasillUnLQSA@monorail.proxy.rlwy.net:38881/railway'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
