from flask import Flask, request, render_template, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, PlaylistSong, Playlists, Song
from forms import UserForm, NewSongForPlaylistForm, Login
from sqlalchemy.exc import IntegrityError

app= Flask(__name__)



app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///dj_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True 
app.config['SECRET_KEY']='TDjakes35'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)

connect_db(app)


@app.route('/', methods=['GET', 'POST'])
def homepage():
    """Home Page"""     
    users= User.query.all()
    form= Login()
    """Validating user login""" 
    if form.validate_on_submit():
          username= form.username.data
          password= form.password.data
          user = User.authenticate(username, password)
          
          if user:
                  session['user_id']= user.id
                  flash(f"Welcome {username}!", 'success')
                  return redirect(f"/users/{user.id}")
        
          else:
                  flash("Enter Correct login details", 'danger')
                  form.username.errors.append('Wrong login details!  Please take another')
                  return redirect('/')
      
    return render_template('index.html', form=form)    
          
        
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
        return render_template('user_account.html',user=user)

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

      # Here's another way you could that is slightly more ORM-ish:
      #
      # song = Song.query.get(form.song.data)
      # playlist.songs.append(song)

      # Either way, you have to commit:
      db.session.commit()

      return redirect(f"/playlists/{playlist_id}")

    return render_template("add_song_to_playlist.html",
                         playlist=playlist,
                         form=form)