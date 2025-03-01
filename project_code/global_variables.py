CHROMA_DATA_PATH = "encodings/"
MODEL = "all-mpnet-base-v2"
COLLECTION_NAME = "splits_embeddings"

UCU_WEBSITE_URL = "https://policy.web.ucu.org.uk/motion-information/?pdb="
UCU_WEBSITE_CLASSES = {"title":"motion_title","session":"session","meeting":"meeting_link","date":"meeting_date","status":"status","number":"motion_number","content":"motion_text",
                        "proposer":"proposing_body","amended":"amended","subcommittee":"sub_committee","notes":"notes","listing":"ref"}

SEARCH_METHODS = ["all-mpnet-base-v2","tf.idf"]