from flask import render_template, request
from flask.ext.login import login_required

from .. import db
from ..models import Role, User, Post, PlatformSetting, BBS
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, InvalidRequestError
from . import main

from .forms import PlatformSettingForm

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

@main.before_request
def before_request():
    setting = db.session.query(PlatformSetting).one()
    g.platform_setting = setting
    
@main.teardown_request
def teardown_request(exception):
    pass

@main.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename = 'images/paw.ico'))

@main.route('/')
def dash():
    print("/dash")
    
    try:
        bbs = db.session.query(BBS).filter(BBS.id == 1).one()
    
        if g.platform_setting.mode == 0:
            user = db.session.query(User).filter(User.id == g.platform_setting.main_blog).one()
            return redirect(url_for('main.blog', name = user.name))
        else:
            return redirect(url_for('main.bbs', name = bbs.name))
    
    except NoResultFound:
        print("NoResultFound")
        return render_template("404.html")
        
    except MultipleResultsFound:
        print("MultipleResultsFound")
        return render_template("404.html")

@main.route('/mainbbs')
def mainbbs():
    print("/mainbbs")
    
    try:
        bbs = db.session.query(BBS).filter(BBS.id == 1).one()
        return redirect(url_for('main.bbs', name = bbs.name))
    
    except NoResultFound:
        print("NoResultFound")
        return render_template("404.html")
        
    except MultipleResultsFound:
        print("MultipleResultsFound")
        return render_template("404.html")

@main.route('/mainblog')
def mainblog():
    print("/mainblog")
    
    try:
        user = db.session.query(User).filter(User.id == g.platform_setting.main_blog).one()
        return redirect(url_for('main.blog', name = user.name))
    
    except NoResultFound:
        print("NoResultFound")
        return render_template("404.html")
        
    except MultipleResultsFound:
        print("MultipleResultsFound")
        return render_template("404.html")

@main.route('/about')
def about():
    print("/about")
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
    
    return json.dumps(thread, cls = ComplexEncoder)

@main.route('/post/t/<title>')
def post_title(title):
    try:
        post = db.session.query(Post).filter(Post.title == title).filter(Post.is_comment == False).one()
        return render_post(post)

    except NoResultFound:
        print("NoResultFound")
        return render_template("wrongpost.html")
        
    except MultipleResultsFound:
        print("MultipleResultsFound")
        return "ERROR"
    
@main.route('/post/i/<id>')
def post_id(id):
    try:
        post = db.session.query(Post).filter(Post.id == id).filter(Post.is_comment == False).one()
        return render_post(post)
    
    except NoResultFound:
        print("NoResultFound")
        return render_template("wrongpost.html")
        
    except MultipleResultsFound:
        print("MultipleResultsFound")
        return "ERROR"

def render_post(post):
    try:
        post.view_count += 1
        db.session.commit()
    
    except:
        db.session.rollback()

    can_reply = 0
    
    if current_user.is_authenticated() and current_user.confirmed:
        can_reply = 1
        
    ancestor_post_id = post.ancestor_post_id
    if ancestor_post_id == 0:
        ancestor_post_id = post.id
        
    parent_post_id = post.parent_post_id
    if parent_post_id == 0:
        parent_post_id = post.id
        
        
    return render_template("post.html", post_id = post.id, parent_post_id = parent_post_id, ancestor_post_id = ancestor_post_id, can_reply = can_reply)

@main.route('/blog/<name>')
def blog(name):
    print("blog %s" % name)
    content = []

    try:
        content = db.session.query(Post, User).filter(Post.author_id == User.id).filter(User.name == name).filter(Post.is_comment == False).order_by(Post.post_time.desc()).all()
        
        return render_template("blog.html", content = content)
        
    except NoResultFound:
        print("NoResultFound")
        return render_template("blog.html", content = content)
    
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
    owner_bbs = int(request.form['owner_bbs'])
    owner_blog = int(request.form['owner_blog'])
    
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
        comment_count = comment_count, like_count = like_count, dislike_count = dislike_count, owner_bbs = owner_bbs)
    #print(post.post_time)
    try:
        db.session.add(post)
        db.session.commit()
        
        if not is_comment:
            post.parent_post_id = 0 #post.id
            post.ancestor_post_id = 0 #post.id
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

@main.route('/dashboard', methods = ['POST', 'GET'])
@login_required
def dashboard():
    if not current_user.is_god():
        return render_template("500.html")
    
    setting = g.platform_setting
    form = PlatformSettingForm(mode = setting.mode)
    
    if form.validate_on_submit():
        setting.window_title = form.window_title.data
        setting.page_title = form.page_title.data
        setting.mode = form.mode.data
        setting.main_blog = form.main_blog.data
        setting.show_blog_link = form.show_blog_link.data
        db.session.commit()
    else:
        form.window_title.data = setting.window_title
        form.page_title.data = setting.page_title
        form.main_blog.data = setting.main_blog
        form.show_blog_link.data = setting.show_blog_link
        
    return render_template("dashboard.html", form = form)

@main.route('/getbbstree', methods = ['POST'])
@login_required
def getbbstree():
    all_bbs = db.session.query(BBS).all()
    
    group = []
    
    for bbs in all_bbs:
        group.append(dict(zip(['id', 'pId', 'name', ''], [bbs.id, bbs.parent_bbs, bbs.name])))
        
    return json.dumps(group)

