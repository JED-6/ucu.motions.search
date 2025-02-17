import pandas as pd
import re
from sentence_similarity import initialise_model
import chromadb
from chromadb.utils import embedding_functions
import math

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

def split_motions():
    df = pd.read_excel("Data/UCU_Motions_2024-2006.xlsx")
    split_motions = {"Contents":[],"ID":[],"index":[]}
    for m in range(0,len(df)):
        splits = split_motion(df.iloc[m,6])
        split_motions["Contents"] = split_motions["Contents"] + splits
        split_motions["ID"] = split_motions["ID"] + [df.iloc[m,11] for f in range(0,len(splits))]
    split_motions["index"] = [f for f in range(0,len(split_motions["Contents"]))]
    split_motions = pd.DataFrame(split_motions)
    split_motions.to_excel("Data/UCU Split Motions 2024-2006.xlsx")

    
    CHROMA_DATA_PATH = "Data/embeddings/"
    MODEL = "all-mpnet-base-v2"
    COLLECTION_NAME = "splits_embeddings"
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL)
    client.delete_collection(name=COLLECTION_NAME)
    collection = client.create_collection(name=COLLECTION_NAME,embedding_function=embedding_func,metadata={"hnsw:space":"cosine"})
    for f in range(0,math.ceil(len(split_motions["Contents"])/5000)):
        collection.add(documents=split_motions["Contents"][f*5000:min((f+1)*5000,len(split_motions["Contents"]))].tolist(),
                       ids=split_motions["index"][f*5000:min((f+1)*5000,len(split_motions["Contents"]))].astype(str).tolist())
    return (True)