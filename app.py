from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 后台账号密码
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'mima'

# 登录保护装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('请先登录', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 文章模型
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Post {self.title}>'

# 首页 - 文章列表
@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

# 文章详情页
@app.route('/post/<slug>')
def post_detail(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    return render_template('post.html', post=post)

# 登录页
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('登录成功', 'success')
            return redirect(url_for('admin'))
        else:
            flash('账号或密码错误', 'error')
    return render_template('login.html')

# 登出
@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    flash('已退出登录', 'success')
    return redirect(url_for('index'))

# 后台 - 发布文章
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        title = request.form['title']
        slug = request.form['slug']
        content = request.form['content']
        
        if not title or not slug or not content:
            flash('所有字段都必须填写', 'error')
            return redirect(url_for('admin'))
        
        if Post.query.filter_by(slug=slug).first():
            flash('该链接标识已存在，请换一个', 'error')
            return redirect(url_for('admin'))
        
        new_post = Post(title=title, slug=slug, content=content)
        db.session.add(new_post)
        db.session.commit()
        flash('文章发布成功！', 'success')
        return redirect(url_for('index'))
    
    return render_template('admin.html')

# 编辑文章
@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST':
        title = request.form['title']
        slug = request.form['slug']
        content = request.form['content']
        
        if not title or not slug or not content:
            flash('所有字段都必须填写', 'error')
            return redirect(url_for('edit_post', post_id=post_id))
        
        # 检查新 slug 是否与其他文章冲突
        existing = Post.query.filter_by(slug=slug).first()
        if existing and existing.id != post.id:
            flash('该链接标识已被其他文章使用', 'error')
            return redirect(url_for('edit_post', post_id=post_id))
        
        post.title = title
        post.slug = slug
        post.content = content
        db.session.commit()
        flash('文章修改成功！', 'success')
        return redirect(url_for('post_detail', slug=post.slug))
    
    return render_template('edit.html', post=post)

# 删除文章
@app.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('文章已删除', 'success')
    return redirect(url_for('index'))

# 初始化数据库并插入示例数据
@app.route('/init')
def init_db():
    db.create_all()
    if Post.query.count() == 0:
        sample = Post(
            title='欢迎来到我的 Flask 博客',
            slug='hello-world',
            content='这是用 Flask 搭建的博客。\n\n支持发布、编辑、删除文章。\n\n后台地址：/admin\n账号：admin\n密码：mima'
        )
        db.session.add(sample)
        db.session.commit()
        return '数据库初始化完成，已添加示例文章。'
    return '数据库已存在。'

if __name__ == '__main__':
    app.run(debug=True)
