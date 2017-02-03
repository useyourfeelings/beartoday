from app.tool.tools import dbg
dbg('site.py')

import os, json, re, time, sys, html
from datetime import datetime

import config as config
#import app.database.model as dbmodel

from .. import db
from app.database.model import Role, User, Post, PlatformSetting, BBS
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, InvalidRequestError
from sqlalchemy import *#create_engine

from .forms import PlatformSettingForm
from .sources import source_videos

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return json.JSONEncoder.default(self, obj)

#main flask
from flask import Flask, Blueprint, request, g, redirect, url_for, abort, render_template, flash, _app_ctx_stack, make_response

#login module
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user

site_blueprint = Blueprint('site', __name__)

@site_blueprint.before_request
def before_request():
    setting = db.session.query(PlatformSetting).one()
    g.platform_setting = setting
    
    g.config = {}
    g.config['jquery_js_url'] = config.jquery_js_url
    g.config['semantic_js_url'] = config.semantic_js_url
    g.config['semantic_css_url'] = config.semantic_css_url
    g.config['avatar_site'] = config.avatar_site
    g.config['background_image'] = config.background_image
    
@site_blueprint.teardown_request
def teardown_request(exception):
    pass

@site_blueprint.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename = 'images/paw.ico'))

@site_blueprint.route('/')
def dash():
    dbg("/dash")
    
    try:
        bbs = db.session.query(BBS).filter(BBS.id == 1).one()
    
        if g.platform_setting.mode == 0:
            user = db.session.query(User).filter(User.id == g.platform_setting.main_blog).one()
            return redirect(url_for('site.blog', name = user.name))
        else:
            return redirect(url_for('site.bbs', name = bbs.name))
    
    except NoResultFound:
        dbg("NoResultFound")
        return render_template("404.html")
        
    except MultipleResultsFound:
        dbg("MultipleResultsFound")
        return render_template("404.html")

@site_blueprint.route('/mainbbs')
def mainbbs():
    dbg("/mainbbs")
    
    try:
        bbs = db.session.query(BBS).filter(BBS.id == 1).one()
        return redirect(url_for('site.bbs', name = bbs.name))
    
    except NoResultFound:
        dbg("NoResultFound")
        return render_template("404.html")
        
    except MultipleResultsFound:
        dbg("MultipleResultsFound")
        return render_template("404.html")

@site_blueprint.route('/mainblog')
def mainblog():
    dbg("/mainblog")
    
    try:
        user = db.session.query(User).filter(User.id == g.platform_setting.main_blog).one()
        return redirect(url_for('site.blog', name = user.name))
    
    except NoResultFound:
        dbg("NoResultFound")
        return render_template("404.html")
        
    except MultipleResultsFound:
        dbg("MultipleResultsFound")
        return render_template("404.html")

@site_blueprint.route('/about')
def about():
    dbg("/about")
    return render_template("about.html")

@site_blueprint.route('/user/<name>')
def user(name):
    try:
        user = db.session.query(User).filter(User.name == name).one()
    
    except NoResultFound:
        dbg("NoResultFound")
        return render_template("500.html")
        
    except MultipleResultsFound:
        dbg("MultipleResultsFound")
        return render_template("500.html")
    
    return render_template("user.html", user = user)

def build_thread(post):#build thread tree
    dbg("build_thread %d" % post.id)
    
    post_dict = {'id':post.id, 'parent_post_id':post.parent_post_id, 'view_count':post.view_count,
                 'post_time':post.post_time,
                 'comment_count':post.comment_count,
                 'title':post.title,
                 'body':post.body,
                 'like_count':post.like_count,
                 'dislike_count':post.dislike_count}
    
    author = post.author
    
    author_dict = {'id':author.id, 'name':author.name, 'avatar_hash':author.avatar_hash}
    
    child_posts = db.session.query(Post).filter(Post.parent_post_id == post.id).\
                                        filter(Post.id != post.id).all()
    
    child_posts_list = []
    for child_post in child_posts:
        child_posts_list.append(build_thread(child_post))

    return {'post':post_dict, 'author':author_dict, 'child_posts':child_posts_list}

