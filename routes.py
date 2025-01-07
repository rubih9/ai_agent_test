from app import app, db, Book, User, Borrow
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime

# 首页
@app.route('/')
def index():
    books = Book.query.all()
    return render_template('index.html', books=books)

# 用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('注册成功！')
        return redirect(url_for('login'))
    return render_template('register.html')

# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('登录成功！')
            return redirect(url_for('index'))
        flash('用户名或密码错误')
    return render_template('login.html')

# 用户登出
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录')
    return redirect(url_for('index'))

# 图书列表
@app.route('/books')
def books():
    books = Book.query.all()
    return render_template('books.html', books=books)

# 添加图书
@app.route('/book/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if not current_user.is_admin:
        flash('权限不足')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        quantity = int(request.form['quantity'])
        
        if Book.query.filter_by(isbn=isbn).first():
            flash('ISBN已存在')
            return redirect(url_for('add_book'))
            
        book = Book(title=title, author=author, isbn=isbn, quantity=quantity)
        db.session.add(book)
        db.session.commit()
        flash('图书添加成功！')
        return redirect(url_for('books'))
    return render_template('add_book.html')

# 编辑图书
@app.route('/book/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    if not current_user.is_admin:
        flash('权限不足')
        return redirect(url_for('index'))
        
    book = Book.query.get_or_404(id)
    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        book.quantity = int(request.form['quantity'])
        book.available = book.available + (int(request.form['quantity']) - book.quantity)
        db.session.commit()
        flash('图书信息已更新！')
        return redirect(url_for('books'))
    return render_template('edit_book.html', book=book)

# 删除图书
@app.route('/book/delete/<int:id>')
@login_required
def delete_book(id):
    if not current_user.is_admin:
        flash('权限不足')
        return redirect(url_for('index'))
        
    book = Book.query.get_or_404(id)
    if book.borrows.filter_by(is_returned=False).first():
        flash('该图书还有未归还的借阅记录，无法删除')
        return redirect(url_for('books'))
    
    db.session.delete(book)
    db.session.commit()
    flash('图书已删除！')
    return redirect(url_for('books'))

# 借书
@app.route('/book/borrow/<int:id>')
@login_required
def borrow_book(id):
    book = Book.query.get_or_404(id)
    if book.available <= 0:
        flash('该图书已全部借出')
        return redirect(url_for('books'))
        
    if Borrow.query.filter_by(user_id=current_user.id, book_id=id, is_returned=False).first():
        flash('您已借阅过该图书')
        return redirect(url_for('books'))
        
    borrow = Borrow(user_id=current_user.id, book_id=id)
    book.available -= 1
    db.session.add(borrow)
    db.session.commit()
    flash('借阅成功！')
    return redirect(url_for('my_borrows'))

# 还书
@app.route('/book/return/<int:id>')
@login_required
def return_book(id):
    borrow = Borrow.query.get_or_404(id)
    if borrow.user_id != current_user.id:
        flash('权限不足')
        return redirect(url_for('my_borrows'))
        
    borrow.is_returned = True
    borrow.return_date = datetime.utcnow()
    borrow.book.available += 1
    db.session.commit()
    flash('图书已归还！')
    return redirect(url_for('my_borrows'))

# 我的借阅
@app.route('/my-borrows')
@login_required
def my_borrows():
    borrows = Borrow.query.filter_by(user_id=current_user.id).order_by(Borrow.borrow_date.desc()).all()
    return render_template('my_borrows.html', borrows=borrows)

# 所有借阅记录（管理员）
@app.route('/borrows')
@login_required
def all_borrows():
    if not current_user.is_admin:
        flash('权限不足')
        return redirect(url_for('index'))
    borrows = Borrow.query.order_by(Borrow.borrow_date.desc()).all()
    return render_template('all_borrows.html', borrows=borrows)