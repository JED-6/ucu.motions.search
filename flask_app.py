
from flask import Flask, render_template, request, redirect
from flask import session as SESSION
import project_code.sentence_similarity as ss
from project_code.models import *
import project_code.global_variables as gv
from project_code.get_motions_web_scraper import scrape_motions
from flask_login import LoginManager, login_user, logout_user, current_user
import bcrypt
import re

global TFIDF, HAVE_MOTION, HAVE_SPLIT

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Motions.db"
app.secret_key = "Top secret"

login_manager = LoginManager()
login_manager.init_app(app)

db.init_app(app)
with app.app_context():
    db.create_all()
    HAVE_MOTION = db.session.execute(select(Motion)).all()
    if len(HAVE_MOTION)==0:
        HAVE_MOTION = False
    else:
        HAVE_MOTION = True

    HAVE_SPLIT = db.session.execute(select(Split)).all()
    if len(HAVE_SPLIT)==0:
        HAVE_SPLIT = False
    else:
        HAVE_SPLIT = True
    if HAVE_SPLIT:
        print("Initialising TFIDF model  ...")
        TFIDF = ss.initialise_tfidf()
        # print("Initialising Transformer model  ...")
        # TRANSFORMER, EMBEDINGS = ss.initialise_transformer_model(gv.MODEL,with_embeddings=True)

def string_to_safe(text):
    text = re.sub("\n","SPECIAL1",text)
    text = re.sub("[']","SPECIAL2",text)
    text = re.sub('["]',"SPECIAL3",text)
    return text

def is_admin():
    if current_user.is_anonymous:
        return False
    return current_user.admin

def is_user():
    if current_user.is_anonymous:
        return False
    else:
        return True

@login_manager.user_loader
def loader_user(user_id):
    return db.session.scalars(select(User).where(User.id==user_id)).first()

@app.route('/', methods=["POST","GET"])
def search():
    if request.method == "POST":
        if not HAVE_MOTION or not HAVE_SPLIT:
            return render_template("index.html",missing_data=True,user=is_user(),admin=is_admin())
        if request.form["submit_buttom"] == "Show More Results":
            SESSION["n_results"] += SESSION["n_initial_results"]
        else:
            SESSION["n_initial_results"] = int(request.form["num_results"])
            SESSION["n_results"] = int(request.form["num_results"])
            SESSION["search_query"] = request.form["search_query"]
            SESSION["method"] = request.form["search_method"]
            SESSION["start_session"] = request.form["session_start"]
            SESSION["end_session"] = request.form["session_end"]
            SESSION["actions"] = request.form.getlist("actions")
        
        all_actions = ["All"] + get_actions()
        sel_acts = []
        acts = []
        for a in all_actions:
            if a in SESSION["actions"]:
                sel_acts += [[a,True]]
                acts += [a]
            else:
                sel_acts += [[a,False]]
        if "All" in SESSION["actions"]:
            acts = all_actions
        all_sessions = get_sessions()
        sel_sessions = [SESSION["start_session"],SESSION["end_session"]]
        sessions = []
        start_reached = False
        for sesh in all_sessions:
            if sesh == sel_sessions[0]:
                start_reached = True
            if start_reached:
                sessions += [sesh]
            if sesh == sel_sessions[1]:
                break
        # if SESSION["method"] == gv.SEARCH_METHODS[1]:
        #     result = ss.compare_transformer_model(SESSION["search_query"],TRANSFORMER,EMBEDINGS,SESSION["n_results"],acts,sessions)
        if SESSION["method"] == gv.SEARCH_METHODS[0]:
            result = ss.calc_tf_idf(TFIDF,SESSION["search_query"],SESSION["n_results"],acts,sessions)
        splits = ss.get_split_details(result,gv.UCU_WEBSITE_URL)
        motions = [[str(s[0]),string_to_safe(s[2]),string_to_safe(s[3])] for s in splits]
        SESSION["ids"] = [s[0] for s in splits]
        return render_template("index.html",splits=splits,search_query=SESSION["search_query"],search_methods=gv.SEARCH_METHODS,
                            method=SESSION["method"],allow_more=True,n_results=SESSION["n_initial_results"],actions=sel_acts,
                            sessions=all_sessions,sel_sessions=sel_sessions,motions=motions,relivant_submit=True,user=is_user(),admin=is_admin())
    else:
        if not HAVE_MOTION or not HAVE_SPLIT:
            return render_template("index.html",missing_data=True,user=is_user(),admin=is_admin())
        else:
            actions = ["All"]
            actions += get_actions()
            actions = [[a,False] for a in actions]
            actions[0][1] = True
            sessions = get_sessions()
            sel_sessions = [sessions[0],sessions[-1]]
            return render_template("index.html",splits=[],motions_content="",search_methods=gv.SEARCH_METHODS,method=gv.SEARCH_METHODS[0],
                                allow_more=False,n_results=10,user=is_user(),admin=is_admin(),actions=actions,sessions=sessions,sel_sessions=sel_sessions)

