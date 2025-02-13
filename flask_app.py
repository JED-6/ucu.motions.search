
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=["POST","GET"])
def hello_world():
    if request.method == "POST":
        motions_content = request.form["content"]
        return motions_content
    else:
        return render_template("index.html")

if __name__=="__main__":
    app.run(debug=True)