@site_blueprint.route('/getthread', methods = ['POST'])
def getthread():
    post_id = int(request.form['post_id'])
    dbg('getthread %d' % post_id)
    try:
        post = db.session.query(Post).filter(Post.id == post_id).one()
    except NoResultFound:
        dbg("NoResultFound")
        return render_template("wrongpost.html")
    except MultipleResultsFound:
        dbg("MultipleResultsFound")
        return "ERROR"
    
    thread = build_thread(post)
    
    return json.dumps(thread, cls = ComplexEncoder)

@site_blueprint.route('/post/t/<title>')
def post_title(title):
    try:
        post = db.session.query(Post).filter(Post.title == title).filter(Post.is_comment == False).one()
        return render_post(post)

    except NoResultFound:
        dbg("NoResultFound")
        return render_template("wrongpost.html")
        
    except MultipleResultsFound:
        dbg("MultipleResultsFound")
        return "ERROR"
    
@site_blueprint.route('/post/i/<id>')
def post_id(id):
    try:
        post = db.session.query(Post).filter(Post.id == id).filter(Post.is_comment == False).one()
        return render_post(post)
    
    except NoResultFound:
        dbg("NoResultFound")
        return render_template("wrongpost.html")
        
    except MultipleResultsFound:
        dbg("MultipleResultsFound")
        return "ERROR"

def render_post(post):
    try:
        post.view_count += 1
        db.session.commit()
    
    except:
        db.session.rollback()

    can_reply = 0
    
    if current_user.is_authenticated and current_user.confirmed:
        can_reply = 1
        
    ancestor_post_id = post.ancestor_post_id
    if ancestor_post_id == 0:
        ancestor_post_id = post.id
        
    parent_post_id = post.parent_post_id
    if parent_post_id == 0:
        parent_post_id = post.id

    
    user_is_author = 0
    if current_user.get_id() == post.author_id:
        user_is_author = 1
        
    return render_template("post.html", user_is_author = user_is_author, owner_bbs = post.owner_bbs, post_id = post.id, parent_post_id = parent_post_id, ancestor_post_id = ancestor_post_id, can_reply = can_reply, window_title = post.title + " - " + g.platform_setting.window_title)

@site_blueprint.route('/blog/<name>')
def blog(name):
    dbg("blog %s" % name)
    content = []

    try:
        content = db.session.query(Post, User).filter(Post.author_id == User.id).filter(User.name == name).filter(Post.is_comment == False).filter(Post.owner_blog == Post.author_id).order_by(Post.post_time.desc()).all()
        
        return render_template("blog.html", content = content)
        
    except NoResultFound:
        dbg("NoResultFound")
        return render_template("blog.html", content = content)
    
    return "ERROR"

@site_blueprint.route('/compose', methods = ['POST', 'GET'])
@login_required
def compose():
    if not current_user.confirmed:
        return redirect(url_for('site.user', name = current_user.name))
    
    return render_template("compose.html")

