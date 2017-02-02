#Hello

Beartoday is a blog/bbs system powered by [**flask**](http://http://flask.pocoo.org/).

##[DEMO](http://bear.today)

#Install
* install python3
* install the dependencies in requirements.txt
* setup your database by editing config.py
* then

        python3 manage.py shell
        from app import db
        from app.models import Role, BBS, PlatformSetting
        db.create_all()
        Role.create_roles()
        BBS.create_root_bbs()
        PlatformSetting.create_default_setting()
        
        python3 manage.py runserver

#Acknowledgment

nginx

uwsgi

flask

semantic-ui

mysql

sqlalchemy

useyourfeelings.com

...