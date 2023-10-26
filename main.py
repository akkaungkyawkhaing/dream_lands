from datetime import date
from functools import wraps

from flask_ckeditor import CKEditor
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap

from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, abort

from forms import RegisterForm, CreatePostForm, LoginForm
from utility import secret_key, generate_pwd_hash, check_pwd_hash
from flask_login import LoginManager, UserMixin, login_manager, login_user, current_user, logout_user


def create_app():
    apps = Flask(__name__)
    apps.secret_key = secret_key
    csrf = CSRFProtect(apps)
    csrf.init_app(apps)
    Bootstrap(apps)
    ckeditor = CKEditor()
    ckeditor.init_app(apps)
    return apps


is_admin = False
app = create_app()
login_managers = LoginManager()
login_managers.init_app(app)

# CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///dream_journeys.db"
# Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()
db.init_app(app)


class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text, nullable=False)
    create_date = db.Column(db.String(20), nullable=False)


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))


# With SQLAlchemy 3.x
with app.app_context():
    db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.id != 1:
                return abort(404)
        else:
            return abort(404)
        return f(*args, **kwargs)

    return decorated_function


@login_managers.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    get_all_posts = Post.query.all()
    print(get_all_posts[0])
    return render_template('index.html', posts=get_all_posts, first_post=get_all_posts[0], is_authenticated=current_user.is_authenticated)


@app.route('/post/<int:post_id>', methods=["GET", "POST"])
def post(post_id):
    get_post = Post.query.filter_by(id=post_id).first()
    print(get_post)
    return render_template('post.html', post=get_post, is_authenticated=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    # if not current_user.is_authenticated:
    register_form = RegisterForm()
    if request.method == 'POST' and register_form.validate_on_submit():
        # Check if the email already exists in the database
        existing_user = User.query.filter_by(email=request.form.get('email')).first()
        if existing_user:
            flash('This email is already in use. Please choose another one.')
        else:
            full_name = f'{request.form.get("f_name")} {request.form.get("l_name")}'
            new_user = User(
                email=request.form.get('email'),
                password=generate_pwd_hash(request.form.get('password')),
                name=full_name.lower()
            )
            db.session.add(new_user)
            db.session.commit()
            # Log in and authenticate user after adding details to database.
            login_user(new_user)

            return redirect(url_for('home'))

    return render_template('register.html', form=register_form)


@app.route('/login', methods=["GET", "POST"])
def login():
    if not current_user.is_authenticated:
        login_form = LoginForm()
        if request.method == "POST" and login_form.validate_on_submit():
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            if not user:
                flash("Login failed, please try again!", 'error')
                return redirect(url_for('login'))
            elif not check_pwd_hash(user.password, password):
                flash("Login failed, please try again!", 'error')
                return redirect(url_for('login'))
            else:
                login_user(user)

                return redirect(url_for('home'))

        return render_template('login.html', form=login_form, is_authenticated=current_user.is_authenticated)
    return redirect(url_for('home'))


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if request.method == 'POST' and form.validate_on_submit():
        new_location = Post(
            location_name=form.location_name.data,
            country=form.country.data,
            img_url=form.img_url.data,
            description=form.description.data,
            create_date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_location)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("make-post.html", form=form, is_edit=False)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    get_post = Post.query.get(post_id)
    form = CreatePostForm()
    if request.method == 'POST' and form.validate_on_submit():
        get_post.location_name = form.location_name.data
        get_post.country = form.country.data
        get_post.img_url = form.img_url.data
        get_post.description = form.description.data
        db.session.commit()
        return redirect(url_for('home'))
    else:
        edit_form = CreatePostForm(
            location_name=get_post.location_name,
            country=get_post.country,
            img_url=get_post.img_url,
            description=get_post.description,
        )
    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = Post.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/elements')
def elements():
    return render_template('elements.html')


@app.route('/generic')
def generic():
    return render_template('generic.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)


# add edit and delete button
# make-post add back to home btn
# add full story page like home page design ✅️
# fix page effect not working
# add error message

#https://medium.com/@christoh/how-to-implement-a-chatgpt-bot-via-a-python-flask-app-b8504ddd6e68