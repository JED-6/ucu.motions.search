import chromadb
from chromadb.utils import embedding_functions

def compare(sentence,collection,n_closest):
    query_results = collection.query(query_texts=[sentence],n_results=n_closest)
    return query_results

def initialise_model():
    CHROMA_DATA_PATH = "Data/embeddings/"
    MODEL = "all-mpnet-base-v2"
    COLLECTION_NAME = "splits_embeddings"
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL)
    collection = client.get_collection(name=COLLECTION_NAME,embedding_function=embedding_func)
    return collection