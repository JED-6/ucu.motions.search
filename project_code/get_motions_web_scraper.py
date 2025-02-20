import math
import requests
import xlsxwriter
from bs4 import BeautifulSoup

def scrape_motions():
    start_id = 7925
    end_id = 10967
    motion_url = "https://policy.web.ucu.org.uk/motion-information/?pdb="

    attributes = ["motion_title","session","meeting_link","meeting_date","status","motion_number","motion_text",
                "proposing_body","amended","sub_committee","notes","ref"]

    workbook = xlsxwriter.Workbook("Data/UCU_Motions_2024-2006.xlsx")
    worksheet = workbook.add_worksheet()

    titles = ["Title","Session","Meeting","Date","Status","Number","Contents","Proposer","Amendment Status","Subcommittee","Notes","ID","Link Number"]
    column = 0
    for title in titles:
        worksheet.write(0, column, title)
        column += 1

    motions = []
    row = 1
    completed = 0
    print("Scraping Motions ...")
    try:
        for motion_num in range(start_id,end_id):
            r = requests.get(motion_url+str(motion_num))
            soup = BeautifulSoup(r.content,"html.parser")
            if soup.find("p", class_="alert alert-error") is None:
                column = 0
                motion = []
                for att in attributes:
                    extract = soup.find("dd", class_=att)
                    if extract is not None:
                        for line_break in extract.find_all("br"):
                            line_break.replace_with("\n")
                        motion.append(extract.get_text())
                        worksheet.write(row, column, extract.get_text())
                    column += 1
                motion.append(motion_num)
                worksheet.write(row, column, motion_num)
                motions.append(motion)
                row += 1
            if completed <= math.floor(((motion_num-start_id)/(end_id-start_id))*10):
                completed += 1
                print(math.floor(((motion_num-start_id)/(end_id-start_id))*100),"% complete ...")
        print("100% complete")
    except:
        print("Something whent wrong!")
    workbook.close()
    print(len(motions)," motions scraped from UCU website")

scrape_motions()