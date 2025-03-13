BI_ENCODER_NAME = "all-mpnet-base-v2"
CROSS_ENCODER_NAME = "msmarco-MiniLM-L6-en-de-v1"
STRIP = True

ACTIONS = ["Resolve","Demand","Instruct","Insist","Mandate","Believe","Note","Call","Reaffirm","Affirm","Agree","Support",
               "Commend","Welcomes","Ask","Congratulate","Deplore","Recognise","Vote","Endorse","Accept","Approve","Oppose","Condemn",
               "Sends","Undertake","Decide","Pledge","Encourage","Recommends","Will","Urges","Reiterates","Requests","Applauds","Rejects"]
INSTITUTIONS = ["Congress","Conference","HE Sector Conference","HESC","HEC","Special FE sector conference","SFESC","FESC","UCU","We"]

import nltk
from nltk.corpus import stopwords
WORDS = " "
for w in ACTIONS:
    WORDS += "|"+w
for w in INSTITUTIONS:
    WORDS += "|"+w
for w in stopwords.words("english"):
    WORDS += "|"+w


UCU_WEBSITE_URL = "https://policy.web.ucu.org.uk/motion-information/?pdb="
UCU_WEBSITE_CLASSES = {"title":"motion_title","session":"session","meeting":"meeting_link","date":"meeting_date","status":"status","number":"motion_number","content":"motion_text",
                        "proposer":"proposing_body","amended":"amended","subcommittee":"sub_committee","notes":"notes","listing":"ref"}

SEARCH_METHODS = ["tf.idf","Word Overlap",BI_ENCODER_NAME,CROSS_ENCODER_NAME,"tf.idf with Cross Encoder"]