from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy.sql import func
from datetime import datetime

db = SQLAlchemy()

bcrypt = Bcrypt()

def connect_db(app):
    """Connect this database to provided Flask app."""
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


class Follows(db.Model):
    """Connection of a follower <-> followed_user."""

    __tablename__ = 'follows'
    def __repr__(self):
        """Shows info about user."""
        p =self
        return f"< Song user_being_followed_id={p.user_being_followed_id} user_following_id={p.user_following_id} >"

    user_being_followed_id = db.Column(db.Integer,db.ForeignKey('users.id', ondelete="cascade"),primary_key=True,)
    user_following_id = db.Column(db.Integer,db.ForeignKey('users.id', ondelete="cascade"),primary_key=True,)



class User(db.Model):
    __tablename__ = 'users'  


    def __repr__(self):
        """Shows info about playlist songs."""
        p =self
        return f"<User id={p.id} name={p.name} email={p.email} password={p.password} username={p.username} image_url={p.image_url} header_image_url={p.header_image_url} bio={p.bio} location={p.location} messages={p.messages} followers={p.followers} following={p.following} likes={p.likes}>"

    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    username = db.Column(db.Text, nullable= False, unique=True)
    name = db.Column(db.Text, nullable= False)
    email= db.Column(db.Text, nullable= False, unique=True)
    password = db.Column(db.Text, nullable= False)
    image_url = db.Column(db.Text,default="/static/images/default-pic.png",)
    header_image_url = db.Column(db.Text,default="/static/images/warbler-hero.jpg")
    bio = db.Column(db.Text,)
    location = db.Column(db.Text,)
    messages = db.relationship('Message')
    followers = db.relationship("User",secondary="follows",primaryjoin=(Follows.user_being_followed_id == id),secondaryjoin=(Follows.user_following_id == id))
    following = db.relationship("User",secondary="follows",primaryjoin=(Follows.user_following_id == id),secondaryjoin=(Follows.user_being_followed_id == id))
    likes = db.relationship('Message',secondary="likes")

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

    def is_followed_by(self, other_user):
        """Is this user followed by `other_user`?"""

        found_user_list = [user for user in self.followers if user == other_user]
        return len(found_user_list) == 1

    def is_following(self, other_user):
        """Is this user following `other_use`?"""

        found_user_list = [user for user in self.following if user == other_user]
        return len(found_user_list) == 1

    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False




class Likes(db.Model):
    """Mapping user likes to warbles."""

    __tablename__ = 'likes' 

    id = db.Column(db.Integer,primary_key=True)

    user_id = db.Column(db.Integer,db.ForeignKey('users.id', ondelete='cascade'))

    message_id = db.Column(db.Integer,db.ForeignKey('messages.id', ondelete='cascade'),unique=True)


class Message(db.Model):
    """An individual message ("warble")."""

    __tablename__ = 'messages'

    id = db.Column(db.Integer,primary_key=True,)
    text = db.Column(db.String(140),nullable=False,)
    timestamp = db.Column(db.DateTime,nullable=False,default=datetime.utcnow(),)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id', ondelete='CASCADE'),nullable=False,)
    user = db.relationship('User')



