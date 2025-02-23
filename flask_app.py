
from flask import Flask, render_template, request
import project_code.sentence_similarity as ss
from project_code.models import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Motions.db"
db = db.init_app(app)

@app.route('/', methods=["POST","GET"])
def search():
    if request.method == "POST":
        motions_content = request.form["content"]
        collection = ss.initialise_model()
        splits = ss.compare(motions_content,collection,10)
        return render_template("index.html",splits=zip(splits["documents"],splits["distances"],splits["links"],splits["Title"]),motions_content=motions_content)
    else:
        return render_template("index.html",splits=[],motions_content="")

if __name__=="__main__":
    app.run(debug=True)