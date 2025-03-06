from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, func, text, Boolean, Text, String, ForeignKey, update
from typing import List
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy_utils import database_exists, create_database
from flask_login import UserMixin, AnonymousUserMixin
import random

#run in console to create db
#from flask_app import app
#from project_code.models import db
#app.app_context().push()
#db.create_all()
#exit()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class RelivantResults(Base):
    __tablename__ = "relivant_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"),primary_key=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("searchquery.id"),primary_key=True)
    split_id: Mapped[int] = mapped_column(ForeignKey("split.id"),primary_key=True)
    relivant: Mapped[Boolean] = mapped_column(Boolean,nullable=False)

    user:Mapped["User"] = relationship(back_populates="relivant")
    search_query:Mapped["SearchQuery"] = relationship(back_populates="relivant")
    split:Mapped["Split"] = relationship(back_populates="relivant")


class Motion(Base):
    __tablename__ = "motion"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    session: Mapped[str] = mapped_column(String(9))
    meeting: Mapped[str] = mapped_column(String(80))
    date: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(100))
    number: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text,nullable=False,deferred=True)
    proposer: Mapped[str] = mapped_column(Text,deferred=True)
    amended: Mapped[str] = mapped_column(Boolean)
    subcommittee: Mapped[str] = mapped_column(String(60))
    notes: Mapped[str] = mapped_column(Text,deferred=True)
    listing: Mapped[str] = mapped_column(String(30))
    splits: Mapped[List["Split"]] = relationship()
    
class Split(Base):
    __tablename__ = "split"
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text,nullable=False,deferred=True)
    motion_id: Mapped[int] = mapped_column(ForeignKey("motion.id"))
    action: Mapped[str] = mapped_column(String(10))
    relivant: Mapped[List["RelivantResults"]] = relationship(back_populates="split")
    

class User(UserMixin, Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(25),nullable=False)
    password: Mapped[str] = mapped_column(String(250),nullable=False)
    salt: Mapped[str] = mapped_column(String(250),nullable=False)
    admin: Mapped[str] = mapped_column(Boolean,nullable=False)
    relivant: Mapped[List["RelivantResults"]] = relationship(back_populates="user")
    
    
class SearchQuery(Base):
    __tablename__ = "searchquery"
    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(Text,nullable=False,deferred=True)
    relivant: Mapped[List["RelivantResults"]] = relationship(back_populates="search_query")

def clear_motions_db():
    splits = db.session.execute(select(Split)).all()
    for split in splits:
        db.session.delete(split)

    motions = db.session.execute(select(Motion)).all()
    for motion in motions:
        db.session.delete(motion)
    db.session.commit()

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
    if len(sessions)==0:
        sessions = ["None"]
    return sessions

def gen_id(existing=[]):
    available = []
    max_val = 100000
    m = 1
    while len(available)==0:
        available = list(set(range(0,max_val*m))-set(existing))
        m = m * 10
    id = random.choice(available)
    return id