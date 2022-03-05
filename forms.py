from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,widgets,PasswordField
from wtforms.validators import DataRequired, URL,Email
from wtforms.fields.html5 import EmailField
from flask_ckeditor import CKEditorField

##WTForm
class P_field(PasswordField):
    widget = widgets.PasswordInput(hide_value=False)
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")
class RegisterForm(FlaskForm):
    name=StringField('Name',validators=[DataRequired()])
    email=EmailField('Email',validators=[DataRequired(),Email()])
    password=P_field('Password',validators=[DataRequired()])
    submit=SubmitField('Register')
class LoginForm(FlaskForm):

    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = P_field('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
class CommentForm(FlaskForm):
    comment=CKEditorField('Leave Comment here!')
    submit=SubmitField('Comment')