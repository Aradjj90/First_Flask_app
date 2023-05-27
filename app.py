from flask import Flask, url_for, render_template, request, session, flash, redirect, make_response, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.secret_key = "lkmwklcmslkcmklcmwlcmcmk"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
app.app_context().push()

menu_lock = [{"title": "Home", "url": "/"},
             {"title": "First page", "url": "/first-page"},
             {"title": "About", "url": "/about"},
             {"title": "Login", "url": "/login"},
             {"title": "Sign up", "url": "/register"},
             ]

menu_unlock = [{"title": "Home", "url": "/"},
               {"title": "First page", "url": "/first-page"},
               {"title": "About", "url": "/about"},
               {"title": "Contacts", "url": "/contacts"},
               {"title": "Logout", "url": "/login_out"},
               {"title": "Profile", "url": "/profile"},
               ]


def logged_check():
    try:
        if session['logged']:
            return True
        else:
            return False
    except:
        return False


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(50), unique=True)
    psw = db.Column(db.String(500), nullable=True)
    ava = db.Column(db.LargeBinary(length=2048), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<users {self.id}>"


@app.route("/")
def index():
    return render_template('index.html', title="Home page", menu=menu_unlock if logged_check() else menu_lock)


@app.route("/login", methods=["POST", "GET"])
def login():
    if logged_check():
        return redirect(url_for('profile'))
    else:
        if request.method == "POST":
            user = Users.query.filter_by(email=request.form['email']).first()
            if user and check_password_hash(user.psw, request.form['psw']):
                session['logged'] = True
                session['name'] = user.name
                session['email'] = user.email
                session['ava'] = user.ava
                session['date'] = user.date
                return redirect(request.args.get("next") or url_for('profile'))
            else:
                flash("Wrong email or password", "error")

        return render_template('login.html', title="Login", menu=menu_unlock if logged_check() else menu_lock)


@app.route("/register", methods=["POST", "GET"])
def register():
    if logged_check():
        return redirect(url_for('profile'))
    else:
        if request.method == "POST":
            try:
                user = Users.query.filter_by(name=request.form['name']).first()
                if user:
                    flash("This Username is already in use", "error")
                    return render_template('register.html', title="Registration",
                                           menu=menu_unlock if logged_check() else menu_lock)
                user = Users.query.filter_by(email=request.form['email']).first()
                if user:
                    flash("This Email is already in use", "error")
                    return render_template('register.html', title="Registration",
                                           menu=menu_unlock if logged_check() else menu_lock)
                hash_pass = generate_password_hash(request.form['psw'])
                user = Users(psw=hash_pass, email=request.form['email'], name=request.form['name'], ava=None)
                db.session.add(user)
                db.session.commit()
                flash("You are successfully registered", "success")
                return redirect(url_for('login'))
            except:
                db.session.rollback()
                print("Error adding to the database")

        return render_template('register.html', title="Registration", menu=menu_unlock if logged_check() else menu_lock)


@app.route("/profile")
def profile():
    if logged_check():
        return render_template('profile.html', title=f"Profile",
                               menu=menu_unlock if logged_check() else menu_lock)
    else:
        flash("This page will be active after login", "error")
        return redirect(url_for('login'))


@app.route("/first-page")
def first_page():
    if logged_check():
        return render_template('first_page.html', title="First page", menu=menu_unlock if logged_check() else menu_lock)
    else:
        flash("This page will be active after login", "error")
        return redirect(url_for('login'))


@app.route("/login_out")
def logout():
    session['logged'] = False
    session['name'] = None
    return redirect(url_for('index'))


@app.route("/about")
def about():
    return render_template('about.html', title="About", menu=menu_unlock if logged_check() else menu_lock)


@app.route("/contacts")
def contacts():
    if logged_check():
        return (render_template('contacts.html', title="contacts",
                                menu=menu_unlock if logged_check() else menu_lock))
    else:
        return redirect(url_for('index'))


@app.route("/userava")
def userava():
    if logged_check():
        img = session.get('ava')
        if not img:
            try:
                with app.open_resource(app.root_path + url_for('static', filename='images/base_ava/default.png'),
                                       'rb') as f:
                    img = f.read()
            except FileNotFoundError:
                print("Can't load default avatar")

        h = make_response(img)
        h.headers['Content-Type'] = 'image/png'
        return h
    else:
        abort(401)


@app.route("/upload", methods=["POST", "GET"])
def upload():
    if logged_check():
        if request.method == "POST":
            user = Users.query.filter_by(email=session.get('email')).first()
            if user:
                file = request.files['file']
                user.ava = file.read()
                db.session.add(user)
                db.session.commit()
                session['ava'] = user.ava
            return redirect(url_for('profile'))
        return redirect(url_for('profile'))
    else:
        abort(401)
    return redirect(url_for('login'))


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