@site_blueprint.route('/savepost', methods = ['POST'])
@login_required
def savepost():
    title = request.form['title']
    body = request.form['body']
    parent_post_id = int(request.form['parent_post_id'])
    ancestor_post_id = int(request.form['ancestor_post_id'])
    is_comment = int(request.form['is_comment'])
    owner_bbs = int(request.form['owner_bbs'])
    owner_blog = int(request.form['owner_blog'])
    editor_mode = request.form['editor_mode']
    original_post = int(request.form['original_post'])
    
    if editor_mode == "edit":
        try:
            post = db.session.query(Post).filter(Post.id == original_post).one()
            #post.title = title  title is not allowed to change
            post.body = body
            post.last_editing_time = datetime.utcnow()
            
            db.session.commit()
            dbg(post.body)
            return "OK"
            
        except Exception:
            dbg("savepost edit ERROR")
            db.session.rollback()
            dbg(type(sys.exc_info()[1]))
            dbg(sys.exc_info()[1])
            return "ERROR"
        
        return "ERROR"
    
    else:#new post
        if is_comment:
            is_comment = True
        else:
            is_comment = False
        author_id = current_user.get_id()
        view_count = 0
        comment_count = 0
        like_count = 0
        dislike_count = 0

        post = Post(title = title, body = body, author_id = author_id,\
            post_time = datetime.utcnow(), last_editing_time = datetime.utcnow(), parent_post_id = parent_post_id,\
            ancestor_post_id = ancestor_post_id, is_comment = is_comment, view_count = view_count, \
            comment_count = comment_count, like_count = like_count, dislike_count = dislike_count, \
            owner_blog = owner_blog, owner_bbs = owner_bbs, last_reply_time = datetime.utcnow(),\
            last_commenter = author_id)
        #dbg(post.post_time)
        try:
            db.session.add(post)
            db.session.commit()
            
            if not is_comment:
                post.parent_post_id = 0 #post.id
                post.ancestor_post_id = 0 #post.id
            else:
                ancestor_post = db.session.query(Post).filter(Post.id == ancestor_post_id).one()
                ancestor_post.comment_count += 1
                ancestor_post.last_reply_time = datetime.utcnow()
                ancestor_post.last_commenter = author_id
            db.session.commit()
            
            #dbg(post.title)
            #dbg(post.author_id)
            #dbg(post.id)
            #dbg(post.like_count)
            #dbg(post.parent_post_id)
            #dbg(post.ancestor_post_id)
            #dbg(post.is_comment)
            #dbg(post.comment_count)
            return "OK"
        except InvalidRequestError:
            dbg("savepost InvalidRequestError")
            dbg(type(sys.exc_info()[1]))
            dbg(sys.exc_info()[1])
            return "ERROR"
        except Exception:
            dbg("savepost ERROR")
            dbg(type(sys.exc_info()[1]))
            dbg(sys.exc_info()[1])
            return "ERROR"
    
    return "ERROR"

@site_blueprint.route('/dashboard', methods = ['POST', 'GET'])
@login_required
def dashboard():
    if not current_user.is_god():
        return render_template("500.html")
    
    
    setting = g.platform_setting
    form = PlatformSettingForm(mode = setting.mode)
        
    if form.validate_on_submit():
        try:
            setting.window_title = form.window_title.data
            setting.page_title = form.page_title.data
            setting.mode = form.mode.data
            setting.main_blog = form.main_blog.data
            setting.show_blog_link = form.show_blog_link.data
            setting.show_about_link = form.show_about_link.data
            setting.bbs_posts_per_page = form.bbs_posts_per_page.data
            
            db.session.commit()
        
        except Exception:
            dbg("saverightinfo ERROR")
            dbg(type(sys.exc_info()[1]))
            dbg(sys.exc_info()[1])
            return "ERROR"
    
    else:
        form.window_title.data = setting.window_title
        form.page_title.data = setting.page_title
        form.main_blog.data = setting.main_blog
        form.show_blog_link.data = setting.show_blog_link
        form.show_about_link.data = setting.show_about_link
        form.bbs_posts_per_page.data = setting.bbs_posts_per_page
            
    return render_template("dashboard.html", form = form)

@site_blueprint.route('/saverightinfo', methods = ['POST'])
@login_required
def saverightinfo():
    try:
        title = request.form['title']
        body = request.form['body']
        
        setting = g.platform_setting
        setting.right_info_title = title
        setting.right_info = body
        db.session.commit()
        return "OK"
    except Exception:
        dbg("saverightinfo ERROR")
        dbg(type(sys.exc_info()[1]))
        dbg(sys.exc_info()[1])
        return "ERROR"
    
    return "ERROR"

@site_blueprint.route('/getrightinfo', methods = ['POST'])
def getrightinfo():
    try:
        reply = {}
        setting = g.platform_setting
        reply['title'] = setting.right_info_title
        reply['body'] = setting.right_info
        
        return json.dumps(reply)
    except Exception:
        dbg("getrightinfo ERROR")
        dbg(type(sys.exc_info()[1]))
        dbg(sys.exc_info()[1])
        return "ERROR"
    
    return "ERROR"

@site_blueprint.route('/getbbstree', methods = ['POST'])
def getbbstree():
    all_bbs = db.session.query(BBS).all()
    
    group = []
    
    for bbs in all_bbs:
        group.append(dict(zip(['id', 'pId', 'name', ''], [bbs.id, bbs.parent_bbs, bbs.name])))
        
    return json.dumps(group)

