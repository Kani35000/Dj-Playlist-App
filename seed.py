from models import User, Song, Playlists, db
from app import app

# Create all tables
db.drop_all()
db.create_all()

u1 = User(username="kani1", Name ="kanidaye1", email="kani1@gmail.com", password="kani")
u2 = User(username="kani2", Name ="kanidaye2", email="kani2@gmail.com", password="kani2")
u3 = User(username="kani3", Name ="kanidaye3", email="kani3@gmail.com", password="kani3")


S1= Song(title="Bounce", artist ="kani1")
S2= Song(title="Bounce1", artist ="kani2")
S3= Song(title="Bounce3", artist ="kani3")

p1= Playlists(name="playlist1", description ="carefully selected1")
p2= Playlists(name="playlist2", description ="carefully selected2")
p3= Playlists(name="playlist3", description ="carefully selected3")

db.session.add_all([u1,u2,u3])
db.session.commit()

db.session.add_all([S1,S2,S3])
db.session.commit()

db.session.add_all([p1,p2,p3])
db.session.commit()