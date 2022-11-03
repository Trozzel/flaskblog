from flask_login import login_required, login_user, current_user, logout_user
from flaskblog import bcrypt, db
from flask import render_template, url_for, flash, redirect, request, Blueprint
from flaskblog.users.forms import (ChangePasswordForm, RegistrationForm,
                                   LoginForm, ResetPassword, UpdateAccountForm,
                                   RequestResetForm)
from flaskblog.users.utils import save_picture, send_reset_email
from flaskblog.models import Post, User


users = Blueprint("users", __name__)


@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(
            form.password.data).decode("utf-8")
        uname = form.username.data
        email = form.email.data
        user = User(username=uname, password=hashed_pw, email=email)
        db.session.add(user)
        db.session.commit()
        flash(f"Account created for {form.username.data}!", "success")
        return redirect(url_for("users.login"))
    return render_template('register.html', title='Register', form=form)


@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            flash(f"Welcome {current_user.username}!", "success")
            return redirect(next_page) if next_page else redirect(url_for("main.home"))
        flash("Login unsuccessful. Please try again.", "danger")
    return render_template("login.html", title="Login", form=form)


@users.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    pw_form = ChangePasswordForm()
    if form.validate_on_submit():
        if form.picture.data:
            current_user.img_file = save_picture(form.picture.data)
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("You have successfully updated your account!", "success")
        return redirect(url_for("users.account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email

    if pw_form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(
            pw_form.password.data).decode("utf-8")
        current_user.password = hashed_pw
        db.session.commit()
        flash("You have successfully changed your password!", "success")
        return redirect(url_for("users.account"))
    image_file = url_for(
        "static", filename="profile_pics/" + current_user.img_file)
    return render_template("account.html", title="Account",
                           image_file=image_file, form=form, pw_form=pw_form)


@users.route("/user/<string:username>")
def user_posts(username: str):
    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user) \
        .order_by(Post.date_posted.desc())    \
        .paginate(page=page, per_page=5)
    return render_template("user_posts.html", posts=posts, user=user)


@users.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    # If the user is already logged in, then redirect to home
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
            return redirect(url_for("users.login"))
    return render_template("reset_request.html", title="Reset Password", form=form)


@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    # If the user is already logged in, no need to reset email
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    user = User.verify_reset_token(token)
    if not user:
        flash("That is an invalid or expired token.", "warning")
        return redirect(url_for("users.reset_request"))
    form = ResetPassword()
    if form.validate_on_submit():
        hashed_pword = bcrypt.generate_password_hash(form.password.data)
        user.password = hashed_pword
        db.session.commit()
        flash("You have successfully updated your password!", "success")
        redirect(url_for("users.login"))
    return render_template("reset_token.html", title="Reset Password", form=form)
