print("Loading packages ...")
from flask import Flask, render_template, request, redirect, url_for
from flask import session as SESSION
import project_code.sentence_similarity as ss
from project_code.models import *
import project_code.global_variables as gv
from project_code.get_motions_web_scraper import scrape_motions
from flask_login import LoginManager, login_user, logout_user, current_user
import bcrypt
import re
import secrets

from project_code.split_motions import resplit_motions

global TFIDF, HAVE_MOTION, HAVE_SPLIT

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Motions.db"
app.secret_key = secrets.token_hex(32)

login_manager = LoginManager()
login_manager.init_app(app)

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time

# initialises necessary models and embeddings for the different search methods
def initialise_models():
    global TFIDF, LSA, WORD2VECS, GLOVE, BI_ENCODER, EMBEDINGS, CROSS_ENCODER
    print("Initialising TFIDF ...")
    TFIDF = ss.initialise_tfidf(gv.STRIP)
    print("Initialising LSA ...")
    LSA = ss.init_LSA(TFIDF,gv.STRIP)

    # cumulative_variance = np.cumsum(LSA.explained_variance_ratio_)
    # plt.plot(cumulative_variance)
    # plt.xlabel('Number of components')
    # plt.ylabel('Cumulative explained variance')
    # plt.grid(True)
    # plt.show()

    print("Initialising Word2Vec ...")
    WORD2VECS = ss.init_Word2Vec()
    print("Initialising GloVe ...")
    GLOVE = ss.init_GloVe()
    print("Initialising Bi-Encoder  ...")
    BI_ENCODER, EMBEDINGS = "", "" #ss.initialise_bi_encoder(gv.BI_ENCODER_NAME,with_embeddings=True,strip=gv.STRIP)
    print("Initialising Cross-Encoder  ...")
    CROSS_ENCODER = ss.initialise_cross_encoder(gv.CROSS_ENCODER_NAME)

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
        initialise_models()

# replaces special characters to allow text to be passed to javascript
# replacement symbols "SPECIAL1" ect are converted back by javascript
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
    
