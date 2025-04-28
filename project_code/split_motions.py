import re
import math
from project_code.models import *
import project_code.global_variables as gv
from project_code.sentence_similarity import strip_text

# convert HTML elements to line breaks
def get_motion(extract):
    for line_break in extract.find_all("br"):
        line_break.replace_with("\n")
    motion = ""
    for p in extract.find_all("p"):
        motion += "\n\n" + p.get_text()
    motion = motion.strip()
    return motion

# assign split action type
def get_split_type(split):
    for a in gv.ACTIONS:
            if re.search("^"+a,split):
                return a
            for i in gv.INSTITUTIONS:
                # check if action occurs within 4 words of an institution
                if (re.search(i+r" ([a-zA-Z]* ){0,3}"+a.lower(),split) or re.search(i.lower()+r" ([a-zA-Z]* ){0,3}"+a.lower(),split) or
                    re.search(i+r" ([a-zA-Z]* ){0,3}"+a,split) or re.search(i.lower()+r" ([a-zA-Z]* ){0,3}"+a,split)):
                    return a
    return "Other"

# split motion and assign split action types
def split_motion_action(motion):
    # split on ordered list items and paragraphs
    init_splits = re.split("\n *(?=i+\\.? |iv\\.? |vi*\\.? |ix*\\.? |[a-z]\\.? |[0-9]+\\.? |[A-Z]|•|§)",motion)
    splits_actions1 =[]
    for s in init_splits:
        # remove splits that are only numbers and punctuation
        if re.search("[a-zA-Z]",s):
            splits_actions1 += [[s.strip(),get_split_type(s)]]

    splits_actions2 = []
    for s1 in range(len(splits_actions1)):
        init_splits = re.split("(?<! [a-zA-Z])(?<!ii)(?<!iii)(?<!iv)(?<!vi)(?<!vii)(?<!viii)(?<!ix)(?<!^[a-zA-Z])(?<![0-9])\\.(?![a-z]| [a-z]|[0-9]| [0-9])",splits_actions1[s1][0])
        if splits_actions1[s1][0][-1] == ":" and s1 < len(splits_actions1)-1 and splits_actions1[s1][1] != "Other":
            splits_actions1[s1+1][1] = splits_actions1[s1][1]
        if s1 > 0:
            if re.search("^(i+\\.? |iv\\.? |vi*\\.? |ix\\.? |[a-zA-Z]\\.? |[0-9]+\\.? |•|§)",splits_actions1[s1][0]) and splits_actions1[s1-1][1] != "Other":
                splits_actions1[s1][1] = splits_actions1[s1-1][1]
        for s2 in init_splits:
            s2 = s2.strip()
            if re.match("[a-zA-Z]",s2) and not re.match("^("+gv.WORDS+")*$",re.sub(r'[^\w\s]', '', s2),re.IGNORECASE):
                action = get_split_type(s2)
                if action == "Other":
                    splits_actions2 += [[s2.strip(),splits_actions1[s1][1]]]
                else:
                    splits_actions2 += [[s2.strip(),action]]
    
    return(splits_actions2)

def resplit_motions():
    relevant = db.session.execute(select(RelevantResults)).all()
    for rel in relevant:
        rel = rel[0]
        db.session.delete(rel)

    splits = db.session.execute(select(Split)).all()
    for split in splits:
        split = split[0]
        db.session.delete(split)
    
    id = 0
    motions = db.session.execute(select(Motion)).all()
    n_motions = len(motions)
    completed = 0
    for m in range(n_motions):
        motion = motions[m][0]
        splits = split_motion_action(motion.content)
        for s in splits:
            nor_split = strip_text(s[0])
            split = Split(id=id,content=s[0],motion_id=motion.id,nor_content=nor_split,action=s[1])
            db.session.add(split)
            id += 1
        if completed <= math.floor(((m)/(n_motions))*10):
            print(math.floor((completed)*10),"% complete ...", end='\r')
            completed += 1
    print("100% complete ...")
    db.session.commit()