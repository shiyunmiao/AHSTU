# app.py - Flask 主程序
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, jsonify, send_from_directory, session)
import os
import random
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, Message, Reply, Like

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# 文件上传配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 最大 5MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Flask-Login 设置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── 4.0 服务上传的图片文件 ───
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """访问上传的图片文件"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ─── 4.1 首页：滚动浏览 ───
@app.route('/')
def index():
    sort = request.args.get('sort', 'time')
    if sort == 'hot':
        from sqlalchemy import func
        messages = Message.query.outerjoin(
            Like, Like.message_id == Message.id
        ).group_by(Message.id).order_by(
            Message.is_pinned.desc(),
            func.count(Like.id).desc(),
            Message.created_at.desc()
        ).limit(100).all()
    else:
        messages = Message.query.order_by(
            Message.is_pinned.desc(),
            Message.created_at.desc()
        ).limit(100).all()

    return render_template('index.html', messages=messages, sort=sort)


# ─── 4.2 发布留言 ───
@app.route('/publish', methods=['GET', 'POST'])
def publish():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('请先登录')
            return redirect(url_for('login'))
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        image_url = request.form.get('image_url', '').strip()

        # 处理文件上传（如果用户选了文件）
        file = request.files.get('image_file')
        if file and file.filename:
            # 检查文件类型
            ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
            if ext in ALLOWED_EXTENSIONS:
                # 用安全文件名保存
                filename = secure_filename(f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{file.filename}')
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_url = url_for('uploaded_file', filename=filename)
            else:
                flash('不支持的文件格式，请上传图片文件')
                return render_template('publish.html')

        if not content:
            flash('留言内容不能为空')
            return render_template('publish.html')
        if len(content) > 5000:
            flash('留言内容不能超过5000字')
            return render_template('publish.html')
        message = Message(user_id=current_user.id, title=title, content=content, image_url=image_url)
        db.session.add(message)
        db.session.commit()
        flash('留言发布成功 🎉')
        return redirect(url_for('index'))

    return render_template('publish.html')

# ─── 4.3 注册 ───
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # 生成验证码
    num1 = random.randint(1, 20)
    num2 = random.randint(1, 10)
    session['captcha_answer'] = num1 + num2
    captcha_text = f'{num1} + {num2} = ?'

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        nickname = request.form.get('nickname', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        captcha_input = request.form.get('captcha', '').strip()

        if not all([student_id, nickname, password, confirm]):
            flash('所有字段都是必填的')
            return render_template('register.html', captcha_text=captcha_text)
        if password != confirm:
            flash('两次密码输入不一致')
            return render_template('register.html', captcha_text=captcha_text)
        if len(password) < 6:
            flash('密码长度至少6位')
            return render_template('register.html', captcha_text=captcha_text)
        if not captcha_input or not captcha_input.isdigit() or int(captcha_input) != session.get('captcha_answer'):
            flash('验证码错误')
            return render_template('register.html', captcha_text=captcha_text)
        if User.query.filter_by(student_id=student_id).first():
            flash('该学号已被注册')
            return render_template('register.html', captcha_text=captcha_text)
        if User.query.filter_by(username=nickname).first():
            flash('该昵称已被使用')
            return render_template('register.html', captcha_text=captcha_text)

        user = User(
            student_id=student_id, username=nickname, nickname=nickname,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('注册成功！欢迎加入校园留言墙')
        return redirect(url_for('index'))

    return render_template('register.html', captcha_text=captcha_text)


# ─── 4.4 登录 ───
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember')

        user = User.query.filter(
            (User.username == login_id) | (User.student_id == login_id)
        ).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=bool(remember))
            next_page = request.args.get('next')
            flash(f'欢迎回来，{user.nickname or user.username}')
            return redirect(next_page or url_for('index'))
        else:
            flash('学号/用户名或密码错误')

    return render_template('login.html')


# ─── 4.5 退出 ───
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录')
    return redirect(url_for('index'))


# ─── 4.6 个人主页 ───
@app.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    messages = Message.query.filter_by(user_id=user_id).order_by(
        Message.created_at.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    likes_received = user.get_likes_received()
    return render_template('user.html', profile_user=user,
                          messages=messages, likes_received=likes_received)


# ─── 4.7 个人信息编辑 ───
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        email = request.form.get('email', '').strip()
        if nickname:
            current_user.nickname = nickname
        if email:
            existing = User.query.filter(User.email == email, User.id != current_user.id).first()
            if existing:
                flash('该邮箱已被其他用户使用')
                return redirect(url_for('profile'))
            current_user.email = email
        db.session.commit()
        flash('个人信息已更新')
        return redirect(url_for('profile'))
    return render_template('profile.html')


# ─── 4.8 修改密码 ───
@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_pw = request.form.get('old_password', '')
        new_pw = request.form.get('new_password', '')
        confirm = request.form.get('confirm', '')
        if not check_password_hash(current_user.password_hash, old_pw):
            flash('旧密码不正确')
            return redirect(url_for('change_password'))
        if new_pw != confirm:
            flash('两次新密码输入不一致')
            return redirect(url_for('change_password'))
        if len(new_pw) < 6:
            flash('新密码长度至少6位')
            return redirect(url_for('change_password'))
        current_user.password_hash = generate_password_hash(new_pw)
        db.session.commit()
        flash('密码已修改，请重新登录')
        logout_user()
        return redirect(url_for('login'))
    return render_template('change_password.html')


# ─── 4.9 留言详情页（查看留言 + 回复） ───
@app.route('/message/<int:message_id>', methods=['GET', 'POST'])
def message_detail(message_id):
    message = Message.query.get_or_404(message_id)

    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('请先登录')
            return redirect(url_for('login', next=request.url))
        content = request.form.get('content', '').strip()
        if not content:
            flash('回复内容不能为空')
            return redirect(url_for('message_detail', message_id=message_id))
        reply = Reply(message_id=message_id, user_id=current_user.id, content=content)
        db.session.add(reply)
        db.session.commit()
        flash('回复成功')
        return redirect(url_for('message_detail', message_id=message_id))

    return render_template('message.html', message=message)


# ─── 4.10 删除留言 ───
@app.route('/message/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.user_id != current_user.id and not current_user.is_admin:
        flash('你没有权限删除此留言')
        return redirect(url_for('index'))
    db.session.delete(message)
    db.session.commit()
    flash('留言已删除')
    return redirect(url_for('index'))


# ─── 4.11 删除回复 ───
@app.route('/reply/<int:reply_id>/delete', methods=['POST'])
@login_required
def delete_reply(reply_id):
    reply = Reply.query.get_or_404(reply_id)
    if reply.user_id != current_user.id and not current_user.is_admin:
        flash('你没有权限删除此回复')
        return redirect(url_for('message_detail', message_id=reply.message_id))
    message_id = reply.message_id
    db.session.delete(reply)
    db.session.commit()
    flash('回复已删除')
    return redirect(url_for('message_detail', message_id=message_id))


# ─── 4.12 点赞（AJAX） ───
@app.route('/like/<int:message_id>', methods=['POST'])
@login_required
def toggle_like(message_id):
    message = Message.query.get_or_404(message_id)
    existing_like = Like.query.filter_by(
        user_id=current_user.id, message_id=message_id
    ).first()
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({'liked': False, 'count': message.like_count()})
    else:
        like = Like(user_id=current_user.id, message_id=message_id)
        db.session.add(like)
        db.session.commit()
        return jsonify({'liked': True, 'count': message.like_count()})


# ─── 4.13 搜索（简化版，无分页） ───
@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'content')

    if not q:
        return render_template('search.html', messages=[], q='', search_type='content')

    if search_type == 'user':
        user = User.query.filter(
            (User.username.ilike(f'%{q}%')) |
            (User.student_id.ilike(f'%{q}%'))
        ).first()
        if user:
            messages = Message.query.filter_by(user_id=user.id).order_by(
                Message.created_at.desc()
            ).limit(50).all()
        else:
            messages = []
    else:
        messages = Message.query.filter(
            Message.content.ilike(f'%{q}%')
        ).order_by(
            Message.created_at.desc()
        ).limit(50).all()

    return render_template('search.html', messages=messages, q=q, search_type=search_type)


# ─── 4.14 管理后台 ───
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('需要管理员权限')
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    messages = Message.query.order_by(Message.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    user_count = User.query.count()
    message_count = Message.query.count()
    reply_count = Reply.query.count()

    return render_template('admin.html', messages=messages,
                          user_count=user_count, message_count=message_count,
                          reply_count=reply_count)


# ─── 4.15 管理员：置顶 ───
@app.route('/admin/pin/<int:message_id>', methods=['POST'])
@login_required
def admin_pin(message_id):
    if not current_user.is_admin:
        return jsonify({'error': '无权限'}), 403
    message = Message.query.get_or_404(message_id)
    message.is_pinned = not message.is_pinned
    db.session.commit()
    return jsonify({'pinned': message.is_pinned})


# ─── 初始化数据库 ───
@app.cli.command('init-db')
def init_db():
    db.create_all()
    print('✓ 数据库表已创建')

    if not User.query.filter_by(username='admin').first():
        admin = User(
            student_id='00000000', username='admin',
            password_hash=generate_password_hash('admin123'),
            nickname='管理员', is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print('✓ 默认管理员已创建（admin / admin123）')


# ─── 生产启动时自动创建表 + 默认管理员（gunicorn 也会执行） ───
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            student_id='00000000', username='admin',
            password_hash=generate_password_hash('admin123'),
            nickname='管理员', is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print('✓ 默认管理员已创建（admin / admin123）')

if __name__ == '__main__':
    # 本地开发用 debug 模式，部署时通过环境变量控制
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    app.run(debug=debug_mode, host='0.0.0.0')