def analys_relevant():
    methods = gv.SEARCH_METHODS
    del methods[6]
    results_init = db.session.execute(select(RelevantResults)).all()
    columns = ["id","user_id","query_id","split_id","relevant","method","similarity"]
    results = {"id":[],"user_id":[],"query_id":[],"split_id":[],"relevant":[],"method":[],"similarity":[]}
    for r in results_init:
            results["id"] += [r[0].id]
            results["user_id"] += [r[0].user_id]
            results["query_id"] += [r[0].query_id]
            results["split_id"] += [r[0].split_id]
            results["relevant"] += [r[0].relevant]
            results["method"] += [r[0].method]
            results["similarity"] += [r[0].similarity]

    results = pd.DataFrame(results)
    queries = [q for q in range(1,21)]

    for q in queries:
        q_splits = results["split_id"].loc[(results["query_id"]==q)]
        for s in q_splits:
            rel = results["relevant"].loc[(results["query_id"]==q) & (results["split_id"]==s)]
            if any(rel):
                results.loc[(results["query_id"]==q) & (results["split_id"]==s),"Relevnat"] = True

    print("Precision")
    for meth in methods:
        relevant1 = np.multiply(np.array(results["relevant"].loc[(results["method"]==meth) & (results["query_id"].isin(queries[:11]))]),1)
        print(meth,"long query average:",sum(relevant1)/len(relevant1))
        relevant2 = np.multiply(np.array(results["relevant"].loc[(results["method"]==meth) & (results["query_id"].isin(queries[11:]))]),1)
        print(meth,"short query average:",sum(relevant2)/len(relevant2))
        print(meth,"total average:",(sum(relevant1)+sum(relevant2))/(len(relevant1)+len(relevant2)))

    print("Recall")
    relevant1 = []
    relevant2 = []
    for q in range(1,11):
        relevant1 += [set(results["split_id"].loc[(results["relevant"]) & (results["query_id"]==q)])]
        relevant2 += [set(results["split_id"].loc[(results["relevant"]) & (results["query_id"]==q+10)])]

    all_selected1 = []
    all_selected2 = []
    for meth in methods:
        selected1 = []
        selected2 = []
        recall1 = 0
        recall2 = 0
        for q in range(1,11):
            selected1 += [set(results["split_id"].loc[(results["relevant"]) & (results["method"]==meth) & (results["query_id"]==q)])]
            selected2 += [set(results["split_id"].loc[(results["relevant"]) & (results["method"]==meth) & (results["query_id"]==q+10)])]
            recall1 += len(selected1[q-1])/len(relevant1[q-1])
            recall2+= len(selected2[q-1])/len(relevant2[q-1])

        all_selected1 += [selected1]
        all_selected2 += [selected2]

        print(meth,"long query recall:",recall1/10)
        print(meth,"short query recall:",recall2/10)
        print(meth,"total average:",(recall1+recall2)/20)
    
    print("Overlap")
    overlap_mat1 = []
    for meth1 in range(len(methods)):
        overlap_mat1 += [[]]
        for meth2 in range(len(methods)):
            overlap = 0
            for q in range(0,10):
                selected1 = all_selected2[meth1][q]
                selected2 = all_selected2[meth2][q]
                if len(selected2)!=0:
                    overlap += len(selected1.intersection(selected2))/len(selected2)
                else:
                    overlap += 1
            overlap = overlap/10
            overlap_mat1[meth1] += [overlap]

    overlap_mat1 += [[]]
    for meth2 in range(len(methods)):
        overlap = 0
        for q in range(0,10):
            selected1 = all_selected2[0][q].union(all_selected2[1][q]).union(all_selected2[2][q])
            selected2 = all_selected2[meth2][q]
            if len(selected2)!=0:
                overlap += len(selected1.intersection(selected2))/len(selected2)
            else:
                overlap += 1
        overlap = overlap/10
        overlap_mat1[7] += [overlap]

    overlap_mat1 += [[]]
    for meth2 in range(len(methods)):
        overlap = 0
        for q in range(0,10):
            selected1 = all_selected2[3][q].union(all_selected2[4][q])
            selected2 = all_selected2[meth2][q]
            if len(selected2)!=0:
                overlap += len(selected1.intersection(selected2))/len(selected2)
            else:
                overlap += 1
        overlap = overlap/10
        overlap_mat1[8] += [overlap]
    
    overlap_mat1 += [[]]
    for meth2 in range(len(methods)):
        overlap = 0
        for q in range(0,10):
            selected1 = all_selected2[5][q].union(all_selected2[6][q])
            selected2 = all_selected2[meth2][q]
            if len(selected2)!=0:
                overlap += len(selected1.intersection(selected2))/len(selected2)
            else:
                overlap += 1
        overlap = overlap/10
        overlap_mat1[9] += [overlap]
    print(overlap_mat1)

def search_time(method,query,n_results,acts,sessions,TFIDF,LSA,WORD2VECS,GLOVE,BI_ENCODER,EMBEDINGS,CROSS_ENCODER,strip):
    t = 0
    for f in range(20):
        start = time.time()
        results = ss.run_similarity(method,query,n_results,acts,sessions,TFIDF,LSA,WORD2VECS,GLOVE,BI_ENCODER,EMBEDINGS,CROSS_ENCODER,strip)
        end = time.time()
        t += end - start
    print(t/20)

# gives default values to some session variables 
@app.before_request
def initialise_var():
    if not SESSION.get("scrape"):
        SESSION["scrape"] = False
    if not SESSION.get("delete"):
        SESSION["delete"] = False
    if not SESSION.get("search"):
        SESSION["search"] = False

@login_manager.user_loader
def loader_user(user_id):
    return db.session.scalars(select(User).where(User.id==user_id)).first()