@site_blueprint.route('/createbbs', methods = ['POST'])
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
        dbg("createbbs IntegrityError")
        dbg(type(sys.exc_info()[1]))
        dbg(sys.exc_info()[1])
        reply = {'result':'BBS with the same name exists!', 'id':0}
        return json.dumps(reply)
    
    except:
        db.session.rollback()
        dbg("createbbs ERROR")
        dbg(type(sys.exc_info()[1]))
        dbg(sys.exc_info()[1])
        reply = {'result':'ERROR', 'id':0}
        return json.dumps(reply)
    
@site_blueprint.route('/renamebbs', methods = ['POST'])
@login_required
def renamebbs():
    dbg("/renamebbs")
    try:
        name = request.form["name"]
        id = int(request.form["id"])
        
        bbs = db.session.query(BBS).filter(BBS.id == id).one()
        
        bbs.name = name
        db.session.commit()
        
        reply = {'result':'OK'}
        return json.dumps(reply)
    
    except NoResultFound:
        dbg("renamebbs NoResultFound")
        reply = {'result':'NoResultFound'}
    except MultipleResultsFound:
        dbg("renamebbs MultipleResultsFound")
        reply = {'result':'MultipleResultsFound'}
    except IntegrityError:
        db.session.rollback()
        dbg("renamebbs IntegrityError")
        dbg(type(sys.exc_info()[1]))
        dbg(sys.exc_info()[1])
        reply = {'result':'IntegrityError'}
    except:
        db.session.rollback()
        dbg("renamebbs except")
        dbg(type(sys.exc_info()[1]))
        dbg(sys.exc_info()[1])
        reply = {'result':'except'}
    finally:
        return json.dumps(reply)
    
    
@site_blueprint.route('/deletebbs', methods = ['POST'])
@login_required
def deletebbs():
    dbg("deletebbs")
    return "no"
'''
    try:
        id = int(request.form["id"])
        
        bbs = db.session.query(BBS).filter(BBS.id == id).delete()
        db.session.commit()
        
        reply = {'result':'OK'}
        return json.dumps(reply)
    
    except NoResultFound:
        dbg("renamebbs NoResultFound")
        reply = {'result':'NoResultFound'}
    except MultipleResultsFound:
        dbg("renamebbs MultipleResultsFound")
        reply = {'result':'MultipleResultsFound'}
    except IntegrityError:
        db.session.rollback()
        dbg("renamebbs IntegrityError")
        dbg(type(sys.exc_info()[1]))
        dbg(sys.exc_info()[1])
        reply = {'result':'IntegrityError'}
    except:
        db.session.rollback()
        dbg("renamebbs except")
        dbg(type(sys.exc_info()[1]))
        dbg(sys.exc_info()[1])
        reply = {'result':'except'}
    finally:
        return json.dumps(reply)
'''


#return redirect(url_for('site.blog', name = user.name))

@site_blueprint.route('/bbs/<name>')
def bbs(name):
    #dbg("/bbs %s" % name)
    
    page = request.args.get('page', 1, type = int)
    
    try:
        bbs = db.session.query(BBS).filter(BBS.name == name).one()
        
    except NoResultFound:
        dbg("NoResultFound")
        return render_template("404.html")
        
    except MultipleResultsFound:
        dbg("MultipleResultsFound")
        return render_template("500.html")
    
    try:
        children_bbs = db.session.query(BBS).filter(BBS.parent_bbs == bbs.id).all()
        
        parent_bbs = None
        
        if bbs.parent_bbs == 0:
            parent_bbs = bbs
        else:
            parent_bbs = db.session.query(BBS).filter(BBS.id == bbs.parent_bbs).one()
        
        can_reply = 0
    
        if current_user.is_authenticated and current_user.confirmed:
            can_reply = 1
            
        return render_template("bbs.html", page = page, can_reply = can_reply, bbs = bbs, parent_bbs = parent_bbs, children_bbs = children_bbs)

    except:
        dbg("bbs except 1")
        dbg(type(sys.exc_info()[1]))
        dbg(sys.exc_info()[1])

    return render_template("500.html")
    
