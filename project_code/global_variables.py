# predefined sentence-transformers model
BI_ENCODER_NAME = "all-mpnet-base-v2"
# predefined cross-encoder model
CROSS_ENCODER_NAME = "msmarco-MiniLM-L6-en-de-v1"
# whether to clean and normalise inputs for above models
STRIP = True

# predefined list of actions and institutions
ACTIONS = ["Resolve","Demand","Instruct","Insist","Mandate","Believe","Note","Call","Reaffirm","Affirm","Agree","Support",
               "Commend","Welcomes","Ask","Congratulate","Deplore","Recognise","Vote","Endorse","Accept","Approve","Oppose","Condemn",
               "Sends","Undertake","Decide","Pledge","Encourage","Recommends","Will","Urges","Reiterates","Requests","Applauds","Rejects"]
# action types are found by looking for one of these institutions followed closely by an action 
INSTITUTIONS = ["Congress","Conference","HE Sector Conference","HESC","HEC","Special FE sector conference","SFESC","FESC","UCU","We"]

# generates regex expression from list of words
# if a split is made up of only these words and punctuation it will be removed
from nltk.corpus import stopwords
WORDS = " "
for w in ACTIONS:
    WORDS += "|"+w
for w in INSTITUTIONS:
    WORDS += "|"+w
for w in stopwords.words("english"):
    WORDS += "|"+w

# website URL which, when combined with motion id links to UCU website page for that motion
UCU_WEBSITE_URL = "https://policy.web.ucu.org.uk/motion-information/?pdb="
# predefined dict of desired attributes and HTML classes
UCU_WEBSITE_CLASSES = {"title":"motion_title","session":"session","meeting":"meeting_link","date":"meeting_date","status":"status","number":"motion_number","content":"motion_text",
                        "proposer":"proposing_body","amended":"amended","subcommittee":"sub_committee","notes":"notes","listing":"ref"}
# list of search methods
SEARCH_METHODS = ["tf.idf","Word Overlap",BI_ENCODER_NAME,CROSS_ENCODER_NAME,"tf.idf with Cross Encoder"]