# loads the home page and processes search requests
@app.route('/', methods=["POST","GET"])
def search():
    if request.method == "POST":
        # prevent search with empty database
        if not HAVE_MOTION or not HAVE_SPLIT:
            return redirect("/")
        # store form variables to session
        # then reqirect to home page as a GET request to prevent need for form resubmission requests
        elif request.form["submit_buttom"] == "Show More Results":
            # overrides if origonal form was changed between search and request for more results
            # only increases number of results to return
            SESSION["n_results"] += SESSION["n_initial_results"]
        else:
            SESSION["n_initial_results"] = int(request.form["num_results"])
            SESSION["n_results"] = int(request.form["num_results"])
            SESSION["search_query"] = request.form["search_query"]
            SESSION["method"] = request.form["search_method"]
            SESSION["start_session"] = request.form["session_start"]
            SESSION["end_session"] = request.form["session_end"]
            SESSION["actions"] = request.form.getlist("actions")
            SESSION["meeting"] = request.form["meeting"]
        SESSION["search"] = True
        return redirect("/")
    else:
        if not HAVE_MOTION or not HAVE_SPLIT:
            return render_template("index.html",missing_data=True,user=is_user(),admin=is_admin())
        else:
            # get list of all actions to display on the page and list of all sessions for select drop down list
            all_actions = ["All"] + get_actions()
            all_sessions = get_sessions()
            # get default home page without request or results
            if not SESSION["search"]:
                actions = [[a,False] for a in all_actions]
                actions[0][1] = True
                sel_sessions = [all_sessions[0],all_sessions[-1]]
                meetings = [[m,False] for m in gv.MEETINGS]
                meetings[0][1] = True
                return render_template("index.html",splits=[],motions_content="",search_methods=gv.SEARCH_METHODS,method=gv.SEARCH_METHODS[0],
                                    allow_more=False,n_results=10,user=is_user(),admin=is_admin(),actions=actions,sessions=all_sessions,sel_sessions=sel_sessions,meetings=meetings)
            # load home page with results
            else:
                SESSION["search"] = False
                # get seperate list of actions selected by the user for processing search and to reselect
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
                # get seperate list of sessions selected by the user for processing search and to reselect
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
                meetings = []
                for m in gv.MEETINGS:
                    if m == SESSION["meeting"]:
                        meetings += [[m,True]]
                    else:
                        meetings += [[m,False]]
                # run search with specific method
                # returns list of split ids and distances
                results = ss.run_similarity(SESSION["method"],SESSION["search_query"],SESSION["n_results"],acts,sessions,SESSION["meeting"],TFIDF,LSA,WORD2VECS,GLOVE,BI_ENCODER,EMBEDINGS,CROSS_ENCODER,strip=gv.STRIP)
                # get the all the details for each split that will be used in the results table
                splits = ss.get_split_details(results,gv.UCU_WEBSITE_URL)
                # create list of splits and full motions that can be processed by javascript to allow the results to expand and show the full motion
                motions = [[str(s[0]),string_to_safe(s[2]),string_to_safe(s[3])] for s in splits]
                # used for processing relevant submission as form only returns splits selected not all splits
                SESSION["ids"] = [s[0] for s in splits]
                SESSION["similarities"] = [s[1] for s in splits]
                return render_template("index.html",splits=splits,search_query=SESSION["search_query"],search_methods=gv.SEARCH_METHODS,
                                    method=SESSION["method"],allow_more=True,n_results=SESSION["n_initial_results"],actions=sel_acts,
                                    sessions=all_sessions,sel_sessions=sel_sessions,meetings=meetings,motions=motions,relevant_submit=True,user=is_user(),admin=is_admin())

