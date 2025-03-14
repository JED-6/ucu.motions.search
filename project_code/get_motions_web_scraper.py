import math
import requests
from bs4 import BeautifulSoup
from project_code.models import Motion, Split, db, clear_motions_db
import project_code.split_motions as sm

def scrape_motions(UCU_WEBSITE_URL,UCU_WEBSITE_CLASSES,START,END,clear_db=False):
    if clear_db:
        #CLEARS DATABASE of existing motions and splits
        clear_motions_db()

    missed = []
    blank = []
    completed = 0
    motions = 0
    id = 0
    print("Scraping Motions ...")
    for motion_num in range(START,END):
        # extract webpage using fixed initial URL and motion id number
        r = requests.get(UCU_WEBSITE_URL+str(motion_num))
        soup = BeautifulSoup(r.content,"html.parser")
        # if webpage is not blank
        # there are some blank pages between motion pages
        if soup.find("p", class_="alert alert-error") is None:
            try:
                # extract the predefined motion features
                # find HTML elements by predefined list of classes
                motion = dict.fromkeys(UCU_WEBSITE_CLASSES.values())
                for att in UCU_WEBSITE_CLASSES.values():
                    extract = soup.find("dd", class_=att)
                    if extract is not None:
                        if att == UCU_WEBSITE_CLASSES["content"]:
                            # from the motion content also generate the splits
                            motion[att] = sm.get_motion(extract)
                            splits = sm.split_motion_action(motion[att])
                            for s in splits:
                                split = Split(id=id,content=s[0],motion_id=motion_num,action=s[1])
                                db.session.add(split)
                                id += 1
                        else:
                            motion[att] = extract.get_text()
                # convert amended from Yes or No to Boolean
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
                db.session.commit()
            except:
                # make note of failed motion extraction
                missed += [motion_num]
        else:
            # make note of blank motion pages
            blank += [motion_num]
        # display to console progress
        if completed <= math.floor(((motion_num-START)/(END-1-START))*10):
            completed += 1
            print(math.floor(((motion_num-START)/(END-1-START))*100),"% complete ...")
    return str(motions) + " motions scraped from UCU website", missed, blank