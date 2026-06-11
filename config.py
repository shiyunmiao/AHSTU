# config.py - 数据库和应用配置
import os

class Config:
    """所有配置项集中在这里"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # 数据库连接：优先读环境变量，最后用 Railway 外部连接
    raw_url = (
        os.environ.get('DATABASE_PUBLIC_URL')
        or os.environ.get('DATABASE_URL')
        or 'postgresql://postgres:ANGGWXissMcnSCmhDwObuasillUnLQSA@monorail.proxy.rlwy.net:38881/railway'
    )

    # 统一转为 pg8000 驱动格式
    if raw_url.startswith('postgres://'):
        raw_url = raw_url.replace('postgres://', 'postgresql+pg8000://', 1)
    elif raw_url.startswith('postgresql://') and '+pg8000' not in raw_url:
        raw_url = raw_url.replace('postgresql://', 'postgresql+pg8000://', 1)

    SQLALCHEMY_DATABASE_URI = raw_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
