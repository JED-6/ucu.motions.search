CHROMA_DATA_PATH = "encodings/"
MODEL = "all-mpnet-base-v2"
COLLECTION_NAME = "splits_embeddings"
ACTIONS = ["Resolve","Demand","Instruct","Insist","Mandate","Believe","Note","Call","Reaffirm","Affirm","Agree","Support",
               "Commend","Welcomes","Ask","Congratulate","Deplore","Recognise","Vote","Endorse","Accept","Approve","Oppose","Condemn",
               "Sends","Undertake","Decide","Pledge","Encourage","Recommends","Will","Urges","Reiterates","Requests","Applauds","Rejects"]

UCU_WEBSITE_URL = "https://policy.web.ucu.org.uk/motion-information/?pdb="
UCU_WEBSITE_CLASSES = {"title":"motion_title","session":"session","meeting":"meeting_link","date":"meeting_date","status":"status","number":"motion_number","content":"motion_text",
                        "proposer":"proposing_body","amended":"amended","subcommittee":"sub_committee","notes":"notes","listing":"ref"}

SEARCH_METHODS = ["all-mpnet-base-v2","tf.idf"]