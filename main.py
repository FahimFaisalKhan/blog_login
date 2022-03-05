from flask import Flask, render_template, redirect, url_for, flash,request,abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm,RegisterForm,LoginForm,CommentForm
from flask_gravatar import Gravatar
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap(app)
db_path=os.environ.get('DATABASE_URL')
if db_path.startswith("postgres://"):
    db_path = db_path.replace("postgres://", "postgresql://", 1)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

login_manager=LoginManager()
login_manager.init_app(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)
##CONFIGURE TABLES


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('blog_user.id'),nullable=False)
    parent = relationship('User', back_populates='children', lazy=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(450), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(1000), nullable=False)
    children=relationship('Comment',back_populates='parent2',lazy=True)

class User(db.Model,UserMixin):
    __tablename__="blog_user"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(120),unique=True)
    password=db.Column(db.String(1000))
    children=relationship('BlogPost',back_populates='parent',lazy=True)
    children2=relationship('Comment',back_populates='parent',lazy=True)

class Comment(db.Model,UserMixin):
    __tablename__="comments"
    id=db.Column(db.Integer,primary_key=True)
    comment_author_id = db.Column(db.Integer, db.ForeignKey('blog_user.id'),nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    parent=relationship('User',back_populates='children2',lazy=True)
    parent2=relationship('BlogPost',back_populates='children',lazy=True)
    text=db.Column(db.Text,nullable=False)

db.create_all()

pas=None
'''THIS ISTHE TEXTBOOK WAY'''
def admin_only(function):
    @wraps(function)
    def decorated_func(*args,**kwargs):
        if current_user.id == 1 and current_user.is_authenticated:
            return function(*args,**kwargs)

        return abort(403,"You are not authorized")
    return decorated_func
'''BUT THIS ALSO WORKS'''
# def admin_only(f):
#
#     def wrapper_func():
#         if current_user.id==1:
#             return f
#         return abort(403,"you don't have permission")
#     return wrapper_func
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    print(current_user.is_authenticated)

    return render_template("index.html", all_posts=posts,logged_in=current_user.is_authenticated,c_user=current_user,user=User)


@app.route('/register',methods=['GET','POST'])
def register():
    global pas
    form=RegisterForm()
    if form.validate_on_submit():

        user_exist=User.query.filter_by(email=form.email.data).first()
        if user_exist:
            flash('User already exists, login instead')
            return redirect(url_for('login',email=user_exist.email))
        else:
            passw = generate_password_hash(password=form.password.data, method='pbkdf2:sha256', salt_length=8)
            pas = form.password.data
            new_user=User(name=form.name.data,
                          email=form.email.data,
                          password=passw)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login',email=new_user.email))
    return render_template("register.html",form=form)


@app.route('/login',methods=['GET','POST'])
def login():
    email=request.args.get('email')

    form=LoginForm()


    if email:
        print(pas)
        form=LoginForm(email=email,
                       password=pas)

    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password,form.password.data):
            login_user(user=user)
            print(current_user.name)
            return redirect(url_for('get_all_posts'))
        else:
            flash('Email or Password Incorrect!')
            return redirect(url_for('login'))

    return render_template("login.html",form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=['GET','POST'])
@login_required
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comment_id=request.args.get('comment_id')
    cm=Comment.query.all()
    comment_form=CommentForm()

    if comment_form.validate_on_submit():
        new_comment=Comment(comment_author_id=current_user.id,
                            post_id=post_id,
                            text=comment_form.comment.data)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post',post_id=post_id))
    return render_template("post.html", post=requested_post,c_user=current_user,logged_in=True,form=comment_form,comments=cm)


@app.route("/about")
def about():

    return render_template("about.html",logged_in=current_user.is_authenticated)


@app.route("/contact")
@login_required
def contact():
    return render_template("contact.html",logged_in=True)



@app.route("/new-post",methods=["GET","POST"])
@login_required
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>",methods=['GET','POST'])
@login_required
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,

        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user.name
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form,logged_in=True)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='https://fahim0.herokuapp.com/', port=5000,debug=True)
