from flask_wtf import FlaskForm
from wtforms import FloatField, EmailField, StringField, PasswordField
from wtforms.validators import InputRequired, Email, Length


class UserForm(FlaskForm):

    username= StringField("Username", validators=[InputRequired()])
    name= StringField("Fullname", validators=[InputRequired()])
    email = StringField('Email address', validators=[InputRequired()])
    password= PasswordField("Password", validators=[InputRequired()])
    
class NewSongForPlaylistForm(FlaskForm):
    New_song= StringField("New song", validators=[InputRequired()])

class Login(FlaskForm):
    
    username= StringField("Username", validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])






