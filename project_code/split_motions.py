import re
import chromadb
from chromadb.utils import embedding_functions
import math
from project_code.models import Split, Motion, db

def split_motion(text):
    splits_O = re.split("\n *(?:i+|[a-z]+|[0-9]+)\\. *",text)
    splits_T = []
    for s in range(0,len(splits_O)):
        splits_O[s] = re.sub("\n"," ",splits_O[s])
        splits_O[s] = re.sub(" *$","",splits_O[s])
        splits_T = splits_T + re.split("\\. *", splits_O[s])
        if len(splits_T[-1]) == 0:
            splits_T = splits_T[:-1]
    return(splits_T)

def split_motions(CHROMA_DATA_PATH,MODEL,COLLECTION_NAME):
    motions = Motion.query.with_entities(Motion.id,Motion.content).all()
    id = 0
    for motion in motions:
        splits = split_motion(motion.content)
        for s in splits:
            if len(s)>0:
                split = Split(id=id,content=s,motion_id=motion.id)
                db.session.add(split)
                id += 1
    db.session.commit()
    
    #create embedding collection
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL)
    collection = client.create_collection(name=COLLECTION_NAME,embedding_function=embedding_func,metadata={"hnsw:space":"cosine"})

    #embed splits
    query = Split.query.with_entities(Split.id,Split.content).order_by(Split.id).all()
    ids = [s.id for s in query]
    splits = [s.content for s in query]
    for f in range(0,math.ceil(len(splits)/5000)):
        collection.add(documents=splits[f*5000:min((f+1)*5000,len(splits))],
                       ids=list(map(str,ids[f*5000:min((f+1)*5000,len(ids))])))
    return (True)