from flask import Flask, request, render_template, redirect, flash, session, url_for, g
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, PlaylistSong, Playlists, Song, Message
from forms import UserForm, NewSongForPlaylistForm, Login, MessageForm
from sqlalchemy.exc import IntegrityError

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import flask
import requests

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

app= Flask(__name__)

# Applying secrets
load_dotenv()

# setting flask app.config
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///dj_db'
app.config['SESSION_COOKIE_NAME'] = 'kani cookies'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True 
app.config['SECRET_KEY']= os.getenv("SECRET_KEY")
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
TOKEN_INFO = "token_info"

debug = DebugToolbarExtension(app)

# youtube client API credentials
api_service_name = "youtube"
api_version = "v3"
# linking json client_secret_CLIENTID.json file
client_secrets_file = "client_secret_CLIENTID.json"
# google API scope
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


connect_db(app)

# gettting spotify authorization
def create_spotify_oauth():
        return SpotifyOAuth(
            client_id= os.getenv("CLIENT_ID"),
            client_secret= os.getenv("CLIENT_SECRET"),
            redirect_uri=url_for('redirectPage', _external=True),
            scope= "user-library-read"
        )

# gettting youtube authorization
def create_youtube_oauth():
        # getting youtube authorization api instance
        # Get credentials and create an API client
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        
        # flow.fetch_token(authorization_response=authorization_response)

        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(client_secrets_file, scopes=scopes)
        flow.redirect_uri = flask.url_for('redirectPage', _external=True)
        
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        # Enable incremental authorization. Recommended as a best practice.
        authorization_url, state = flow.authorization_url(access_type='offline',include_granted_scopes='true')
        # Store the state so the callback can verify the auth server response.
        flask.session['state'] = state

        return flask.redirect(authorization_url)

 
        
        

@app.route('/', methods=['GET', 'POST'])
def homepage():
    """Home Page"""     
    users= User.query.all()
    form= Login()

    # Validating user login
    if form.validate_on_submit():
          username= form.username.data
          password= form.password.data
          user = User.authenticate(username, password)
          
        #   checking if user's username exist on the session
          if user:
                  session['user_id']= user.id
                  flash(f"Welcome {username}!", 'success')
                  return redirect(f"/users/{user.id}")
        
        # else redirect back to the login page
          else:
                  flash("Enter Correct login details", 'danger')
                  flash("New to Djplaylist?", 'success')
                  flash("Sign up now to get your own personalized timeline!", 'success')
                  form.username.errors.append('Wrong login details!  Please take another')
                  return redirect('/')
        

        #     - anon users: no messages
        #     - logged in: 100 most recent messages of followed_users
          
    return render_template('index.html', form=form)

# spotify login redirect page
@app.route('/spotify_auth')
def spotify_authentification():
    # spotify authorisation flow
    sp_oauth= create_spotify_oauth()
    auth_url=sp_oauth.get_authorize_url()
    return redirect(auth_url)    

# youtube login redirect page
@app.route('/youtube_auth')
def youtube_authentification():
    # youtube authorisation flow
    return create_youtube_oauth()

# creating route that bring client back to app after spotify authentification
@app.route('/redirect')
def redirectPage():
    if spotify_authentification():
        # redirecting spotify authentification back to app
        sp_oauth= create_spotify_oauth()
        session.clear()
        code= request.args.get('code')
        token_info= sp_oauth.get_access_token(code)
        session[TOKEN_INFO]= token_info
        return 'redirect'
    if youtube_authentification():
        
        # verified in the authorization server response.
        state = flask.session['state']

        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=scopes, state=state)
        flow.redirect_uri = flask.url_for('redirectPage', _external=True)

        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        authorization_response = flask.request.url
        flow.fetch_token(authorization_response=authorization_response)

        # Store credentials in the session.
        # ACTION ITEM: In a production app, you likely want to save these
        #              credentials in a persistent database instead.
        credentials = flow.credentials
        flask.session['credentials'] = credentials_to_dict(credentials)

        # return flask.redirect(flask.url_for('test_api_request'))

        # access_token = credentials.token  # Access token for making API requests
        # refresh_token = credentials.refresh_token  # Refresh token for obtaining new access tokens when the current one expires
        return 'redirect'
   


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """this creates users"""
    form= UserForm()
    if form.validate_on_submit():
        username= form.username.data
        name= form.name.data
        email= form.email.data
        password= form.password.data
        new_user = User.register(username, name, email, password)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken!  Please take another')
            return redirect('/register')
        session['user_id']= new_user.id
        flash(f'Welcome {name}! Succesfully created your account!', 'success')
        return redirect(f'/users/{new_user.id}')
    return render_template('register.html', form=form)         
    

@app.route("/users/<int:user_id>")
def show_user_account(user_id):
    user=User.query.get_or_404(user_id)
    if "user_id" not in session:
        flash("Please login frist!", "danger")
        return redirect('/')
       
    else:   
        messages = (Message.query.order_by(Message.timestamp.desc()).limit(100).all())         
        return  render_template('home.html', messages=messages)

@app.route('/logout')
def logout_user():
    session.pop('user_id')
    flash("Goodbye!", 'info')
    return redirect('/')


@app.route("/playlists/<int:playlist_id>/add-song", methods=["GET", "POST"])
def add_song_to_playlist(playlist_id):
    """Add a playlist and redirect to list."""

    playlist = Playlists.query.get_or_404(playlist_id)
    form = NewSongForPlaylistForm()

    # Restrict form to songs not already on this playlist

    curr_on_playlist = [s.id for s in playlist.songs]
    form.song.choices = (db.session.query(Song.id, Song.title)
                       .filter(Song.id.notin_(curr_on_playlist))
                       .all())

    if form.validate_on_submit():

      # This is one way you could do this ...
      playlist_song = PlaylistSong(song_id=form.song.data,
                                  playlist_id=playlist_id)
      db.session.add(playlist_song)

      
      db.session.commit()

      return redirect(f"/playlists/{playlist_id}")

    return render_template("add_song_to_playlist.html", playlist=playlist, form=form)


# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session['user_id'] = user.id


def do_logout():
    """Logout user."""

    if user_id in session:
        del session['user_id']


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template('users/show.html', user=user, messages=messages)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    # IMPLEMENT THIS


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Homepage and error pages





##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
