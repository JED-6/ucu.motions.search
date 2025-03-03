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
    splits = db.relationship("Split")

    def __repr__(self):
        return "<Motion " + self.title + ">"
    
class Split(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text,nullable=False)
    motion_id = db.Column(db.Integer,db.ForeignKey("motion.id"),nullable=False)
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
    answers = db.relationship("Answer")

    def __repr__(self):
        return "<User " + self.username + ">"

class Question(db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    split_main = db.Column(db.Integer,nullable=False)
    split1 = db.Column(db.Integer)
    split2 = db.Column(db.Integer)
    split3 = db.Column(db.Integer)
    split4 = db.Column(db.Integer)
    split5 = db.Column(db.Integer)
    split6 = db.Column(db.Integer)
    split7 = db.Column(db.Integer)
    split8 = db.Column(db.Integer)
    split9 = db.Column(db.Integer)
    split10 = db.Column(db.Integer)
    answers = db.relationship("Answer")

class Answer(db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    question = db.Column(db.Integer,db.ForeignKey("question.id"),nullable=False)
    user = db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    split1 = db.Column(db.Boolean)
    split2 = db.Column(db.Boolean)
    split3 = db.Column(db.Boolean)
    split4 = db.Column(db.Boolean)
    split5 = db.Column(db.Boolean)
    split6 = db.Column(db.Boolean)
    split7 = db.Column(db.Boolean)
    split8 = db.Column(db.Boolean)
    split9 = db.Column(db.Boolean)
    split10 = db.Column(db.Boolean)

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