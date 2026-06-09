# config.py - 数据库和应用配置（部署版）
import os

class Config:
    """所有配置项集中在这里"""
    # SECRET_KEY：生产环境从环境变量读取，本地用默认值
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # 数据库连接地址
    DATABASE_PUBLIC_URL = os.environ.get('DATABASE_PUBLIC_URL')
    DATABASE_URL = os.environ.get('DATABASE_URL')

    import sys
    print(f"[DEBUG] DATABASE_PUBLIC_URL exists: {bool(DATABASE_PUBLIC_URL)}", file=sys.stderr)
    print(f"[DEBUG] DATABASE_URL exists: {bool(DATABASE_URL)}", file=sys.stderr)
    print(f"[DEBUG] All env vars: {[(k,v) for k,v in os.environ.items() if 'DATABASE' in k.upper() or 'SECRET' in k.upper()]}", file=sys.stderr)

    # 优先使用 DATABASE_PUBLIC_URL（Railway 外部地址），
    # 其次 DATABASE_URL（内部地址），最后用本地数据库
    raw_db_url = (
        DATABASE_PUBLIC_URL
        or DATABASE_URL
        or 'postgresql+pg8000://postgres:admin@localhost/message_board'
    )

    print(f"[DEBUG] Using raw_db_url: {raw_db_url!r}", file=sys.stderr)

    # 不同平台提供的 DATABASE_URL 格式不同，统一转为 pg8000 驱动格式
    if raw_db_url:
        if raw_db_url.startswith('postgres://'):
            raw_db_url = raw_db_url.replace('postgres://', 'postgresql+pg8000://', 1)
        elif raw_db_url.startswith('postgresql://'):
            raw_db_url = raw_db_url.replace('postgresql://', 'postgresql+pg8000://', 1)

    SQLALCHEMY_DATABASE_URI = raw_db_url
    print(f"[DEBUG] Final SQLALCHEMY_DATABASE_URI: {SQLALCHEMY_DATABASE_URI!r}", file=sys.stderr)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
