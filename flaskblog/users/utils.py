import os
import secrets
from PIL import Image
from flaskblog import app, mail
from flask import url_for
from flaskblog.models import User
from flask_mail import Message


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    file_ext = os.path.splitext(form_picture.filename)[1]
    new_fname = random_hex + file_ext
    full_fname = os.path.join(app.root_path, "static/profile_pics", new_fname)

    img = Image.open(form_picture)
    img.thumbnail((125, 125))
    img.save(full_fname)

    return new_fname


def send_reset_email(user: User):
    token = user.get_reset_token()
    msg = Message("Password Reset for 'flaskblog'", sender="noreply@demo.com",
                  recipients=[user.email])
    msg.body = "To reset your password, please visit the following link: \n"\
        f"{url_for('users.reset_token', token=token, _external=True)}"
    mail.send(msg)
