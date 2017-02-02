from app.tool.tools import dbg
dbg('auth.py')

import config as config

from flask import render_template, redirect, request, url_for, flash, g
from flask_login import login_user, logout_user, login_required, current_user

from .. import db
from app.database.model import User, PlatformSetting
from app.tool.email import send_email
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm

from datetime import datetime

import hashlib

from flask import Blueprint
auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.before_request
def before_request():
    setting = db.session.query(PlatformSetting).one()
    g.platform_setting = setting
    
    g.config = {}
    g.config['jquery_js_url'] = config.jquery_js_url
    g.config['semantic_js_url'] = config.semantic_js_url
    g.config['semantic_css_url'] = config.semantic_css_url
    g.config['background_image'] = config.background_image
    
@auth_blueprint.before_app_request
def before_request():
    if current_user.is_authenticated:
        pass
        #current_user.ping()
        '''if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.':
            dbg("redirect(url_for('auth.unconfirmed')")
            return redirect(url_for('auth.unconfirmed'))'''
        #if not current_user.confirmed and request.endpoint[:5] != 'auth.':
        #    flash('check your email and confirm your account', 'not_confirmed')
            #return redirect(url_for('auth.unconfirmed'))


@auth_blueprint.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous() or current_user.confirmed:
        return redirect(url_for('site.dash'))
    return render_template('auth/unconfirmed.html')


@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    dbg("xcc login")
    if form.validate_on_submit():
        dbg("xcc login submit")
        user = User.query.filter_by(email=form.email_or_name.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            user.last_seen_time = datetime.utcnow()
            db.session.commit()
            return redirect(request.args.get('next') or url_for('site.dash'))
        else:
            user = User.query.filter_by(name=form.email_or_name.data).first()
            if user is not None and user.verify_password(form.password.data):
                login_user(user, form.remember_me.data)
                user.last_seen_time = datetime.utcnow()
                db.session.commit()
                return redirect(request.args.get('next') or url_for('site.dash'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('site.dash'))


@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    name=form.username.data,
                    password=form.password.data,
                    registration_time = datetime.utcnow(),
                    last_seen_time = datetime.utcnow())
        user.confirmed = True;
        user.avatar_hash = hashlib.md5(form.email.data.encode('utf-8')).hexdigest()
        db.session.add(user)
        db.session.commit()
        #token = user.generate_confirmation_token()
        #send_email(user.email, 'Confirm Your Account',
        #           'auth/email/confirm', user=user, token=token)
        #flash('A confirmation email has been sent to you by email.')
        flash('log in please!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth_blueprint.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('site.dash'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('site.dash'))


@auth_blueprint.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('site.dash'))


@auth_blueprint.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('Your password has been updated.')
            return redirect(url_for('site.dash'))
        else:
            flash('Invalid password.')
    return render_template("auth/change_password.html", form=form)


@auth_blueprint.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous():
        return redirect(url_for('site.dash'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash('An email with instructions to reset your password has been '
              'sent to you.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth_blueprint.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous():
        return redirect(url_for('site.dash'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('site.dash'))
        if user.reset_password(token, form.password.data):
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('site.dash'))
    return render_template('auth/reset_password.html', form=form)


@auth_blueprint.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, 'Confirm your email address',
                       'auth/email/change_email',
                       user=current_user, token=token)
            flash('An email with instructions to confirm your new email '
                  'address has been sent to you.')
            return redirect(url_for('site.dash'))
        else:
            flash('Invalid email or password.')
    return render_template("auth/change_email.html", form=form)


@auth_blueprint.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash('Your email address has been updated.')
    else:
        flash('Invalid request.')
    return redirect(url_for('site.dash'))
