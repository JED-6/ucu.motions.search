
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, request
import project_code.sentence_similarity as ss 

app = Flask(__name__)

@app.route('/', methods=["POST","GET"])
def hello_world():
    if request.method == "POST":
        motions_content = request.form["content"]
        collection = ss.initialise_model()
        splits = ss.compare(motions_content,collection,10)
        return render_template("index.html",splits=zip(splits["documents"][0],splits["distances"][0]))
    else:
        return render_template("index.html",splits=[])

if __name__=="__main__":
    app.run(debug=True)