@main.route('/createbbs', methods = ['POST'])
@login_required
def createbbs():
    try:
        name = request.form["name"]
        
        parent_bbs = int(request.form["parent_bbs"])
        bbs = BBS(name, parent_bbs)
        
        db.session.add(bbs)
        db.session.commit()
        
        reply = {'result':'OK', 'id':bbs.id}
        return json.dumps(reply)
    
    except IntegrityError:
        db.session.rollback()
        print("createbbs IntegrityError")
        print(type(sys.exc_info()[1]))
        print(sys.exc_info()[1])
        reply = {'result':'BBS with the same name exists!', 'id':0}
        return json.dumps(reply)
    
    except:
        db.session.rollback()
        print("createbbs ERROR")
        print(type(sys.exc_info()[1]))
        print(sys.exc_info()[1])
        reply = {'result':'ERROR', 'id':0}
        return json.dumps(reply)
    
@main.route('/renamebbs', methods = ['POST'])
@login_required
def renamebbs():
    print("/renamebbs")
    try:
        name = request.form["name"]
        id = int(request.form["id"])
        
        bbs = db.session.query(BBS).filter(BBS.id == id).one()
        
        bbs.name = name
        db.session.commit()
        
        reply = {'result':'OK'}
        return json.dumps(reply)
    
    except NoResultFound:
        print("renamebbs NoResultFound")
        reply = {'result':'NoResultFound'}
    except MultipleResultsFound:
        print("renamebbs MultipleResultsFound")
        reply = {'result':'MultipleResultsFound'}
    except IntegrityError:
        db.session.rollback()
        print("renamebbs IntegrityError")
        print(type(sys.exc_info()[1]))
        print(sys.exc_info()[1])
        reply = {'result':'IntegrityError'}
    except:
        db.session.rollback()
        print("renamebbs except")
        print(type(sys.exc_info()[1]))
        print(sys.exc_info()[1])
        reply = {'result':'except'}
    finally:
        return json.dumps(reply)
    
    
@main.route('/deletebbs', methods = ['POST'])
@login_required
def deletebbs():
    print("deletebbs")
    return "no"
'''
    try:
        id = int(request.form["id"])
        
        bbs = db.session.query(BBS).filter(BBS.id == id).delete()
        db.session.commit()
        
        reply = {'result':'OK'}
        return json.dumps(reply)
    
    except NoResultFound:
        print("renamebbs NoResultFound")
        reply = {'result':'NoResultFound'}
    except MultipleResultsFound:
        print("renamebbs MultipleResultsFound")
        reply = {'result':'MultipleResultsFound'}
    except IntegrityError:
        db.session.rollback()
        print("renamebbs IntegrityError")
        print(type(sys.exc_info()[1]))
        print(sys.exc_info()[1])
        reply = {'result':'IntegrityError'}
    except:
        db.session.rollback()
        print("renamebbs except")
        print(type(sys.exc_info()[1]))
        print(sys.exc_info()[1])
        reply = {'result':'except'}
    finally:
        return json.dumps(reply)
'''

@main.route('/bbs/<name>')
def bbs(name):
    print("/bbs %s" % name)
    try:
        bbs = db.session.query(BBS).filter(BBS.name == name).one()
        
    except NoResultFound:
        print("NoResultFound")
        return render_template("404.html")
        
    except MultipleResultsFound:
        print("MultipleResultsFound")
        return render_template("500.html")
    
    try:
        children_bbs = db.session.query(BBS).filter(BBS.parent_bbs == bbs.id).all()
        
        parent_bbs = None
        
        if bbs.parent_bbs == 0:
            parent_bbs = bbs
        else:
            parent_bbs = db.session.query(BBS).filter(BBS.id == bbs.parent_bbs).one()
        
        can_reply = 0
    
        if current_user.is_authenticated() and current_user.confirmed:
            can_reply = 1
            
        return render_template("bbs.html", can_reply = can_reply, bbs = bbs, parent_bbs = parent_bbs, children_bbs = children_bbs)

    except:
        print("bbs except 1")
        print(type(sys.exc_info()[1]))
        print(sys.exc_info()[1])

    return render_template("500.html")
    
@main.route('/getbbsposts', methods = ['POST'])
def getbbsposts():
    print("/getbbsposts")
    
    id = int(request.form["bbs_id"])
    
    try:
        bbs = db.session.query(BBS).filter(BBS.id == id).one()
        
    except NoResultFound:
        print("NoResultFound")
        return render_template("404.html")
        
    except MultipleResultsFound:
        print("MultipleResultsFound")
        return "MultipleResultsFound"
        
    bbs_posts = []
    
    try:
        content = db.session.query(Post, User).filter(Post.author_id == User.id).filter(Post.owner_bbs == bbs.id).filter(Post.is_comment == False).order_by(Post.post_time.desc()).all()
        
        for row in content:
            post_dict = {'id':row.Post.id, 'parent_post_id':row.Post.parent_post_id, 'view_count':row.Post.view_count,
                 'post_time':row.Post.post_time,
                 'comment_count':row.Post.comment_count,
                 'title':row.Post.title,
                 'body':row.Post.body,
                 'like_count':row.Post.like_count,
                 'dislike_count':row.Post.dislike_count}
            
            author_dict = {'id':row.User.id, 'name':row.User.name}
        
            bbs_posts.append({"post":post_dict, "author":author_dict})
    except:
        print("bbs except 2")
        print(type(sys.exc_info()[1]))
        print(sys.exc_info()[1])
        
    return json.dumps(bbs_posts, cls = ComplexEncoder)