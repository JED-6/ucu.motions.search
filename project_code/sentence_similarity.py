import chromadb
from chromadb.utils import embedding_functions
from project_code.models import Split, Motion
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings

def get_split_details(result,UCU_WEBSITE_URL):
    splits = Split.query.with_entities(Split.id,Split.motion_id).filter(Split.id.in_(result["ids"])).all()
    splits = sorted(splits, key=lambda s: result["ids"].index(s.id))
    motion_ids = [split.motion_id for split in splits]
    result["links"] = [UCU_WEBSITE_URL+str(id) for id in motion_ids]

    motions = Motion.query.with_entities(Motion.id,Motion.title,Motion.session).filter(Motion.id.in_(motion_ids)).all()
    motions = [[m.id for m in motions],[m.title for m in motions],[m.session for m in motions]]
    result["Title"] = [motions[1][motions[0].index(id)]  for id in motion_ids]
    result["Session"] = [motions[2][motions[0].index(id)]  for id in motion_ids]
    result = zip(result["documents"],result["distances"],result["links"],result["Title"],result["Session"])
    return result

def compare(sentence,collection,n_closest):
    query_results = collection.query(query_texts=[sentence],n_results=n_closest)

    result = {}
    result["documents"] = query_results["documents"][0]
    result["distances"] = query_results["distances"][0]
    result["ids"] = list(map(int,query_results["ids"][0]))
    return result

def initialise_model(CHROMA_DATA_PATH,MODEL,COLLECTION_NAME):
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL)
    collection = client.get_collection(name=COLLECTION_NAME,embedding_function=embedding_func)
    return collection

def calc_tf_idf(query_sentence):
    warnings.filterwarnings("ignore",message="The parameter 'token_pattern' will not be used since 'tokenizer' is not None'")
    all_splits = Split.query.with_entities(Split.id,Split.content).order_by(Split.id).all()
    all_content = [split.content for split in all_splits]

    tfidf = TfidfVectorizer(analyzer="word",sublinear_tf=True,max_features=5000,tokenizer=nltk.word_tokenize)
    tfidf = tfidf.fit(all_content)
    splits_encodings = tfidf.transform(all_content)
    query_encoding = tfidf.transform([query_sentence])
    similarity = cosine_similarity(splits_encodings,query_encoding)

    similarity = [s[0] for s in similarity]
    similarity = list(zip([split.id for split in all_splits],similarity,all_content))
    similarity = sorted(similarity, key=lambda x: x[1],reverse=True)

    result = {}
    result["documents"] = [s[2] for s in similarity[:10]]
    result["distances"] = [1-s[1] for s in similarity[:10]]
    result["ids"] = [s[0] for s in similarity[:10]]
    return result