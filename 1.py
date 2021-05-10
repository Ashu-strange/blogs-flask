from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename
import os
import json
import math

with open ('config.json','r') as c:
    params = json.load(c)['params']

localhost = params['local_server']

app = Flask(__name__)
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = 'True',
    MAIL_USERNAME = params['email_address'],
    MAIL_PASSWORD = params['email_password']
)
app.config['SECRET_KEY'] = 'the random string'    

mail = Mail(app)

if(localhost):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(12), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    msg = db.Column(db.String(80), nullable=False)
    date = db.Column(db.String(120), nullable=True)

class posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)

@app.route("/")
def home():
    Posts = posts.query.filter_by().all()
    last = math.ceil(len(Posts)/int(params['blog_no']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1

    page = int(page)
    Posts = Posts[(page-1)*int(params['blog_no']):(page-1)*int(params['blog_no'])+int(params['blog_no'])]
    
    if(page == 1):
        prev = "#"
        next = "?page="+str(page+1)
    elif(page == last):
        next = "#"
        prev = "?page="+str(page-1)
    else:
        prev = "?page="+str(page-1)
        next = "?page="+str(page+1)
    
    return render_template('index.html', params=params, Posts = Posts, prev=prev, next = next)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/delete/<s_no>")
def delete(s_no):
    if('user' in session and session['user'] == params['u_name']):
        post = posts.query.filter_by(sno = s_no).first()
        db.session.delete(post)
        db.session.commit()
    Posts = posts.query.all()
    return render_template('dashboard.html', params=params, posts=Posts)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/upload", methods=['GET','POST'])
def upload():
    if('user' in session and session['user'] == params['u_name']):
        if(request.method == 'POST'):
            f = request.files['file']
            f.save(os.path.join(params['location'],secure_filename(f.filename)))
            return "FILE UPLOADED"
    return render_template('login.html', params=params)

@app.route("/dashboard", methods=['GET','POST'])
def login():
    Posts = posts.query.all()
    if ('user' in session and session['user'] == params['u_name']):
        return render_template('dashboard.html', params=params, posts=Posts)

    if(request.method == 'POST'):
        username = request.form.get('uname')
        password = request.form.get('pass')
        if(username == params['u_name'] and password == params['pass']):
            session['user'] = username
            return render_template('dashboard.html', params=params, posts=Posts)
        return render_template('login.html', params=params)
    else:
        return render_template('login.html', params=params)

@app.route("/post/<post_slug>/", methods=['GET'])
def post_route(post_slug):
    post = posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/contact" , methods=['GET','POST'])
def contacts():
    if(request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        msg = request.form.get('message')

        entry = contact(name=name, phone=phone, email=email, msg=msg, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New msg from '+name,sender='bjh',recipients=[params['email_address']],body = msg)
    return render_template('contact.html', params=params)

@app.route("/edit/<s_no>" , methods=['GET','POST'])
def edit(s_no):
    if ('user' in session and session['user'] == params['u_name']):
        if(request.method == 'POST'):
            title = request.form.get('title')
            content = request.form.get('content')
            slug = request.form.get('slug')
            image = request.form.get('image')

            if(s_no == '0'):
                entry = posts(title=title, content=content, slug=slug, img_file=image, date=datetime.now())
                db.session.add(entry)
                db.session.commit()
                Posts = posts.query.all()
                return render_template('dashboard.html', params=params, posts=Posts)
            
            else:
                post = posts.query.filter_by(sno=s_no).first()
                post.title = title
                post.content = content
                post.slug = slug
                post.img_file = image
                db.session.commit()
                return redirect('/edit/'+s_no)
        post = posts.query.filter_by(sno=s_no).first()
        return render_template('edit.html', params=params, sno=s_no)
    return render_template('login.html', params=params)

app.run(debug=True)