
from flask import Flask, render_template, request
import project_code.sentence_similarity as ss
from project_code.models import db
from project_code.global_variables import *
from project_code.split_motions import split_motions

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Motions.db"
db = db.init_app(app)

COLLECTION = ss.initialise_model(CHROMA_DATA_PATH,MODEL,COLLECTION_NAME)

@app.route('/', methods=["POST","GET"])
def search():
    search_methods = ["all-mpnet-base-v2","tf.idf"]
    if request.method == "POST":
        motions_content = request.form["content"]
        method = request.form["search_method"]
        if method == search_methods[0]:
            result = ss.compare(motions_content,COLLECTION,10)
        elif method == search_methods[1]:
            result = ss.calc_tf_idf(motions_content)
        splits = ss.get_split_details(result,UCU_WEBSITE_URL)
        return render_template("index.html",splits=splits,motions_content=motions_content,search_methods=search_methods,method=request.form["search_method"])
    else:
        return render_template("index.html",splits=[],motions_content="",search_methods=search_methods,method=search_methods[0])

if __name__=="__main__":
    app.run(debug=True)