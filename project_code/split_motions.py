import re
from project_code.models import *
import project_code.global_variables as gv

# assign split action type
def get_split_type(split):
    for a in gv.ACTIONS:
            if re.search("^"+a,split.strip()):
                return a
            for i in gv.INSTITUTIONS:
                # check if action occurs within 4 words of an institution
                if (re.search(i+r" ([a-zA-Z]* ){0,3}"+a.lower(),split.strip()) or re.search(i.lower()+r" ([a-zA-Z]* ){0,3}"+a.lower(),split.strip()) or
                    re.search(i+r" ([a-zA-Z]* ){0,3}"+a,split.strip()) or re.search(i.lower()+r" ([a-zA-Z]* ){0,3}"+a,split.strip())):
                    return a
    return "Other"

# split on ordered list items
def split_para(text):
    init_splits = re.split("\n *(?=i+\\.? |iv\\.? |vi*\\.? |ix*\\.? |[a-z]\\.? |[0-9]+\\.? |[A-Z])",text)
    splits =[]
    for s in init_splits:
        # remove splits that are only punctuation
        if not re.search("^[ |`|'|)|\"|”|‘|’]*$",s):
            splits += [s.strip()]
    return(splits)

# split into sentences
# only split when full stop followed by space and capital letter to avoid over splitting 
def split_sentence(split,action):
    splits = re.split("(?<! [a-zA-Z])(?<!ii)(?<!iii)(?<!iv)(?<!vi)(?<!vii)(?<!viii)(?<!ix)(?<!^[a-zA-Z])(?<![0-9])\\.(?![a-z]| [a-z]|[0-9]| [0-9])",split)
    splits_action = []
    for s in splits:
        s = s.strip()
        if not re.match("^(`|'|\\(|\\)|\"|”|‘|’|:|\\.)*$",s) and not re.match("^(`|'|\\(|\\)|\"|”|‘|’|:|\\.|s|"+gv.WORDS+")*$",s,re.IGNORECASE):
            splits_action += [[re.sub("\n"," ",s).strip(),action]]
    return splits_action

# convert HTML elements to line breaks
def get_motion(extract):
    for line_break in extract.find_all("br"):
        line_break.replace_with("\n")
    motion = ""
    for p in extract.find_all("p"):
        motion += "\n\n" + p.get_text()
    motion = motion.strip()
    return motion

# split motion and assign split action types
def split_motion_action(motion):
    splits = split_para(motion)
    splits_action = []
    s = 0
    while s < len(splits):
        action = get_split_type(splits[s])
        splits_action += split_sentence(splits[s],action)
        j = 1
        if s+j < len(splits):
            # give splits following ":" or that make up and ordered list the same action type as above split
            if re.search(":$",splits[s].strip()):
                splits_action += split_sentence(splits[s+j],action)
                j += 1
            if s+j < len(splits):
                while re.search("^(i+\\.? |iv\\.? |vi*\\.? |ix\\.? |[a-zA-Z]\\.? |[0-9]+\\.? )",splits[s+j].strip()):
                    splits_action += split_sentence(splits[s+j],action)
                    j += 1
                    if s+j >= len(splits):
                        break
        s += j
    return splits_action