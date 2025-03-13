
from flask import Flask, render_template, request, redirect, url_for
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
        print("Initialising TFIDF model ...")
        TFIDF = ss.initialise_tfidf()
        print("Initialising Word Overlap Tokens ...")
        #WO_TOKENS = ss.initialise_WO()
        WO_TOKENS = ""
        print("Initialising Transformer model  ...")
        TRANSFORMER, EMBEDINGS = ss.initialise_transformer_model(gv.MODEL,with_embeddings=True,strip=gv.STRIP)

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
    
@app.before_request
def initialise_var():
    if not SESSION.get("refresh"):
        SESSION["refresh"] = False

@login_manager.user_loader
def loader_user(user_id):
    return db.session.scalars(select(User).where(User.id==user_id)).first()

@app.route('/', methods=["POST","GET"])
def search():
    if request.method == "POST":
        if not HAVE_MOTION or not HAVE_SPLIT:
            return render_template("index.html",missing_data=True,user=is_user(),admin=is_admin())
        if SESSION["refresh"]:
            SESSION["refresh"] = False
        elif request.form["submit_buttom"] == "Show More Results":
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
        if SESSION["method"] == gv.SEARCH_METHODS[0]:
            result = ss.calc_tf_idf(TFIDF,SESSION["search_query"],SESSION["n_results"],acts,sessions)
        elif SESSION["method"] == gv.SEARCH_METHODS[1]:
            result = ss.word_overlap(SESSION["search_query"],WO_TOKENS,SESSION["n_results"],acts,sessions)
        elif SESSION["method"] == gv.SEARCH_METHODS[2]:
             result = ss.compare_transformer_model(SESSION["search_query"],TRANSFORMER,EMBEDINGS,SESSION["n_results"],acts,sessions,strip=gv.STRIP)
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
        for id in ids:
            if str(id) in relivant:
                rel = True
            else:
                rel = False
            id_obj = db.session.scalars(select(func.max(RelivantResults.id))).first()
            if id_obj is not None:
                rel_id = id_obj+1
            else:
                rel_id = 1
            result = RelivantResults(id=rel_id,user_id=user,query_id=query.id,split_id=id,relivant=rel)
            db.session.add(result)
        db.session.commit()
        SESSION["refresh"] = True
        return redirect(url_for("search"), code=307)
        
    return redirect("/")

@app.route('/survey', methods=["POST","GET"])
def survey():
    if not is_admin():
        return redirect("/")
    else:
        if request.method == "POST":
            user = current_user.id
            relivant = request.form.getlist("relivant")
            ids = SESSION["result_ids"]
            query = db.session.execute(select(SearchQuery).where(SearchQuery.id==SESSION["query_id"])).first()
            query=query[0]
            for id in ids:
                id_obj = db.session.scalars(select(func.max(RelivantResults.id))).first()
                if id_obj is not None:
                    rel_id = id_obj+1
                else:
                    rel_id = 1
                if str(id) in relivant:
                    rel_res = RelivantResults(id=rel_id,user_id=user,query_id=query.id,split_id=id,relivant=True,method=SESSION["method2"])
                else:
                    rel_res = RelivantResults(id=rel_id,user_id=user,query_id=query.id,split_id=id,relivant=False,method=SESSION["method2"])
                db.session.add(rel_res)
            db.session.commit()
            SESSION["method2"] = request.form["search_method"]
            return redirect("/survey")
        else:
            if not SESSION.get("method2"):
                SESSION["method2"] = gv.SEARCH_METHODS[0]
            user = current_user.id
            answered = db.session.execute(select(SearchQuery.id).join(RelivantResults).where(RelivantResults.user_id==user,RelivantResults.method==SESSION["method2"]).distinct()).all()
            answered_ids = []
            for a in answered:
                answered_ids += a
            query = db.session.execute(select(SearchQuery).where(SearchQuery.id.not_in(answered_ids))).first()
            if query is None:
                split = db.session.execute(select(Split).join(Motion).where(Split.id.not_in(answered_ids),Motion.session=="2023-2024").order_by(func.random())).first()
                if split is None:
                    return redirect("/")
                else:
                    split = split[0]
                query = SearchQuery(question=split.content,split_id=split.id)
                db.session.add(query)
                db.session.commit()
            else:
                query = query[0]
            acts = ["All"] + get_actions()
            sessions = get_sessions()
            del sessions[sessions.index("2023-2024")]
            if SESSION["method2"] == gv.SEARCH_METHODS[2]:
                result = ss.compare_transformer_model(query.question,TRANSFORMER,EMBEDINGS,10,acts,sessions,strip=gv.STRIP)
            elif SESSION["method2"] == gv.SEARCH_METHODS[1]:
                result = ss.word_overlap(query.question,WO_TOKENS,10,acts,sessions)
            else:
                result = ss.calc_tf_idf(TFIDF,query.question,10,acts,sessions)
            splits = ss.get_split_details(result,gv.UCU_WEBSITE_URL)
            motions = [[str(s[0]),string_to_safe(s[2]),string_to_safe(s[3])] for s in splits]
            SESSION["result_ids"] = [s[0] for s in splits]
            SESSION["query_id"] = query.id
            motion_main = string_to_safe(db.session.execute(select(Motion.content).join(Split).where(Split.id==query.split_id)).first()[0])
            return render_template("survey.html",user=is_user(),admin=is_admin(),split_main=string_to_safe(query.question),
                                   motion_main=motion_main,splits=splits,search_query=query.question,motions=motions,search_methods=gv.SEARCH_METHODS,method=SESSION["method2"])

@app.route('/help', methods=["GET"])
def help():
    return render_template("help.html",user=is_user(),admin=is_admin())

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
                    ids = db.session.execute(select(User.id)).all()
                    ids = [id.id for id in ids]
                    id = gen_id(existing=ids)
                    user = User(id=id,username=username,password=password_crypt,salt=salt,admin=False)
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
    app.run(debug=True)#,use_reloader=False)