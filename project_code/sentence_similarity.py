from project_code.models import *
import re
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, CrossEncoder
import torch.nn as nn

# given text tokenise, lemmatize and remove stopwords and any none alphabetical symbols
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

# normalise text but return as one string instead of list of tokens
def strip_text(text):
    tokens = normalise_text(text)
    stripped_text = ""
    for t in tokens:
        stripped_text += " " + t
    return stripped_text

# given list of split ids and distances return list that includes more details about each split
# all details needed for results table
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

def initialise_cross_encoder(model_name):
    model = CrossEncoder("cross-encoder/"+model_name,default_activation_function=nn.Sigmoid())
    return model

# use the Cross-Encoder to find similar results to the query_sentence
# can take a while to run when checks all splits
def compare_cross_encoder(model,query_sentence,n_closest,actions,sessions,strip=False,ids=[]):
    # find either all splits or only those specified in ids
    if len(ids)==0:
        splits = db.session.execute(select(Split.id,Split.content).join(Motion).where(Split.action.in_(actions),Motion.session.in_(sessions))).all()
        ids = [s[0] for s in splits]
    else:
        splits = db.session.execute(select(Split.id,Split.content).where(Split.id.in_(ids))).all()
    if strip:
        splits = [strip_text(s[1]) for s in splits]
        query_sentence = strip_text(query_sentence)
    else:
        splits = [s[1] for s in splits]
    # generate similarity scores
    pairs = [[query_sentence,s] for s in splits]
    scores = model.predict(pairs)
    results = []
    for f in range(len(ids)):
        results += [[ids[f],scores[f]]]
    results = sorted(results, key=lambda x:x[1],reverse=True)
    return results[:n_closest]

def initialise_bi_encoder(model_name,with_embeddings=False,with_prompt=False,strip=False):
    if with_prompt:
        model = SentenceTransformer("sentence-transformers/"+model_name,prompts={"Similarity":"Identify semantically similar text:"},default_prompt_name="Similarity")
    else:
        model = SentenceTransformer("sentence-transformers/"+model_name)
    if with_embeddings:
        splits = db.session.execute(select(Split).where(Split.id<50)).all()
        if strip:
            contents = [strip_text(s[0].content) for s in splits]
        else:
            contents = [s[0].content for s in splits]
        embeddings = {}
        # also generate embeddings for splits to save time during search
        embeddings["embeddings"] = model.encode(contents)
        embeddings["ids"] = [s[0].id for s in splits]
        return model, embeddings
    else:
        return model

# generate embedding for query_sentence and compare with precalculated embeddings for splits
def compare_bi_encoder(query_sentence,model,embeddings,n_closest,actions,sessions,strip=False):
    # limit search by action type and session
    splits = db.session.execute(select(Split.id).join(Motion).where(Split.action.in_(actions),Motion.session.in_(sessions),Split.id.in_(embeddings["ids"]))).all()
    indexes = []
    for s in splits:
        indexes += [embeddings["ids"].index(s[0])]
    if strip:
        emb = model.encode(strip_text(query_sentence))
    else:
        emb = model.encode(query_sentence)
    embs = embeddings["embeddings"][indexes,:]
    # generate similarity scores 
    similarity = model.similarity(emb,embs).tolist()[0]
    results = []
    for i in range(len(indexes)):
        results += [[embeddings["ids"][indexes[i]],similarity[i]]]
    results = sorted(results, key=lambda x:x[1], reverse=True)
    return results[:n_closest]

def initialise_tfidf(strip=False):
    all_splits = db.session.execute(select(Split.content)).all()
    if strip:
        all_content = [strip_text(split.content) for split in all_splits]
    else:
        all_content = [split.content for split in all_splits]
    if len(all_content)==0:
        return False
    else:
        tfidf = TfidfVectorizer(analyzer="word",sublinear_tf=True,max_features=5000,tokenizer=nltk.word_tokenize, token_pattern=None)
        tfidf = tfidf.fit(all_content)
        return tfidf

# generate vector for qurey_sentence and splits and calculate similarity scores
def calc_tf_idf(tfidf,query_sentence,n_closest,actions,sessions,strip=False):
    # limit search by action type and session
    query_splits = db.session.execute(select(Split.id,Split.content).join(Motion).where(Split.action.in_(actions),Motion.session.in_(sessions)).order_by(Split.id)).all()
    if strip:
        query_sentence = strip_text(query_sentence)
        query_content = [strip_text(split.content) for split in query_splits]
    else:
        query_content = [split.content for split in query_splits]
    splits_encodings = tfidf.transform(query_content)
    query_encoding = tfidf.transform([query_sentence])
    similarity = cosine_similarity(splits_encodings,query_encoding)

    similarity = [s[0] for s in similarity]
    results = []
    for f in range(len(similarity)):
        results += [[query_splits[f].id,similarity[f]]]
    results = sorted(results, key=lambda x: x[1],reverse=True)

    return results[:n_closest]

# generate tokenised splits
def initialise_WO():
    query_splits = db.session.execute(select(Split.id,Split.content)).all()
    splits_tokens = []
    for s in query_splits:
        norm = normalise_text(s.content)
        if len(norm)>0:
            splits_tokens += [[s.id,norm]]
    return splits_tokens

# calculate similarity by word overlap
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
    return similarity[:n_closest]

# find similar splits to query_sentence by finding similar splits with tfid and then cross-encoder on top results
# faster than running cross-encoder on all splits
def tfidf_cross_encoder(tfidf,model,query_sentence,n_closest,actions,sessions,strip=False):
    results = calc_tf_idf(tfidf,query_sentence,n_closest*10,actions,sessions)
    ids = [r[0] for r in results]
    results = compare_cross_encoder(model,query_sentence,n_closest,actions,sessions,strip=strip,ids=ids)
    return results