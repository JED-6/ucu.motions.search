import time
import re
import requests
import xlsxwriter
from bs4 import BeautifulSoup

motion_url = "https://policy.web.ucu.org.uk/motion-information/?pdb="
attributes = ["motion_title","session","meeting_link","meeting_date","status","motion_number","motion_text",
              "proposing_body","amended","sub_committee","notes","ref"]

workbook = xlsxwriter.Workbook("UCU Motions 2024-2006.xlsx")
worksheet = workbook.add_worksheet()

motions = ["Title","Session","Meeting","Date","Status","Number","Contents","Proposer","Amendment Status","Subcommittee","Notes","ID"]

start_id = 7925
end_id = 10967

try:
    row = 0
    print("Scraping Motions ...")
    print("0% complete ...")
    for motion_num in range(start_id,end_id):
        r = requests.get(motion_url+str(motion_num))
        soup = BeautifulSoup(r.content,"html.parser")
        if soup.find("p", class_="alert alert-error") is None:
            column = 0
            motion = []
            for att in attributes:
                extract = soup.find("dd", class_=att)
                if extract is not None:
                    for line_break in extract.findAll("br"):
                        line_break.replaceWith("\n")
                    motion.append(extract.get_text())
                    worksheet.write(row, column, extract.get_text())
                column += 1
            motions.append(motion)
            row += 1
        if ((motion_num-start_id)/(end_id-start_id))*10 == round(((motion_num-start_id)/(end_id-start_id))*10):
            print(((motion_num-start_id)/(end_id-start_id))*100,"% complete ...")
except:
    print("something went wrong")
workbook.close()
print(len(motions))
