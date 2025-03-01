
from flask import Flask, render_template, request, session, flash
import project_code.sentence_similarity as ss
from project_code.models import db
import project_code.global_variables as gv
from project_code.get_motions_web_scraper import scrape_motions

from project_code.split_motions import encode_splits

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Motions.db"
app.secret_key = "Top secret"
db = db.init_app(app)

COLLECTION = ss.initialise_model(gv.CHROMA_DATA_PATH,gv.MODEL,gv.COLLECTION_NAME)

@app.route('/', methods=["POST","GET"])
def search():
    global db
    search_methods = ["all-mpnet-base-v2","tf.idf"]
    if request.method == "POST":
        if request.form["submit_buttom"] == "Scrape Motions":
            scrape_motions(gv.UCU_WEBSITE_URL,gv.URL_ID_START,gv.URL_ID_END,gv.UCU_WEBSITE_CLASSES)
            return render_template("index.html",splits=[],motions_content="",search_methods=search_methods,
                                   method=search_methods[0],allow_more=False,n_results=10)
        else:
            if request.form["submit_buttom"] == "Show More Results":
                session["n_results"] += session["n_initial_results"]
            else:
                session["n_initial_results"] = int(request.form["num_results"])
                session["n_results"] = int(request.form["num_results"])
                session["motions_content"] = request.form["content"]
                session["method"] = request.form["search_method"]
            
            if session["method"] == search_methods[0]:
                result = ss.compare(session["motions_content"],COLLECTION,session["n_results"])
            elif session["method"] == search_methods[1]:
                result = ss.calc_tf_idf(session["motions_content"],session["n_results"])
            splits = ss.get_split_details(result,gv.UCU_WEBSITE_URL)
            return render_template("index.html",splits=splits,motions_content=session["motions_content"],search_methods=search_methods,
                                method=session["method"],allow_more=True,n_results=session["n_initial_results"])
    else:
        return render_template("index.html",splits=[],motions_content="",search_methods=search_methods,method=search_methods[0],allow_more=False,n_results=10)

if __name__=="__main__":
    app.run(debug=True)