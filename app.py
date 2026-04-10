from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'secret123'

db = SQLAlchemy(app)

# 🔐 Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 👤 User table
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

# 📝 Task table
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    complete = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(10), default='Low')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# ✅ create database
with app.app_context():
    db.create_all()

# 🔄 load user
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 🏠 Home
@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        task_title = request.form['title']
        due_date = request.form['due_date']
        priority = request.form['priority']

        if due_date:
            due_date = datetime.strptime(due_date, '%Y-%m-%d')

        new_task = Task(
            title=task_title,
            due_date=due_date,
            priority=priority,
            user_id=current_user.id
        )

        db.session.add(new_task)
        db.session.commit()
        return redirect('/')

    search = request.args.get('search')

    if search:
        tasks = Task.query.filter(
            Task.title.contains(search),
            Task.user_id == current_user.id
        ).all()
    else:
        tasks = Task.query.filter_by(user_id=current_user.id).all()

    return render_template('index.html', tasks=tasks)

# ✔ Complete
@app.route('/complete/<int:id>')
@login_required
def complete(id):
    task = Task.query.get(id)
    task.complete = not task.complete
    db.session.commit()
    return redirect('/')

# ❌ Delete
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    task = Task.query.get(id)
    db.session.delete(task)
    db.session.commit()
    return redirect('/')

# 📝 Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)

        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

# 🔑 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')

    return render_template('login.html')

# 🚪 Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)