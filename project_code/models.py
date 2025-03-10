from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, func, text
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
        return "<Split " + str(self.id) + ">"
    
def clear_motions_db():
    splits = db.session.execute(select(Split)).all()
    for split in splits:
        db.session.delete(split)

    motions = db.session.execute(select(Motion)).all()
    for motion in motions:
        db.session.delete(motion)
    db.session.commit()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    username = db.Column(db.String(25),unique=True,nullable=False)
    password = db.Column(db.String(250),nullable=False)
    salt = db.Column(db.String(250),nullable=False)
    admin = db.Column(db.Boolean,nullable=False)

    def __repr__(self):
        return "<User " + self.username + ">"

def get_actions_ordered():
    counts = db.session.execute(select(Split.action, func.count(Split.action).label("count")).where(Split.action!="Other").group_by(Split.action).order_by(text("count DESC")))
    actions = ["Other"]
    for c in counts:
        actions += [c.action]
    return actions

def get_actions():
    counts = db.session.execute(select(Split.action).where(Split.action!="Other").distinct().order_by(Split.action))
    actions = ["Other"]
    for c in counts:
        actions += [c.action]
    return actions

def get_sessions():
    sessions = db.session.execute(select(Motion.session).order_by(Motion.session).distinct())
    sessions = [s.session for s in sessions]
    return sessions