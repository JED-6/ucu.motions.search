import re
# import chromadb
# from chromadb.utils import embedding_functions
# import math
from project_code.models import *
import project_code.global_variables as gv

def get_split_type(split):
    institutions = ["Congress","Conference","HE Sector Conference","HESC","HEC","Special FE sector conference","SFESC","FESC","UCU","We"]
    for a in gv.ACTIONS:
            if re.search("^"+a,split.strip()):
                return a
            for i in institutions:
                if (re.search(i+r" ([a-zA-Z]* ){0,3}"+a.lower(),split.strip()) or re.search(i.lower()+r" ([a-zA-Z]* ){0,3}"+a.lower(),split.strip()) or
                    re.search(i+r" ([a-zA-Z]* ){0,3}"+a,split.strip()) or re.search(i.lower()+r" ([a-zA-Z]* ){0,3}"+a,split.strip())):
                    return a
    return "Other"

def split_para(text):
    init_splits = re.split("\n *(?=i+\\.? |iv\\.? |vi*\\.? |ix*\\.? |[a-z]\\.? |[0-9]+\\.? |[A-Z])",text)
    splits =[]
    for s in init_splits:
        if not re.search("^[ |`|'|)|\"|”|‘|’]*$",s):
            splits += [s.strip()]
    return(splits)

def split_sentence(split,action):
    splits = re.split("(?<! [a-zA-Z])(?<!ii)(?<!iii)(?<!iv)(?<!vi)(?<!vii)(?<!viii)(?<!ix)(?<!^[a-zA-Z])(?<![0-9])\\.(?![a-z]| [a-z]|[0-9]| [0-9])",split)
    splits_action = []
    for s in splits:
        if not re.search("^[`|'|)|\"|”|‘|’]*$",s.strip()):
            splits_action += [[re.sub("\n"," ",s).strip(),action]]
    return splits_action

def get_motion(extract):
    for line_break in extract.find_all("br"):
        line_break.replace_with("\n")
    motion = ""
    for p in extract.find_all("p"):
        motion += "\n\n" + p.get_text()
    motion = motion.strip()
    return motion

def split_motion_action(motion):
    splits = split_para(motion)
    splits_action = []
    s = 0
    while s < len(splits):
        action = get_split_type(splits[s])
        splits_action += split_sentence(splits[s],action)
        j = 1
        if s+j < len(splits):
            if re.search(":$",splits[s].strip()):
                splits_action += split_sentence(splits[s+j],action)
                j += 1
            if s+j < len(splits):
                while re.search("^(i+\\.? |iv\\.? |vi*\\.? |ix\\.? |[a-zA-Z]\\.? |[0-9]+\\.? )",splits[s+j].strip()):
                    splits_action += split_sentence(splits[s+j],action)
                    j += 1
                    if s+j >= len(splits):
                        break
        s += j
    return splits_action

# def encode_splits(CHROMA_DATA_PATH,MODEL,COLLECTION_NAME,URL_ID_START,URL_ID_END,clear_collection=False):
#     #create embedding collection
#     client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
#     embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL)
#     if clear_collection:
#         try:
#             client.delete_collection(name=COLLECTION_NAME)
#         except:
#             print("Failed to delete collection ",COLLECTION_NAME)
#     collection = client.get_or_create_collection(name=COLLECTION_NAME,embedding_function=embedding_func,metadata={"hnsw:space":"cosine"})

#     #embed splits
#     query = db.session.execute(select(Split.id,Split.content,Split.action,Motion.session).select_from(Split).join(Motion,Motion.id==Split.motion_id).where(Split.motion_id>=URL_ID_START,Split.motion_id<URL_ID_END)).all()
#     ids = []
#     metadata = []
#     splits = []
#     for s in query:
#         ids += [str(s.id)]
#         metadata += [{"action":s.action,"session":s.session}]
#         splits += [s.content]
#     for f in range(0,math.ceil(len(splits)/5000)):
#         collection.add(documents=splits[f*5000:min((f+1)*5000,len(splits))],
#                     ids=ids[f*5000:min((f+1)*5000,len(ids))],
#                     metadatas=metadata[f*5000:min((f+1)*5000,len(ids))])
#     return (True)