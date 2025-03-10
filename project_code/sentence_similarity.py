from project_code.models import *
import re
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
# import numpy as np
# from sentence_transformers import SentenceTransformer

def get_split_details(results,UCU_WEBSITE_URL):
    ids = [r[0] for r in results]
    splits = db.session.execute(select(Split.id,Split.content,Split.motion_id,Split.action,Motion.content.label("motion_content"),Motion.title,Motion.session).join(Motion).where(Split.id.in_(ids))).all()
    splits = sorted(splits, key=lambda s: ids.index(s.id))
    motion_ids = [split.motion_id for split in splits]
    for r in range(len(results)):
        results[r] += [splits[r].content]
        results[r] += [splits[r].motion_content]
        results[r] += [UCU_WEBSITE_URL+str(motion_ids[r])]
        results[r] += [splits[r].title]
        results[r] += [splits[r].session]
        results[r] += [splits[r].action]
    return results

# def compare_transformer_model(query_sentence,model,embeddings,n_closest,actions,sessions):
#     splits = db.session.execute(select(Split.id).join(Motion).where(Split.action.in_(actions),Motion.session.in_(sessions),Split.id.in_(embeddings["ids"])))
#     indexes = []
#     for s in splits:
#         indexes += [embeddings["ids"].index(s[0])]
#     emb = model.encode(query_sentence)
#     embs = embeddings["embeddings"][indexes,:]
#     similarity = model.similarity(emb,embs).tolist()[0]
#     result = []
#     for i in range(len(indexes)):
#         result += [[embeddings["ids"][indexes[i]],1-similarity[i]]]
#     results = sorted(result, key=lambda x:x[1])
#     return results[:n_closest]

# def initialise_transformer_model(MODEL,with_embeddings=False):
#     model = SentenceTransformer("sentence-transformers/"+MODEL)
#     if with_embeddings:
#         splits = db.session.execute(select(Split).where(Split.id<50)).all()
#         contents = [s[0].content for s in splits]
#         embeddings = {}
#         embeddings["embeddings"] = model.encode(contents)
#         embeddings["ids"] = [s[0].id for s in splits]
#         return model, embeddings
#     else:
#         return model

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
    similarity = list(zip([split.id for split in query_splits],similarity))
    similarity = sorted(similarity, key=lambda x: x[1],reverse=True)

    results = [[s[0],1-s[1]] for s in similarity[:n_closest]]
    return results

def normalise_text(text):
    lemmatizer = nltk.stem.WordNetLemmatizer()
    text_tokens = nltk.tokenize.word_tokenize(text)
    text_tokens = [lemmatizer.lemmatize(t) for t in text_tokens]
    tokens = []
    for t in text_tokens:
        t = t.lower()
        t = re.sub(r"[^a-z]","",t)
        if t not in stopwords.words("english") and t!="":
            tokens.append(t)
    return tokens

def initialise_WO():
    query_splits = db.session.execute(select(Split.id,Split.content)).all()
    splits_tokens = []
    for s in query_splits:
        norm = normalise_text(s.content)
        if len(norm)>0:
            splits_tokens += [[s.id,norm]]
    return splits_tokens

def word_overlap(query_sentence,splits_tokens,n_closest,actions,sessions):
    ids = [s[0] for s in splits_tokens]
    query_splits = db.session.execute(select(Split.id,Split.content).join(Motion).where(Split.id.in_(ids),Split.action.in_(actions),
                                                                             Motion.session.in_(sessions)).order_by(Split.id)).all()
    query_tokens = set(normalise_text(query_sentence))
    similarity = []
    for s in range(len(query_splits)):
        i = ids.index(query_splits[s].id)
        common = query_tokens.intersection(splits_tokens[i][1])
        similarity += [[query_splits[s].id,(len(common)/len(query_tokens))*(len(query_tokens)/len(splits_tokens[i][1]))]]
    similarity = sorted(similarity, key=lambda x: x[1],reverse=True)
    results = [[s[0],1-s[1]] for s in similarity[:n_closest]]
    return results