@site_blueprint.route('/getbbsposts', methods = ['POST'])
def getbbsposts():
    dbg("/getbbsposts")
    
    id = int(request.form["bbs_id"])
    page = int(request.form["page"])
    
    page_size = g.platform_setting.bbs_posts_per_page
    if page < 1:
        page = 1
    
    dbg('page %d page_size %d' % (page, page_size))
    
    try:
        bbs = db.session.query(BBS).filter(BBS.id == id).one()
        
    except NoResultFound:
        dbg("NoResultFound")
        return render_template("404.html")
        
    except MultipleResultsFound:
        dbg("MultipleResultsFound")
        return "MultipleResultsFound"
        
    reply = {}
    
    
    try:
        #################page bar
        
        pagebar = {}
        
        buttons = []
        
        total_posts = db.session.query(Post).filter(Post.owner_bbs == bbs.id).filter(Post.is_comment == False).order_by(Post.last_reply_time.desc()).count()
        
        total_pages = int(total_posts / page_size)
        
        if total_posts % page_size:
            total_pages+= 1
            
        if page > total_pages:
            page = total_pages
            
        pagebar['current_page'] = page
        
        prev_page = page - 1
        if prev_page < 1:
            prev_page = 1
        buttons.append({'title':'上一页', 'page':prev_page})
        
        start = page - 3
        if start <= 2:
            for p in range(1, page + 1):
                buttons.append({'title':str(p), 'page':p})
        else:
            buttons.append({'title':'1', 'page':1})
            buttons.append({'title':'...', 'page':page})
            for p in range(start, page + 1):
                buttons.append({'title':str(p), 'page':p})
                
        end = page + 3
        if end >= total_pages - 1:
            for p in range(page + 1, total_pages + 1):
                buttons.append({'title':str(p), 'page':p})
        else:
            for p in range(page + 1, end + 1):
                buttons.append({'title':str(p), 'page':p})
            buttons.append({'title':'...', 'page':page})
            buttons.append({'title':str(total_pages), 'page':total_pages})
            
        next_page = page+ + 1
        if next_page > total_pages:
            next_page = total_pages
        buttons.append({'title':'下一页', 'page':next_page})
            
        pagebar['buttons'] = buttons
            
        reply['pagebar'] = pagebar
        
        #########posts
        query = db.session.query(Post, User).filter(Post.author_id == User.id)\
            .filter(Post.owner_bbs == bbs.id)\
            .filter(Post.is_comment == False)\
            .order_by(Post.last_reply_time.desc()).offset(page_size * (page - 1)).limit(page_size)
        
        #dbg(query)
        
        content = query.all()
        
        posts = []
        
        for row in content:
            last_commenter = db.session.query(User).filter(row.Post.last_commenter == User.id).one()
        
            post_dict = {'id':row.Post.id, 'parent_post_id':row.Post.parent_post_id, 'view_count':row.Post.view_count,
                 'post_time':row.Post.post_time,
                 'comment_count':row.Post.comment_count,
                 'title':row.Post.title,
                 'body':row.Post.body,
                 'like_count':row.Post.like_count,
                 'dislike_count':row.Post.dislike_count,
                 'last_commenter':last_commenter.name,
                 'last_reply_time':row.Post.last_reply_time}
            
            author_dict = {'id':row.User.id, 'name':row.User.name, 'avatar_hash':row.User.avatar_hash}
        
            posts.append({"post":post_dict, "author":author_dict})
            
        reply['posts'] = posts
        
    except:
        dbg("bbs except 2")
        dbg(type(sys.exc_info()[1]))
        dbg(sys.exc_info()[1])
        
    return json.dumps(reply, cls = ComplexEncoder)

@site_blueprint.route('/gallery')
def gallery():
    dbg("/gallery")
    dbg(os.getcwd())
    all_files = os.listdir(os.getcwd() + '/app' + config.gallery_dir)
    dbg(all_files)
    pictures = []
    for f in sorted(all_files, reverse = True):
        pictures.append(config.gallery_dir + f)
    return render_template("gallery.html", pictures = pictures)

@site_blueprint.route('/videos')
def videos():
    dbg("/videos")
    return render_template("videos.html", videos = source_videos)
