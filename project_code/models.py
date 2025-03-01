from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, AnonymousUserMixin
db = SQLAlchemy()

#run in console to create db
#from flask_app import app
#from project_code.models import db
#app.app_context().push()
#db.create_all()
#exit()

class Motion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    session = db.Column(db.String(9))
    meeting = db.Column(db.String(80))
    date = db.Column(db.String(20))
    status = db.Column(db.String(100))
    number = db.Column(db.String(10))
    content = db.Column(db.Text,nullable=False)
    proposer = db.Column(db.Text)
    amended = db.Column(db.Boolean)
    subcommittee = db.Column(db.String(60))
    notes = db.Column(db.Text)
    listing = db.Column(db.String(30))
    splits = db.relationship("Split", backref="motion")

    def __repr__(self):
        return "<Motion " + self.title + ">"
    
class Split(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text,nullable=False)
    motion_id = db.Column(db.Integer,db.ForeignKey("motion.id"))
    action = db.Column(db.String(10))

    def __repr__(self):
        return "<Split " + self.id + ">"
    
def clear_motions_db():
    splits = Split.query.all()
    for split in splits:
        db.session.delete(split)

    motions = Motion.query.all()
    for motion in motions:
        db.session.delete(motion)
    db.session.commit()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    username = db.Column(db.String(25),unique=True,nullable=False)
    password = db.Column(db.String(250),nullable=False)
    salt = db.Column(db.String(250),nullable=False)
    admin = db.Column(db.Boolean,nullable=False)