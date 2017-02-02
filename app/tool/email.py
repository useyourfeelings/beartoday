from app.tool.tools import dbg
dbg("email.py")

from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from app import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['BT_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['BT_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    
    dbg('xcc send_email')
    dbg('%r %r' %(app.config['BT_MAIL_SENDER'], to))
    
    msg.charset = 'utf8' #xiongchen20140811
    
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
