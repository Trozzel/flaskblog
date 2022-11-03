from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, BooleanField, PasswordField, SubmitField,
                     ValidationError)
from wtforms.validators import DataRequired, EqualTo, Length, Email
from flaskblog.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_confirm = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "That username already exists. Please choose another")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                "That email already exists. Please choose another")


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField("Update Profile Picture", validators=[
                        FileAllowed(["jpg", "png"])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    "That username already exists. Please choose another")

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    "That email already exists. Please choose another")


class ChangePasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password_confirm = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Change Password")


class ResetPassword(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired()])
    password_confirm = PasswordField("New Password",
                                     validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Reset Password")


class RequestResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")

    def validate_email(self, email):
        user_email = User.query.filter_by(email=email.data).first()
        if not user_email:
            return ValidationError("You have entered an invalid email")
