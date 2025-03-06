# import chromadb
# from chromadb.utils import embedding_functions
from project_code.models import *
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings

def get_split_details(result,UCU_WEBSITE_URL):
    splits = db.session.execute(select(Split.id,Split.motion_id,Split.action,Motion.content).join(Motion).where(Split.id.in_(result["ids"]))).all()
    splits = sorted(splits, key=lambda s: result["ids"].index(s.id))
    motion_ids = [split.motion_id for split in splits]
    result["links"] = [UCU_WEBSITE_URL+str(id) for id in motion_ids]
    result["action"] = [split.action for split in splits]
    result["motion"] = [split.content for split in splits]
    result["ids"] = [split.id for split in splits]

    motions = db.session.execute(select(Motion.id,Motion.title,Motion.session).where(Motion.id.in_(motion_ids))).all()
    motions = [[m.id for m in motions],[m.title for m in motions],[m.session for m in motions]]
    result["Title"] = [motions[1][motions[0].index(id)]  for id in motion_ids]
    result["Session"] = [motions[2][motions[0].index(id)]  for id in motion_ids]

    result = list(zip(result["ids"],result["documents"],result["motion"],result["distances"],result["links"],result["Title"],result["Session"],result["action"]))
    return result

# def compare(sentence,collection,n_closest,actions,sessions):
#     query_results = collection.query(query_texts=[sentence],n_results=n_closest,where={"$and":[{"action":{"$in":actions}},{"session":{"$in":sessions}}]})

#     result = {}
#     result["documents"] = query_results["documents"][0]
#     result["distances"] = query_results["distances"][0]
#     result["ids"] = list(map(int,query_results["ids"][0]))
#     return result

# def initialise_model(CHROMA_DATA_PATH,MODEL,COLLECTION_NAME):
#     client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
#     embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL)
#     collection = client.get_or_create_collection(name=COLLECTION_NAME,embedding_function=embedding_func,metadata={"hnsw:space":"cosine"})
#     return collection

def initialise_tfidf():
    warnings.filterwarnings("ignore",message="The parameter 'token_pattern' will not be used since 'tokenizer' is not None'")
    all_splits = db.session.execute(select(Split.content)).all()
    all_content = [split.content for split in all_splits]
    if len(all_content)==0:
        return False
    else:
        tfidf = TfidfVectorizer(analyzer="word",sublinear_tf=True,max_features=5000,tokenizer=nltk.word_tokenize)
        tfidf = tfidf.fit(all_content)
        return tfidf

def calc_tf_idf(tfidf,query_sentence,n_closest,actions,sessions):
    query_splits = db.session.execute(select(Split.id,Split.content).join(Motion).where(Split.action.in_(actions),Motion.session.in_(sessions)).order_by(Split.id)).all()
    query_content = [split.content for split in query_splits]
    splits_encodings = tfidf.transform(query_content)
    query_encoding = tfidf.transform([query_sentence])
    similarity = cosine_similarity(splits_encodings,query_encoding)

    similarity = [s[0] for s in similarity]
    similarity = list(zip([split.id for split in query_splits],similarity,query_content))
    similarity = sorted(similarity, key=lambda x: x[1],reverse=True)

    result = {}
    result["documents"] = [s[2] for s in similarity[:n_closest]]
    result["distances"] = [1-s[1] for s in similarity[:n_closest]]
    result["ids"] = [s[0] for s in similarity[:n_closest]]
    return result