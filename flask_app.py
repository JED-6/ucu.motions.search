
from flask import Flask, render_template, request, redirect
from flask import session as SESSION
import project_code.sentence_similarity as ss
from project_code.models import *
import project_code.global_variables as gv
from project_code.get_motions_web_scraper import scrape_motions
from flask_login import LoginManager, login_user, logout_user, current_user
import bcrypt
import re

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Motions.db"
app.secret_key = "Top secret"

login_manager = LoginManager()
login_manager.init_app(app)

db.init_app(app)
with app.app_context():
    db.create_all()

# COLLECTION = ss.initialise_model(gv.CHROMA_DATA_PATH,gv.MODEL,gv.COLLECTION_NAME)

def string_to_safe(text):
    text = re.sub("\n","SPECIAL1",text)
    text = re.sub("[']","SPECIAL2",text)
    text = re.sub('["]',"SPECIAL3",text)
    return text

def is_admin():
    if current_user.is_anonymous:
        return False
    return current_user.admin

@login_manager.user_loader
def loader_user(user_id):
    return db.session.scalars(select(User).where(User.id==user_id)).first()

@app.route('/', methods=["POST","GET"])
def search():
    if request.method == "POST":
        if request.form["submit_buttom"] == "Show More Results":
            SESSION["n_results"] += SESSION["n_initial_results"]
        else:
            SESSION["n_initial_results"] = int(request.form["num_results"])
            SESSION["n_results"] = int(request.form["num_results"])
            SESSION["search_query"] = request.form["search_query"]
            SESSION["method"] = request.form["search_method"]
        
        all_actions = ["All"] + get_actions()
        sel_acts = []
        acts = []
        for a in all_actions:
            if a in request.form.getlist("actions"):
                sel_acts += [[a,True]]
                acts += [a]
            else:
                sel_acts += [[a,False]]
        if "All" in request.form.getlist("actions"):
            acts = all_actions
        all_sessions = get_sessions()
        sel_sessions = [request.form["session_start"],request.form["session_end"]]
        sessions = []
        start_reached = False
        for sesh in all_sessions:
            if sesh == sel_sessions[0]:
                start_reached = True
            if start_reached:
                sessions += [sesh]
            if sesh == sel_sessions[1]:
                break
        # if SESSION["method"] == gv.SEARCH_METHODS[0]:
        #     result = ss.compare(SESSION["search_query"],COLLECTION,SESSION["n_results"],acts,sessions)
        if SESSION["method"] == gv.SEARCH_METHODS[0]:
            result = ss.calc_tf_idf(SESSION["search_query"],SESSION["n_results"],acts,sessions)
        splits = ss.get_split_details(result,gv.UCU_WEBSITE_URL)
        motions = [[str(s[0]),string_to_safe(s[1]),string_to_safe(s[2])] for s in splits]
        return render_template("index.html",splits=splits,search_query=SESSION["search_query"],search_methods=gv.SEARCH_METHODS,
                            method=SESSION["method"],allow_more=True,n_results=SESSION["n_initial_results"],admin=is_admin(),
                            actions=sel_acts,sessions=all_sessions,sel_sessions=sel_sessions,motions=motions)
    else:
        actions = ["All"]
        actions += get_actions()
        actions = [[a,False] for a in actions]
        actions[0][1] = True
        sessions = get_sessions()
        sel_sessions = [sessions[0],sessions[-1]]
        return render_template("index.html",splits=[],motions_content="",search_methods=gv.SEARCH_METHODS,method=gv.SEARCH_METHODS[0],
                               allow_more=False,n_results=10,admin=is_admin(),actions=actions,sessions=sessions,sel_sessions=sel_sessions)

@app.route('/scrape_motions', methods=["POST"])
def scrape_motions():
    if is_admin():
        start = request.form["start"]
        end = request.form["end"]+1
        splits = db.session.scalar(select(Split).where(Split.motion_id>=start,Split.motion_id<end)).all()
        split_ids = []
        for s in splits:
            split_ids += s.id
            db.session.delete(s)
        motions = db.session.scalar(select(Motion).where(Motion.id>=start,Motion.id<end)).all()
        motion_ids = []
        for m in motions:
            motion_ids += [m.id]
            db.session.delete(m)
        db.session.commit()
        message, missed =scrape_motions(gv.UCU_WEBSITE_URL,gv.UCU_WEBSITE_CLASSES,gv.CHROMA_DATA_PATH,gv.MODEL,gv.COLLECTION_NAME,start,end)
    return redirect("/")

@app.route('/survey', methods=["POST","GET"])
def relivant_splits():
    if current_user.is_anonymous:
        return redirect("/")
    else:
        split = db.session.execute(select(Split,Motion.title,Motion.content).join(Motion)).first()
        motions = [[str(split[0].id),string_to_safe(split[0].content),string_to_safe(split[2])]]
        splits = [[split[0].id,split[0].content,split[0].motion_id,split[1],split[0].action]]
        return render_template("survey.html",splits=splits,motions=motions)

@app.route('/login', methods=["POST","GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        user = db.session.scalars(select(User).where(User.username==username)).first()
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
            if db.session.scalars(select(User).where(User.username==username)).first() is None:
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