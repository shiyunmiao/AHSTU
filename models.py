# models.py - 数据库模型定义
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)   # 学号，唯一不可改
    username = db.Column(db.String(50), unique=True, nullable=False)     # 用户名
    email = db.Column(db.String(100), nullable=True)                      # 邮箱（注册时不再必填）
    password_hash = db.Column(db.String(255), nullable=False)            # 密码哈希
    nickname = db.Column(db.String(50), default='')                      # 昵称
    avatar_url = db.Column(db.Text, default='')                           # 头像（支持 base64）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)         # 注册时间
    is_admin = db.Column(db.Boolean, default=False)                      # 是否管理员

    messages = db.relationship('Message', backref='author', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    replies = db.relationship('Reply', backref='author', lazy='dynamic')

    def get_likes_received(self):
        from sqlalchemy import func
        return db.session.query(func.count(Like.id)).join(
            Message, Like.message_id == Message.id
        ).filter(Message.user_id == self.id).scalar() or 0


class Message(db.Model):
    """留言表"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), default='')       # 留言标题
    content = db.Column(db.Text, nullable=False)        # 留言正文
    image_url = db.Column(db.Text, default='')           # 图片链接（支持 base64）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_pinned = db.Column(db.Boolean, default=False)

    replies = db.relationship('Reply', backref='message', lazy='dynamic',
                              order_by='Reply.created_at', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='message', lazy='dynamic', cascade='all, delete-orphan')

    def like_count(self):
        return self.likes.count()

    def reply_count(self):
        return self.replies.count()

    def is_liked_by(self, user):
        if user.is_authenticated:
            return self.likes.filter_by(user_id=user.id).first() is not None
        return False


class Reply(db.Model):
    """回复表（支持嵌套回复）"""
    __tablename__ = 'replies'

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('replies.id'), nullable=True)  # 回复的回复
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    children = db.relationship('Reply', backref=db.backref('parent', remote_side=[id]),
                                lazy='dynamic', order_by='Reply.created_at')


class Like(db.Model):
    """点赞表"""
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'message_id', name='unique_like'),)
