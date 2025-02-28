import re
import math
import requests
from bs4 import BeautifulSoup
from project_code.models import Motion, Split, db, clear_motions_db

def get_split_type(split):
    actions = ["resolve","demands","instructs","insists","mandates","believe","notes","calls","agrees","welcomes","asks","congradulates","deplores"]
    institutions = ["Congress","HE Sector Conference", "HESC", "Conference"]
    for a in actions:
            for i in institutions:
                if re.search(i+r" ([\w] ){0,3}"+a,split) or re.search(i.lower()+r" ([\w] ){0,3}"+a,split):
                    return a
    return "Other"

def split_motion(text):
    splits_O = re.split("\n *(?=i+\\.|iv\\.|vi*\\.|ix*\\.|[a-zA-Z]\\.|[0-9]+\\. )",text)
    splits_T = []
    for s in range(0,len(splits_O)):
        splits_O[s] = re.sub("\n"," ",splits_O[s])
        splits_T = splits_T + re.split("(?<! [a-zA-Z])(?<!^ii)(?<!^iii)(?<!^iv)(?<!^vi)(?<!^vii)(?<!^viii)(?<!^ix)(?<!^[a-zA-Z])(?<![0-9])\\.(?![a-zA-z]|[0-9]| [0-9]| g.)",
                                       splits_O[s])
    s = 0
    while s < len(splits_T):
        if re.search("^[ |`|'|)|\"|”|‘|’]*$",splits_T[s]):
            splits_T = splits_T[:s] + splits_T[(s+1):]
        else:
            splits_T[s] = splits_T[s].lstrip() 
            s += 1
    return(splits_T)

def split_motion_2(motion):
    splits_init = []
    for p in motion.find_all("p"):
        splits_init += [p.get_text()]
    
    s = 0
    while s < len(splits_init)-1:
        if re.search(":$",splits_init[s].lstrip()):
            if not re.search("^\n",splits_init[s+1]):
                splits_init[s] = splits_init[s] + "\n" + splits_init[s+1]
            else:
                splits_init[s] = splits_init[s] + splits_init[s+1]
        while re.search("^(i+\\.|iv\\.|vi*\\.|ix\\.|[a-zA-Z]\\.|[0-9]+\\.)",splits_init[s+1].lstrip()):
            if not re.search("^\n",splits_init[s+1]):
                splits_init[s] = splits_init[s] + "\n" + splits_init[s+1]
            else:
                splits_init[s] = splits_init[s] + splits_init[s+1]
            del splits_init[s+1]
            if s == len(splits_init)-1:
                break
        s += 1
    final_splits = []
    for s in range(len(splits_init)):
        action = get_split_type(splits_init[s])
        splits = split_motion(splits_init[s])
        for split in splits:
                final_splits += [[split,action]]
    return final_splits

def scrape_motions(UCU_WEBSITE_URL,URL_ID_START,URL_ID_END,UCU_WEBSITE_CLASSES):
    clear_motions_db()

    completed = 0
    motions = 0
    print("Scraping Motions ...")
    try:
        id = 0
        for motion_num in range(URL_ID_START,URL_ID_END):
            r = requests.get(UCU_WEBSITE_URL+str(motion_num))
            soup = BeautifulSoup(r.content,"html.parser")
            if soup.find("p", class_="alert alert-error") is None:
                motion = dict.fromkeys(UCU_WEBSITE_CLASSES.values())
                for att in UCU_WEBSITE_CLASSES.values():
                    extract = soup.find("dd", class_=att)
                    if extract is not None:
                        if att == UCU_WEBSITE_CLASSES["content"]:
                            for line_break in extract.find_all("br"):
                                line_break.replace_with("\n")
                            m = ""
                            for p in extract.find_all("p"):
                                m += "\n\n" + p.get_text()
                            motion[att] = m[2:]
                            splits = split_motion_2(extract)
                            for s in splits:
                                split = Split(id=id,content=s[0],motion_id=motion_num,split_type=s[1])
                                db.session.add(split)
                                id += 1
                        else:
                            motion[att] = extract.get_text()
                if motion[UCU_WEBSITE_CLASSES["amended"]] == "Yes":
                    amended = True
                else:
                    amended = False
                new_motion = Motion(id=motion_num,title=motion[UCU_WEBSITE_CLASSES["title"]],session=motion[UCU_WEBSITE_CLASSES["session"]],
                                    meeting=motion[UCU_WEBSITE_CLASSES["meeting"]],date=motion[UCU_WEBSITE_CLASSES["date"]],status=motion[UCU_WEBSITE_CLASSES["status"]],
                                    number=motion[UCU_WEBSITE_CLASSES["number"]],content=motion[UCU_WEBSITE_CLASSES["content"]],proposer=motion[UCU_WEBSITE_CLASSES["proposer"]],
                                    amended=amended,subcommittee=motion[UCU_WEBSITE_CLASSES["subcommittee"]],notes=motion[UCU_WEBSITE_CLASSES["notes"]],
                                    listing=motion[UCU_WEBSITE_CLASSES["listing"]])
                db.session.add(new_motion)
                motions += 1
            if completed <= math.floor(((motion_num-URL_ID_START)/(URL_ID_END-URL_ID_START))*10):
                completed += 1
                print(math.floor(((motion_num-URL_ID_START)/(URL_ID_END-URL_ID_START))*100),"% complete ...")
        db.session.commit()
        print("100% complete")
        return str(motions) + " motions scraped from UCU website"
    except:
         return "Something whent wrong!"