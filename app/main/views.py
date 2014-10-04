from flask import render_template, request
from flask.ext.login import login_required

from .. import db
from ..models import Role, User, Post
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, InvalidRequestError
from . import main

from sqlalchemy import *#create_engine

import json, re, time, sys, html

from datetime import datetime

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return json.JSONEncoder.default(self, obj)

#main flask
from flask import Flask, request, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack

#login module
from flask_login import (LoginManager, UserMixin, login_required, login_user,
                             logout_user, make_secure_token, current_user)

GOD_ID = 1

@main.route('/')
#@login_required
def dash():
    print("xcc /")
    return redirect(url_for('main.index'))

@main.route('/about')
#@login_required
def about():
    print("xcc /about")
    return render_template("about.html")

@main.route('/user/<name>')
def user(name):
    try:
        user = db.session.query(User).filter(User.name == name).one()
    
    except NoResultFound:
        print("NoResultFound")
        return render_template("user.html", user = user)
        
    except MultipleResultsFound:
        print("MultipleResultsFound")
        return "ERROR"
    
    return render_template("user.html", user = user)

def build_thread(post):#build thread tree
    print("build_thread %d" % post.id)
    
    post_dict = {'id':post.id, 'parent_post_id':post.parent_post_id, 'view_count':post.view_count,
                 'post_time':post.post_time,
                 'comment_count':post.comment_count,
                 'title':post.title,
                 'body':post.body,
                 'like_count':post.like_count,
                 'dislike_count':post.dislike_count}
    
    author = post.author
    
    author_dict = {'id':author.id, 'name':author.name}
    
    child_posts = db.session.query(Post).filter(Post.parent_post_id == post.id).\
                                        filter(Post.id != post.id).all()
    
    child_posts_list = []
    for child_post in child_posts:
        #print('buid %d for %d type %s' % (child_post.id, post.id, type(child_post)))
        child_posts_list.append(build_thread(child_post))

    return {'post':post_dict, 'author':author_dict, 'child_posts':child_posts_list}

@main.route('/getthread', methods = ['POST'])
def getthread():
    post_id = int(request.form['post_id'])
    print('getthread %d' % post_id)
    try:
        post = db.session.query(Post).filter(Post.id == post_id).one()
    except NoResultFound:
        print("NoResultFound")
        return render_template("wrongpost.html")
    except MultipleResultsFound:
        print("MultipleResultsFound")
        return "ERROR"
    
    thread = build_thread(post)
    print(thread)
    
    return json.dumps(thread, cls = ComplexEncoder)

@main.route('/post/<title>')
def post(title):
    
    print(title)
    try:
        post = db.session.query(Post).filter(Post.title == title).one()
        post.view_count += 1
        db.session.commit()
    
    except NoResultFound:
        print("NoResultFound")
        return render_template("wrongpost.html")
        
    except MultipleResultsFound:
        print("MultipleResultsFound")
        return "ERROR"

    can_reply = 0
    
    if current_user.is_authenticated() and current_user.confirmed:
        can_reply = 1
        
    return render_template("post.html", post_id = post.id, parent_post_id = post.parent_post_id, ancestor_post_id = post.ancestor_post_id, can_reply = can_reply)

@main.route('/index')
#@login_required
def index():
    print("index")
    content = []

    try:
        content = db.session.query(Post, User).filter(Post.author_id == User.id).filter(User.id == GOD_ID).filter(Post.is_comment == False).order_by(Post.post_time.desc()).all()
        
        return render_template("index.html", content = content)
        
    except NoResultFound:
        print("NoResultFound")
        return render_template("index.html", content = content)
    
    return "ERROR"

@main.route('/compose', methods = ['POST', 'GET'])
@login_required
def compose():
    return render_template("compose.html")

@main.route('/savepost', methods = ['POST', 'GET'])
@login_required
def savepost():
    title = request.form['title']
    body = request.form['body']
    parent_post_id = int(request.form['parent_post_id'])
    ancestor_post_id = int(request.form['ancestor_post_id'])
    is_comment = int(request.form['is_comment'])
    if is_comment:
        is_comment = True
    else:
        is_comment = False
    author_id = current_user.get_id()
    view_count = 0
    comment_count = 0
    like_count = 0
    dislike_count = 0

    post = Post(title = title, body = body, author_id = current_user.get_id(),\
        post_time = datetime.utcnow(), last_editing_time = datetime.utcnow(), parent_post_id = parent_post_id,\
        ancestor_post_id = ancestor_post_id, is_comment = is_comment, view_count = view_count, \
        comment_count = comment_count, like_count = like_count, dislike_count = dislike_count)
    #print(post.post_time)
    try:
        db.session.add(post)
        db.session.commit()
        
        if not is_comment:
            post.parent_post_id = post.id
            post.ancestor_post_id = post.id
        else:
            ancestor_post = db.session.query(Post).filter(Post.id == ancestor_post_id).one()
            ancestor_post.comment_count += 1
        db.session.commit()
        
        #print(post.title)
        #print(post.author_id)
        #print(post.id)
        #print(post.like_count)
        #print(post.parent_post_id)
        #print(post.ancestor_post_id)
        #print(post.is_comment)
        #print(post.comment_count)
        return "OK"
    except InvalidRequestError:
        print("savepost InvalidRequestError")
        print(type(sys.exc_info()[1]))
        print(sys.exc_info()[1])
        return "ERROR"
    except Exception:
        print("savepost ERROR")
        print(type(sys.exc_info()[1]))
        print(sys.exc_info()[1])
        return "ERROR"
    
    return "ERROR"