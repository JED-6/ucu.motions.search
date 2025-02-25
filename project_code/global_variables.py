CHROMA_DATA_PATH = "Data/embeddings/"
MODEL = "all-mpnet-base-v2"
COLLECTION_NAME = "splits_embeddings"

UCU_WEBSITE_URL = "https://policy.web.ucu.org.uk/motion-information/?pdb="
URL_ID_START = 7925
URL_ID_END = 10967
UCU_WEBSITE_CLASSES = {"title":"motion_title","session":"session","meeting":"meeting_link","date":"meeting_date","status":"status","number":"motion_number","content":"motion_text",
                        "proposer":"proposing_body","amended":"amended","subcommittee":"sub_committee","notes":"notes","listing":"ref"}
COLLECTION_INITIALIZED = False