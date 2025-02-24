import math
import requests
from bs4 import BeautifulSoup
from project_code.models import Motion, db

def scrape_motions(UCU_WEBSITE_URL,URL_ID_START,URL_ID_END,UCU_WEBSITE_CLASSES):
    completed = 0
    motions = 0
    print("Scraping Motions ...")
    try:
        for motion_num in range(URL_ID_START,URL_ID_END):
            r = requests.get(UCU_WEBSITE_URL+str(motion_num))
            soup = BeautifulSoup(r.content,"html.parser")
            if soup.find("p", class_="alert alert-error") is None:
                motion = dict.fromkeys(UCU_WEBSITE_CLASSES.values())
                for att in UCU_WEBSITE_CLASSES.values():
                    extract = soup.find("dd", class_=att)
                    if extract is not None:
                        for line_break in extract.find_all("br"):
                            line_break.replace_with("\n")
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
    except:
        print("Something whent wrong!")
    print(motions," motions scraped from UCU website")