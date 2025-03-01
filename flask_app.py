
from flask import Flask, render_template, request, session, redirect
import project_code.sentence_similarity as ss
from project_code.models import db, User
import project_code.global_variables as gv
from project_code.get_motions_web_scraper import scrape_motions
from flask_login import LoginManager, login_user, logout_user, current_user
import bcrypt

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Motions.db"
app.secret_key = "Top secret"

login_manager = LoginManager()
login_manager.init_app(app)

db.init_app(app)
with app.app_context():
    db.create_all()

COLLECTION = ss.initialise_model(gv.CHROMA_DATA_PATH,gv.MODEL,gv.COLLECTION_NAME)

def is_admin():
    if current_user.is_anonymous:
        return False
    return current_user.admin

@login_manager.user_loader
def loader_user(user_id):
    return db.session.query(User).get(user_id)

@app.route('/', methods=["POST","GET"])
def search():
    if request.method == "POST":
        if request.form["submit_buttom"] == "Scrape Motions":
            scrape_motions(gv.UCU_WEBSITE_URL,gv.URL_ID_START,gv.URL_ID_END,gv.UCU_WEBSITE_CLASSES)
            return render_template("index.html",splits=[],motions_content="",search_methods=gv.SEARCH_METHODS,
                                   method=gv.SEARCH_METHODS[0],allow_more=False,n_results=10)
        else:
            if request.form["submit_buttom"] == "Show More Results":
                session["n_results"] += session["n_initial_results"]
            else:
                session["n_initial_results"] = int(request.form["num_results"])
                session["n_results"] = int(request.form["num_results"])
                session["motions_content"] = request.form["content"]
                session["method"] = request.form["search_method"]
            
            if session["method"] == gv.SEARCH_METHODS[0]:
                result = ss.compare(session["motions_content"],COLLECTION,session["n_results"])
            elif session["method"] == gv.SEARCH_METHODS[1]:
                result = ss.calc_tf_idf(session["motions_content"],session["n_results"])
            splits = ss.get_split_details(result,gv.UCU_WEBSITE_URL)
            return render_template("index.html",splits=splits,motions_content=session["motions_content"],search_methods=gv.SEARCH_METHODS,
                                method=session["method"],allow_more=True,n_results=session["n_initial_results"],admin=is_admin())
    else:
        return render_template("index.html",splits=[],motions_content="",search_methods=gv.SEARCH_METHODS,method=gv.SEARCH_METHODS[0],
                               allow_more=False,n_results=10,admin=is_admin())

@app.route('/login', methods=["POST","GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        user = db.session.query(User).filter(User.username==username).first()
        if user is not None:
            salt = user.salt
            password = bcrypt.hashpw(request.form.get("password").encode("utf-8"),salt)
            if password == user.password:
                login_user(user)
                return redirect("/")
        return render_template("login.html",admin=is_admin(),failed=True)
    else:
        return render_template("login.html",admin=is_admin())

@app.route('/register', methods=["POST","GET"])
def register():
    if is_admin():
        if request.method == "POST":
            username = request.form.get("username")
            if db.session.query(User).filter(User.username==username).first() is None:
                password = request.form.get("password")
                confirm = request.form.get("confirm")
                if password == confirm:
                    salt = bcrypt.gensalt()
                    password_crypt = bcrypt.hashpw(password.encode("utf-8"),salt)
                    user = User(username=username,password=password_crypt,salt=salt,admin=False)
                    db.session.add(user)
                    db.session.commit()
                    login_user(user)
                    return redirect("/")
                else:
                    render_template("register.html",password=True)
            else:
                render_template("register.html",username=True)
        else:
            return render_template("register.html")
    else:
        return redirect("/")

@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)