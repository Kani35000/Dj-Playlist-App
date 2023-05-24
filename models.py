from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy.sql import func


db = SQLAlchemy()

bcrypt = Bcrypt()

def connect_db(app):
    db.app = app
    db.init_app(app)





# MODELS HERE


class Playlists(db.Model):
    __tablename__='playlist'

    def __repr__(self):
        """Shows info about user."""
        p =self
        return f"<Playlists id={p.id} name={p.name} description={p.description}>"


    id= db.Column(db.Integer, primary_key=True, autoincrement=True)
    name= db.Column(db.Text, nullable= False, unique=True)
    description= db.Column(db.Text)
    created_at= db.Column(db.TIMESTAMP, nullable=False, server_default=func.now())
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user=db.relationship('User', backref='playlist')

    song_plalist= db.relationship('Playlists', secondary='playlist_songs', backref="song")




class Song(db.Model):
    __tablename__='song'

    def __repr__(self):
        """Shows info about user."""
        p =self
        return f"<Song id={p.id} title={p.title} artist={p.artist}>"


    id= db.Column(db.Integer, primary_key=True, autoincrement=True)
    title= db.Column(db.Text, nullable= False)
    artist= db.Column(db.Text, nullable= False)




class PlaylistSong(db.Model):
    __tablename__ = 'playlist_songs'  


    def __repr__(self):
        """Shows info about playlist songs."""
        p =self
        return f"<PlaylistSong id={p.id} playlist_id={p.playlist_id} song_id={p.song_id}>"

    id = db.Column(db.Integer,
                    primary_key=True,
                    autoincrement=True)

    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'))

    song_id = db.Column(db.Integer, db.ForeignKey('song.id'))

   


class User(db.Model):
    __tablename__ = 'users'  


    def __repr__(self):
        """Shows info about playlist songs."""
        p =self
        return f"<User id={p.id} name={p.name} email={p.email} password={p.password} >"

    id = db.Column(db.Integer,
                    primary_key=True,
                    autoincrement=True)

    username = db.Column(db.Text, nullable= False, unique=True)
    name = db.Column(db.Text, nullable= False)
    email= db.Column(db.Text, nullable= False, unique=True)
    password = db.Column(db.Text, nullable= False)

    @classmethod
    def register(cls, username, name, email, password):
        """Register user w/hashed password & return user"""

        hashed = bcrypt.generate_password_hash(password)
        # Turn byteString into normal (unicode utf8) string
        hashed_utf8= hashed.decode("utf8")
        #return instance of user w/ username and hashed password
        return cls(username=username, name=name, email=email, password=hashed_utf8)
    
    @classmethod
    def authenticate(cls, username, password):
        """Validates that user exist and password is correct
        Return user if valid;else return false
        """

        u = User.query.filter_by(username=username).first()

        if u and bcrypt.check_password_hash(u.password, password):
            # return user instance
            return u
        
        else:
            return False

   
    
