from datetime import datetime
from functools import wraps
from flask import Flask, session, request, redirect, url_for, flash, send_from_directory
import os.path
from passlib.hash import sha256_crypt
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s"%(os.path.abspath(os.path.dirname(os.path.dirname(__file__))+'/db/todo.db'),)

# app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///todo.db'

db = SQLAlchemy(app=app)
app.secret_key = "secret key"


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(80))
    content = db.Column(db.String(1200), nullable=True)
    complete = db.Column(db.Boolean)
    created_date = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)
    user = db.relationship('User', backref='todos')


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(32), nullable=False)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash(message="bu sayfayı görüntülemek için giriş yapınız",
                  category="danger")
            return redirect(url_for("login"))
    return decorated_function


@app.route("/")
def index():
    if "logged_in" in session:
        todos = Todo.query.filter_by(user_id=session["user_id"])
        return render_template("mainpage.html", todos=todos)
    else:
        return render_template("index.html")


@app.route("/add", methods=["POST"])
@login_required
def addTodo():
    title = request.form.get('title')
    content = request.form.get('content')
    new_todo = Todo(user_id=session["user_id"], title=title,content=content, complete=False)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/complete/<id>")
@login_required
def completeTodo(id):
    todo = Todo.query.filter_by(id=id).first()
    todo.complete = not todo.complete
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/delete/<id>", methods=["GET"])
@login_required
def deleteTodo(id):
    todo = Todo.query.filter_by(id=id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("index"))

@app.route('/detail/<id>',methods=['GET'])
@login_required
def detailTodo(id):
    todo = Todo.query.filter_by(id=id).first()
    return render_template('tododetail.html',todo=todo)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = sha256_crypt.hash(request.form.get("password"))

        new_user = User(name=name, username=username,
                        email=email, password=password)

        db.session.add(new_user)
        db.session.commit()

        flash(message="başarıyla kayıt oldunuz .....", category="success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form = request.form
        user = User.query.filter_by(username=form.get("username")).first()
        if isinstance(user.id, int):
            if sha256_crypt.verify(form["password"], user.password):
                session["logged_in"] = True
                session["user_id"] = user.id
                return redirect(url_for("index"))
            else:
                flash(message="hatalı bir parola girdiniz", category="danger")
                return redirect(url_for("login"))
        else:
            flash(
                message="böyle bir kullanıcı bulumuyor aşağıdan kayıt olabilirsiniz", category="danger")
            return redirect(url_for("register"))
    else:
        return render_template("login.html")


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route('/about',methods=["GET"])
def about():
    return render_template('about.html')

@app.route("/static/<filename>")
def static_file(filename):
    return send_from_directory("static", filename=filename)

@app.template_filter('date')
def date_filter(date):
    return date.strftime("%m/%d/%Y - %H:%M")

def main():
    try:
        db.create_all()
        app.run(debug=True)
    except Exception as err:
        print("yine olmadı")
        print(err)
        print("----------------------------------------------------------------------")
        print(app.config["SQLALCHEMY_DATABASE_URI"])
        print("----------------------------------------------------------------------")




if __name__ == "__main__":
    main()