# allow admins to scrape the UCU website for motions
@app.route('/scrape_motions', methods=["POST","GET"])
def scrape():
    global HAVE_MOTION, HAVE_SPLIT
    # only allow admins to perform scrape or access page
    if is_admin():
        if request.method == "POST":
            # require user confirmation before deletion 
            if request.form["submit_buttom"] == "Delete":
                # remove existing motions and splits that overlap
                splits = db.session.execute(select(Split).where(Split.motion_id>=SESSION["start_scrape"],Split.motion_id<SESSION["end_scrape"])).all()
                motions = db.session.execute(select(Motion).where(Motion.id>=SESSION["start_scrape"],Motion.id<SESSION["end_scrape"])).all()
                split_ids = []
                for s in splits:
                    split_ids += [s[0].id]
                    db.session.delete(s[0])
                motion_ids = []
                for m in motions:
                    motion_ids += [m[0].id]
                    db.session.delete(m[0])
                db.session.commit()
            elif request.form["submit_buttom"] == "Don't Delete":
                return redirect("/scrape_motions")
            else:
                # initial form submition
                SESSION["start_scrape"] = int(request.form["start_scrape"])
                SESSION["end_scrape"] = int(request.form["end_scrape"])+1

                # check for existing motions and splits
                motions = db.session.execute(select(Motion.id).where(Motion.id>=SESSION["start_scrape"],Motion.id<SESSION["end_scrape"])).all()
                splits = db.session.execute(select(Split.id).where(Split.motion_id>=SESSION["start_scrape"],Split.motion_id<SESSION["end_scrape"])).all()
                if len(motions)>0 or len(splits)>0:
                    SESSION["delete"] = True
                    SESSION["m_ids"] = len(motions)
                    SESSION["s_ids"] = len(splits)
                    # request user permission to delete
                    return redirect("/scrape_motions")
            # process scrape request
            start = SESSION["start_scrape"]
            end = SESSION["end_scrape"]
            message, missed, blank = scrape_motions(gv.UCU_WEBSITE_URL,gv.UCU_WEBSITE_CLASSES,start,end)
            SESSION["scrape_message"] = message
            SESSION["missed"] = len(missed)
            SESSION["blank"] = len(blank)
            SESSION["scrape"] = True
            # reinitialise models and embeddings
            HAVE_MOTION = db.session.execute(select(Motion)).all()
            if len(HAVE_MOTION)==0:
                HAVE_MOTION = False

            HAVE_SPLIT = db.session.execute(select(Split)).all()
            if len(HAVE_SPLIT)==0:
                HAVE_SPLIT = False
            if HAVE_SPLIT:
                initialise_models()
            return redirect("/scrape_motions")
        else:
            if SESSION["scrape"]:
                SESSION["scrape"] = False
                # render successful scrape message
                return render_template("scrape_motions.html",user=is_user(),admin=is_admin(),scraped=True,message=SESSION["scrape_message"],missed=SESSION["missed"],blank=SESSION["blank"])
            if SESSION["delete"]:
                SESSION["delete"] = False
                # render deletion request
                return render_template("scrape_motions.html",user=is_user(),admin=is_admin(),delete=True,m_ids=SESSION["m_ids"],s_ids=SESSION["s_ids"])
            else:
                # render default scrape motion page
                return render_template("scrape_motions.html",user=is_user(),admin=is_admin())
    else:
        return redirect("/")

# allow users to provided feedback on which of the results returned were relevant to their search
@app.route('/relevance', methods=["POST"])
def relevance():
    if request.method == "POST":
        if current_user.is_anonymous:
            user = 0
        else:
            user = current_user.id
        # get splits marked as relevant and list of all result splits
        relevant = request.form.getlist("relevant")
        ids = SESSION["ids"]
        # find existing queries with the same question
        query = db.session.scalars(select(SearchQuery).where(SearchQuery.question==SESSION["search_query"])).first()
        if query is None:
            # if none exist create new SearchQuery
            query = SearchQuery(question=SESSION["search_query"])
            db.session.add(query)
            db.session.commit()
        # get current highest RelevantResults id
        id_obj = db.session.scalars(select(func.max(RelevantResults.id))).first()
        if id_obj is not None:
            rel_id = id_obj+1
        else:
            rel_id = 1
        # for each result Split link with SearchQuery and User in RelevantResults
        for f in range(len(ids)):
            id = ids[f]
            if str(id) in relevant:
                rel = True
            else:
                rel = False
            result = RelevantResults(id=rel_id,user_id=user,query_id=query.id,split_id=id,relevant=rel,method=SESSION["method"],similarity=SESSION["similarities"][f])
            rel_id += 1
            db.session.add(result)
        db.session.commit()
        return redirect("/")
    else:
        return redirect("/")

