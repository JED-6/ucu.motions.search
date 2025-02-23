import math
import requests
from bs4 import BeautifulSoup
from project_code.models import Motion, db

def scrape_motions():
    start_id = 7925
    end_id = 10967
    motion_url = "https://policy.web.ucu.org.uk/motion-information/?pdb="

    attributes = ["motion_title","session","meeting_link","meeting_date","status","motion_number","motion_text",
                "proposing_body","amended","sub_committee","notes","ref"]
    completed = 0
    motions = 0
    print("Scraping Motions ...")
    try:
        for motion_num in range(start_id,end_id):
            r = requests.get(motion_url+str(motion_num))
            soup = BeautifulSoup(r.content,"html.parser")
            if soup.find("p", class_="alert alert-error") is None:
                motion = dict.fromkeys(attributes)
                for att in attributes:
                    extract = soup.find("dd", class_=att)
                    if extract is not None:
                        for line_break in extract.find_all("br"):
                            line_break.replace_with("\n")
                        motion[att] = extract.get_text()
                if motion["status"] == "Yes":
                    status = True
                else:
                    status = False
                new_motion = Motion(id=motion_num,title=motion["motion_title"],session=motion["session"],meeting=motion["meeting_link"],date=motion["meeting_date"],
                                    status=motion["status"],number=motion["motion_number"],content=motion["motion_text"],proposer=motion["proposing_body"],amended=status,
                                    subcommittee=motion["sub_committee"],notes=motion["notes"],listing=motion["ref"])
                db.session.add(new_motion)
                motions += 1
            if completed <= math.floor(((motion_num-start_id)/(end_id-start_id))*10):
                completed += 1
                print(math.floor(((motion_num-start_id)/(end_id-start_id))*100),"% complete ...")
        db.session.commit()
        print("100% complete")
    except:
        print("Something whent wrong!")
    print(motions," motions scraped from UCU website")