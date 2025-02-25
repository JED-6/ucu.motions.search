
from flask import Flask, render_template, request
import project_code.sentence_similarity as ss
from project_code.models import db
from project_code.global_variables import *
from project_code.split_motions import split_motions

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Motions.db"
db = db.init_app(app)

@app.route('/', methods=["POST","GET"])
def search():
    global COLLECTION_INITIALIZED
    if request.method == "POST":
        motions_content = request.form["content"]
        method = request.form["search_method"]
        if method == "all_mpnet_base_v2":
            if not COLLECTION_INITIALIZED:
                collection = ss.initialise_model(CHROMA_DATA_PATH,MODEL,COLLECTION_NAME)
                COLLECTION_INITIALIZED = True
            result = ss.compare(motions_content,collection,10)
        elif method == "tf_idf":
            result = ss.calc_tf_idf(motions_content)
        splits = ss.get_split_details(result,UCU_WEBSITE_URL)
        return render_template("index.html",splits=zip(splits["documents"],splits["distances"],splits["links"],splits["Title"]),motions_content=motions_content)
    else:
        return render_template("index.html",splits=[],motions_content="")

if __name__=="__main__":
    app.run(debug=True)