@app.route('/scrape_motions', methods=["POST"])
def scrape():
    global TFIDF, HAVE_MOTION, HAVE_SPLIT
    #19984
    if is_admin():
        start = int(request.form["start"])
        end = int(request.form["end"])+1
        splits = db.session.execute(select(Split).where(Split.motion_id>=start,Split.motion_id<end)).all()
        #add warning about deleting existing splits and motions
        split_ids = []
        for s in splits:
            split_ids += [s[0].id]
            db.session.delete(s[0])
        motions = db.session.execute(select(Motion).where(Motion.id>=start,Motion.id<end)).all()
        motion_ids = []
        for m in motions:
            motion_ids += [m[0].id]
            db.session.delete(m[0])
        db.session.commit()
        message, missed = scrape_motions(gv.UCU_WEBSITE_URL,gv.UCU_WEBSITE_CLASSES,gv.CHROMA_DATA_PATH,gv.MODEL,gv.COLLECTION_NAME,start,end)
        TFIDF = ss.initialise_tfidf()
        HAVE_MOTION = db.session.execute(select(Motion)).all()
        if len(HAVE_MOTION)==0:
            HAVE_MOTION = False

        HAVE_SPLIT = db.session.execute(select(Split)).all()
        if len(HAVE_SPLIT)==0:
            HAVE_SPLIT = False
    return redirect("/")

@app.route('/relivance', methods=["POST"])
def relivance():
    if request.method == "POST":
        if current_user.is_anonymous:
            user = 0
        else:
            user = current_user.id
        relivant = request.form.getlist("relivant")
        ids = SESSION["ids"]
        query = db.session.scalars(select(SearchQuery).where(SearchQuery.question==SESSION["search_query"])).first()
        if query is None:
            query = SearchQuery(question=SESSION["search_query"])
            db.session.add(query)
            db.session.commit()
        else:
            results = db.session.execute(select(RelivantResults).where(RelivantResults.query_id==query.id,RelivantResults.user_id==user,RelivantResults.split_id.in_(ids))).all()
            if len(results)>0:
                for r in results:
                    if not r[0].relivant and str(r[0].split_id) in relivant:
                        db.session.execute(update(RelivantResults).where(RelivantResults.query_id==query.id,RelivantResults.user_id==user,
                                                                         RelivantResults.split_id==r[0].split_id).values(relivant=True))
                    del ids[ids.index(r[0].split_id)]
        for id in ids:
            if str(id) in relivant:
                rel = True
            else:
                rel = False
            result = RelivantResults(user_id=user,query_id=query.id,split_id=id,relivant=rel)
            db.session.add(result)
        db.session.commit()
        
    return redirect("/")

@app.route('/login', methods=["POST","GET"])
def login():
    if is_user():
        return redirect("/")
    else:
        if request.method == "POST":
            username = request.form.get("username")
            user = db.session.scalars(select(User).where(User.username==username)).first()
            if user is not None:
                salt = user.salt
                password = bcrypt.hashpw(request.form.get("password").encode("utf-8"),salt)
                if password == user.password:
                    login_user(user)
                    return redirect("/")
            return render_template("login.html",user=is_user(),admin=is_admin(),failed=True)
        else:
            return render_template("login.html",user=is_user(),admin=is_admin())

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
                    return redirect("/")
                else:
                    render_template("register.html",user=is_user(),admin=is_admin(),password=True)
            else:
                render_template("register.html",user=is_user(),admin=is_admin(),username=True)
        else:
            return render_template("register.html",user=is_user(),admin=is_admin())
    else:
        return redirect("/")

@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True,use_reloader=False)