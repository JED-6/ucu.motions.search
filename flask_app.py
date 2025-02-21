
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, request
import project_code.sentence_similarity as ss
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Motions.db"
db = SQLAlchemy(app)

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
    subcommitee = db.Column(db.String(60))
    notes = db.Column(db.Text)
    listing = db.Column(db.String(30))

    def __repr__(self):
        return "<Motion " + self.title + ">"

#run in console to create db
#from flask_app import app, db
#app.app_context().push()
#db.create_all()

@app.route('/', methods=["POST","GET"])
def hello_world():
    if request.method == "POST":
        motions_content = request.form["content"]
        collection = ss.initialise_model()
        splits = ss.compare(motions_content,collection,10)
        return render_template("index.html",splits=zip(splits["documents"],splits["distances"],splits["links"],splits["Title"]),motions_content=motions_content)
    else:
        return render_template("index.html",splits=[],motions_content="")

if __name__=="__main__":
    app.run(debug=True)