# allows admins to perform evaluation of search methods using 2023-2024 splits as search queries
@app.route('/survey', methods=["POST","GET"])
def survey():
    if not is_admin():
        return redirect("/")
    else:
        if request.method == "POST":
            # for each result Split link with SearchQuery and User in RelevantResults
            user = current_user.id
            relevant = request.form.getlist("relevant")
            query = db.session.execute(select(SearchQuery).where(SearchQuery.id==SESSION["query_id"])).first()
            query=query[0]
            for f in range(10):
                id = SESSION["result_ids"][f]
                sim = SESSION["similarities"][f]
                id_obj = db.session.scalars(select(func.max(RelevantResults.id))).first()
                if id_obj is not None:
                    rel_id = id_obj+1
                else:
                    rel_id = 1
                if str(id) in relevant:
                    rel_res = RelevantResults(id=rel_id,user_id=user,query_id=query.id,split_id=id,relevant=True,method=SESSION["method2"],similarity=sim)
                else:
                    rel_res = RelevantResults(id=rel_id,user_id=user,query_id=query.id,split_id=id,relevant=False,method=SESSION["method2"],similarity=sim)
                db.session.add(rel_res)
            db.session.commit()
            # change search method if specified by user
            SESSION["method2"] = request.form["search_method"]
            return redirect("/survey")
        else:
            if not SESSION.get("method2"):
                SESSION["method2"] = gv.SEARCH_METHODS[0]
            user = current_user.id
            # find all SearchQuerys the user has already provided relevant splits for using the method selected
            answered = db.session.execute(select(SearchQuery.split_id).join(RelevantResults).where(RelevantResults.user_id==user,RelevantResults.method==SESSION["method2"]).distinct()).all()
            answered_ids = []
            for a in answered:
                answered_ids += a
            # check if there are any active SearchQueries the user hasn't provided an answer for using the method selected
            query = db.session.execute(select(SearchQuery).where(SearchQuery.split_id.not_in(answered_ids),SearchQuery.split_id!=None)).first()
            if query is None:
                # if not generate new SearchQuery by selecting a random split from the 2023-2024 session
                split = db.session.execute(select(Split).join(Motion).where(Split.id.not_in(answered_ids),Motion.session=="2023-2024").order_by(func.random())).first()
                if split is None:
                    return render_template("survey.html",user=is_user(),admin=is_admin(),finished=True)
                else:
                    split = split[0]
                query = SearchQuery(question=split.content,split_id=split.id)
                db.session.add(query)
                db.session.commit()
            else:
                query = query[0]
            # run search on split, excluding results from the 2023-2024 session
            acts = ["All"] + get_actions()
            sessions = get_sessions()
            del sessions[sessions.index("2023-2024")]
            results = ss.run_similarity(SESSION["method2"],query.question,10,acts,sessions,gv.MEETINGS[0],TFIDF,LSA,WORD2VECS,GLOVE,BI_ENCODER,EMBEDINGS,CROSS_ENCODER,strip=gv.STRIP)
            splits = ss.get_split_details(results,gv.UCU_WEBSITE_URL)
            motions = [[str(s[0]),string_to_safe(s[2]),string_to_safe(s[3])] for s in splits]
            SESSION["result_ids"] = [s[0] for s in splits]
            SESSION["query_id"] = query.id
            SESSION["similarities"] = [s[1] for s in splits]
            motion_main = string_to_safe(db.session.execute(select(Motion.content).join(Split).where(Split.id==query.split_id)).first()[0])
            # render results table
            return render_template("survey.html",user=is_user(),admin=is_admin(),split_main=string_to_safe(query.question),
                                   motion_main=motion_main,splits=splits,search_query=query.question,motions=motions,search_methods=gv.SEARCH_METHODS,method=SESSION["method2"])

# render help page
@app.route('/help', methods=["GET"])
def help():
    return render_template("help.html",user=is_user(),admin=is_admin())

@app.route('/login', methods=["POST","GET"])
def login():
    if is_user():
        return redirect("/")
    else:
        # check username and password are valid then login user
        if request.method == "POST":
            username = request.form.get("username")
            user = db.session.scalars(select(User).where(User.username==username)).first()
            if user is not None:
                salt = user.salt
                # check password with salt
                password = bcrypt.hashpw(request.form.get("password").encode("utf-8"),salt)
                if password == user.password:
                    login_user(user)
                    return redirect("/")
            return render_template("login.html",user=is_user(),admin=is_admin(),failed=True)
        else:
            return render_template("login.html",user=is_user(),admin=is_admin())

# allow admins to create new users
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
                    return render_template("register.html",user=is_user(),admin=is_admin(),success=True)
                else:
                    return render_template("register.html",user=is_user(),admin=is_admin(),password=True)
            else:
                return render_template("register.html",user=is_user(),admin=is_admin(),username=True)
        else:
            return render_template("register.html",user=is_user(),admin=is_admin())
    else:
        return redirect("/")

@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)#, use_reloader=False)