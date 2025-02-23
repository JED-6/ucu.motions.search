import chromadb
from chromadb.utils import embedding_functions
from project_code.models import Split, Motion

def compare(sentence,collection,n_closest):
    query_results = collection.query(query_texts=[sentence],n_results=n_closest)

    result = {}
    result["documents"] = query_results["documents"][0]
    result["distances"] = query_results["distances"][0]

    ids = list(map(int,query_results["ids"][0]))
    splits = Split.query.with_entities(Split.id,Split.motion_id).filter(Split.id.in_(ids)).all()
    splits = sorted(splits, key=lambda s: ids.index(s.id))
    motion_ids = [split.motion_id for split in splits]
    result["links"] = ["https://policy.web.ucu.org.uk/motion-information/?pdb="+str(id) for id in motion_ids]

    motions = Motion.query.with_entities(Motion.id,Motion.title).filter(Motion.id.in_(motion_ids)).all()
    motions = sorted(motions, key=lambda m: motion_ids.index(m.id))
    result["Title"] = [ motion.title for motion in motions]
    return result

def initialise_model():
    CHROMA_DATA_PATH = "Data/embeddings/"
    MODEL = "all-mpnet-base-v2"
    COLLECTION_NAME = "splits_embeddings"
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL)
    collection = client.get_collection(name=COLLECTION_NAME,embedding_function=embedding_func)
    return collection