
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
    TFIDF = ss.initialise_tfidf()
    #COLLECTION = ss.initialise_model(gv.CHROMA_DATA_PATH,gv.MODEL,gv.COLLECTION_NAME)

    HAVE_MOTION = db.session.execute(select(Motion)).all()
    if len(HAVE_MOTION)==0:
        HAVE_MOTION = False

    HAVE_SPLIT = db.session.execute(select(Split)).all()
    if len(HAVE_SPLIT)==0:
        HAVE_SPLIT = False

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
        # if SESSION["method"] == gv.SEARCH_METHODS[0]:
        #     result = ss.compare(SESSION["search_query"],COLLECTION,SESSION["n_results"],acts,sessions)
        if SESSION["method"] == gv.SEARCH_METHODS[0]:
            result = ss.calc_tf_idf(TFIDF,SESSION["search_query"],SESSION["n_results"],acts,sessions)
        splits = ss.get_split_details(result,gv.UCU_WEBSITE_URL)
        motions = [[str(s[0]),string_to_safe(s[1]),string_to_safe(s[2])] for s in splits]
        SESSION["ids"] = [s[0] for s in splits]
        return render_template("index.html",splits=splits,search_query=SESSION["search_query"],search_methods=gv.SEARCH_METHODS,
                            method=SESSION["method"],allow_more=True,n_results=SESSION["n_initial_results"],admin=is_admin(),
                            actions=sel_acts,sessions=all_sessions,sel_sessions=sel_sessions,motions=motions,relivant_submit=True)
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
    app.run(debug=True)


# @app.route('/survey', methods=["POST","GET"])
# def relivant_splits():
#     if current_user.is_anonymous:
#         return redirect("/")
#     else:
#         if request.method == "POST":
#             user = current_user.id
#             question = request.form["q_id"]
#             exists = db.session.execute(select(Answer).where(Answer.question==question,Answer.user==user)).first()
#             if exists is None:
#                 question = db.session.execute(select(Question).where(Question.id==question)).first()[0]
#                 split_ids = [question.split1,question.split2,question.split3,question.split4,question.split5,
#                             question.split6,question.split7,question.split8,question.split9,question.split10]
#                 relivant = request.form.getlist("relivant")
#                 relivant = [int(r) for r in relivant]
#                 bool_rel = []
#                 for id in split_ids:
#                     if id in relivant:
#                         bool_rel += [True]
#                     else:
#                         bool_rel += [False]
#                 answer = Answer(question=question.id,user=user,split1=bool_rel[0],split2=bool_rel[1],split3=bool_rel[2],split4=bool_rel[3],
#                                 split5=bool_rel[4],split6=bool_rel[5],split7=bool_rel[6],split8=bool_rel[7],split9=bool_rel[8],split10=bool_rel[9])
#                 db.session.add(answer)
#                 db.session.commit()
#             return redirect("/survey")
#         else:
#             user = current_user.id
#             answered = db.session.execute(select(Answer.question).where(Answer.user==user)).all()
#             answered = [a.question for a in answered]
#             question = db.session.execute(select(Question).where(Question.id.notin_(answered))).first()
#             if question is not None:
#                 question = question[0]
#                 split_ids = [question.split_main,question.split1,question.split2,question.split3,question.split4,question.split5,
#                             question.split6,question.split7,question.split8,question.split9,question.split10]
#                 splits = db.session.execute(select(Split,Motion.title,Motion.content).join(Motion).where(Split.id.in_(split_ids))).all()
#                 motions = []
#                 splits_list = []
#                 for s in splits:
#                     motions += [[str(s[0].id),string_to_safe(s[0].content),string_to_safe(s[2])]]
#                     splits_list += [[s[0].id,s[0].content,s[0].motion_id,s[1]]]
#                 split_main = splits_list[0]
#                 del splits_list[0]
#                 return render_template("survey.html",user=is_user(),admin=is_admin(),split_main=split_main,splits=splits_list,motions=motions,question=question.id)
#             else:
#                 return render_template("survey.html",user=is_user(),admin=is_admin(),finished=True)
            
# @app.route('/make_questions', methods=["POST"])
# def gen_questions():
#     if is_admin():
#         splits = db.session.execute(select(Split).join(Motion).where(Motion.session=="2023-2024")).all()
#         actions = get_actions()
#         sessions = get_sessions()
#         del sessions[-1]
#         for split in splits:
#             split = split[0]
#             print(split.id)
#             result = ss.calc_tf_idf(TFIDF,split.content,10,actions,sessions)
#             question = Question(split_main=split.id,split1=result["ids"][0],split2=result["ids"][1],split3=result["ids"][2],split4=result["ids"][3],
#                                 split5=result["ids"][4],split6=result["ids"][5],split7=result["ids"][6],split8=result["ids"][7],split9=result["ids"][8],split10=result["ids"][9])
#             db.session.add(question)
#         db.session.commit()
#     return redirect("/survey")