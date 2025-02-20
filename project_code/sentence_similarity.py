import chromadb
from chromadb.utils import embedding_functions
import pandas as pd

def compare(sentence,collection,n_closest):
    query_results = collection.query(query_texts=[sentence],n_results=n_closest)
    df = pd.read_excel("Data/UCU_Split_Motions_2024-2006.xlsx")
    result = {}
    result["documents"] = query_results["documents"][0]
    result["distances"] = query_results["distances"][0]
    link_numbers = [df.query("index=="+str(id))["Link Number"].iloc[0] for id in query_results["ids"][0]]
    result["links"] = ["https://policy.web.ucu.org.uk/motion-information/?pdb="+str(link) for link in link_numbers]
    df = pd.read_excel("Data/UCU_Motions_2024-2006.xlsx")
    result["Title"] = [df.query("`Link Number`=="+str(link))["Title"].iloc[0] for link in link_numbers]
    return result

def initialise_model():
    CHROMA_DATA_PATH = "Data/embeddings/"
    MODEL = "all-mpnet-base-v2"
    COLLECTION_NAME = "splits_embeddings"
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL)
    collection = client.get_collection(name=COLLECTION_NAME,embedding_function=embedding_func)
    return collection