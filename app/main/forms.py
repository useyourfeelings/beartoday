from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, SelectField, BooleanField
from wtforms.validators import Required, Length, Regexp

class PlatformSettingForm(Form):
    window_title = StringField('windoow title', validators=[Required(), Length(1, 24)])
    page_title = StringField('page title', validators=[Required(), Length(1, 24)])
    main_blog = StringField('main blog id', validators=[Required(), Length(1, 24), Regexp('^[0-9]$', 1,
                                          'bad id')])
    mode = SelectField('mode', choices = [('0', 'blog'), ('1', 'bbs')])
    show_blog_link = BooleanField('show blog link')
    submit = SubmitField('SAVE')