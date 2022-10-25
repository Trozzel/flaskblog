import os, secrets
from PIL import Image
from flask_login import login_required, login_user, current_user, logout_user
from flaskblog import app, bcrypt, db, mail
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog.forms import (RegistrationForm, LoginForm, ResetPassword, UpdateAccountForm,
    PostForm, RequestResetForm)
from flaskblog.models import Post, User
from flask_mail import Message

@app.route('/')
@app.route('/index')
@app.route('/home')
def home():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template("home.html", posts=posts)


@app.route("/about") 
def about():
    return render_template("about.html", title="About")

 
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        uname = form.username.data
        email=form.email.data
        user = User(username=uname, password=hashed_pw, email=email)
        db.session.add(user)
        db.session.commit()
        flash(f"Account created for {form.username.data}!", "success")
        return redirect(url_for("login"))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            flash(f"Welcome {current_user.username}!", "success")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        flash("Login unsuccessful. Please try again.", "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for("home"))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    file_ext = os.path.splitext(form_picture.filename)[1]
    new_fname = random_hex + file_ext
    full_fname = os.path.join(app.root_path, "static/profile_pics", new_fname)

    img = Image.open(form_picture)
    img.thumbnail((125, 125))
    img.save(full_fname)
    
    return new_fname


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            current_user.img_file = save_picture(form.picture.data)
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("You have successfully updated your account!", "success")
        return redirect(url_for("account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for("static", filename="profile_pics/" + current_user.img_file)
    return render_template("account.html", title="Account", 
            image_file=image_file, form=form)


@app.route("/post/new", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, 
            author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("New post uploaded successfully!", "success")
        return redirect(url_for("home"))
    return render_template("create_post.html", title="New Post", form=form,
        legend="New Post")


@app.route("/post/<post_id>")
def post(post_id: int):
    post = Post.query.get_or_404(post_id)
    return render_template("post.html", title=post.title, post=post)

    
@app.route("/post/<int:post_id>/update", methods=["POST", "GET"])
@login_required
def update_post(post_id: int):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Post updated successfully!", "success")
        return redirect(url_for("post", post_id=post.id))
    elif request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content
    return render_template("create_post.html", title="Update Post", form=form,
        legend="Update Post")


@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id: int):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted!!", "success")
    return redirect(url_for("home"))

@app.route("/user/<string:username>")
def user_posts(username: str):
    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user) \
        .order_by(Post.date_posted.desc())    \
        .paginate(page=page, per_page=5)
    return render_template("user_posts.html", posts=posts, user=user)


def send_reset_email(user: User):
    token = user.get_reset_token()
    msg = Message("Password Reset for 'flaskblog'", sender="noreply@demo.com",
                  recipients=[user.email])
    msg.body = "To reset your password, please visit the following link: \n"\
        f"{url_for('reset_token', token=token, _external=True)}"
    mail.send(msg)
    
    
@app.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    # If the user is already logged in, then redirect to home
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
            return redirect(url_for("login"))
    return render_template("reset_request.html", title="Reset Password", form=form)
    

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    # If the user is already logged in, no need to reset email
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    user = User.get_reset_token(token)
    if not user:
        flash("That is an invalid or expired token.", "warning")
        return redirect(url_for("reset_request"))
    form = ResetPassword()
    if form.validate_on_submit():
        hashed_pword = bcrypt.generate_password_hash(form.password.data)
        user.password = hashed_pword
        db.session.commit()
        flash("You have successfully updated your password!", "success")
        redirect(url_for("login"))
    return render_template("reset_token.html", title="Reset Password", form=form)
