from project_code.models import *
import re
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sentence_transformers import SentenceTransformer, CrossEncoder
import torch.nn as nn
import project_code.global_variables as gv
from gensim.scripts.glove2word2vec import glove2word2vec
from gensim.models import KeyedVectors
import gensim.downloader
import os.path

# given text tokenise, lemmatize and remove stopwords and any none alphabetical symbols
def normalise_text(text):
    #lemmatizer = nltk.stem.WordNetLemmatizer()
    stemmer = nltk.stem.PorterStemmer()
    text_tokens = nltk.tokenize.word_tokenize(text)
    text_tokens = [stemmer.stem(t) for t in text_tokens]
    tokens = []
    for t in text_tokens:
        t = t.lower()
        t = re.sub(r"[^a-z0-9]","",t)
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

def select_splits(actions,sessions,meeting):
    if meeting == gv.MEETINGS[0]:
        splits = db.session.execute(select(Split.id,Split.content,Split.nor_content).join(Motion).where(Split.action.in_(actions),Motion.session.in_(sessions)).order_by(Split.id)).all()
    else:
        splits = db.session.execute(select(Split.id,Split.content,Split.nor_content).join(Motion).where(Split.action.in_(actions),Motion.session.in_(sessions),Motion.meeting.contains(meeting)).order_by(Split.id)).all()
    return splits

# calculate similarity by word overlap
def word_overlap(query_sentence,n_closest,actions,sessions,meeting):
    query_splits = select_splits(actions,sessions,meeting)
    query_tokens = set(normalise_text(query_sentence))
    similarity = []
    for s in range(len(query_splits)):
        nor_s = re.split(" ",query_splits[s].nor_content)
        common = query_tokens.intersection(set(nor_s))
        similarity += [[query_splits[s].id,(len(common)/min(max(1,len(query_tokens)),len(nor_s)))]]
    similarity = sorted(similarity, key=lambda x: x[1],reverse=True)
    return similarity[:n_closest]

def initialise_tfidf(strip=True):
    splits = db.session.execute(select(Split.content,Split.nor_content)).all()
    if strip:
        all_content = [split.nor_content for split in splits]
    else:
        all_content = [split.content for split in splits]
    if len(all_content)==0:
        return False
    else:
        tfidf = TfidfVectorizer(analyzer="word",sublinear_tf=True,max_features=5000,tokenizer=nltk.word_tokenize, token_pattern=None)
        tfidf.fit(all_content)
        return tfidf

# generate vector for qurey_sentence and splits and calculate similarity scores
def calc_tf_idf(tfidf,query_sentence,n_closest,actions,sessions,meeting,strip=True):
    # limit search by action type and session
    query_splits = select_splits(actions,sessions,meeting)
    if strip:
        query_sentence = strip_text(query_sentence)
        query_content = [split.nor_content for split in query_splits]
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

def init_LSA(tfidf,strip=True):
    splits = db.session.execute(select(Split.content,Split.nor_content)).all()
    if strip:
        all_content = [split.nor_content for split in splits]
    else:
        all_content = [split.content for split in splits]
    if len(all_content)==0:
        return False
    else:
        tfidf = tfidf.transform(all_content)
        lsa = TruncatedSVD(n_components=500)
        lsa.fit(tfidf)
        return lsa

def compare_LSA(lsa,tfidf,query_sentence,n_closest,actions,sessions,meeting,strip=True):
    query_splits = select_splits(actions,sessions,meeting)
    if strip:
        query_sentence = strip_text(query_sentence)
        query_content = [split.nor_content for split in query_splits]
    else:
        query_content = [split.content for split in query_splits]
    splits_encodings = tfidf.transform(query_content)
    splits_encodings = lsa.transform(splits_encodings)
    query_encoding = tfidf.transform([query_sentence])
    query_encoding = lsa.transform(query_encoding)
    similarity = cosine_similarity(splits_encodings,query_encoding)

    similarity = [s[0] for s in similarity]
    results = []
    for f in range(len(similarity)):
        results += [[query_splits[f].id,similarity[f]]]
    results = sorted(results, key=lambda x: x[1],reverse=True)

    return results[:n_closest]

def init_Word2Vec():
    try:
        WORD2VECS = KeyedVectors.load_word2vec_format(gv.WORD2VEC_PATH, binary=True)
    except:
        WORD2VECS = gensim.downloader.load(gv.WORD2VEC_MODEL)
    return WORD2VECS

def word2vec_similarity(word2vec,query_sentence,n_closest,actions,sessions,meeting):
    query_tokens = nltk.tokenize.word_tokenize(query_sentence)
    query_tokens = [t.lower() for t in query_tokens]
    query_tokens = [t for t in query_tokens if t in word2vec]
    if query_tokens:
        query_splits = query_splits = select_splits(actions,sessions,meeting)
        similarity = []
        for s in query_splits:
            tokens = nltk.tokenize.word_tokenize(s.content)
            tokens = [t.lower() for t in tokens]
            tokens = [t for t in tokens if t in word2vec]
            if tokens:
                similarity += [[s.id,word2vec.wmdistance(query_tokens,tokens)]]
        similarity = sorted(similarity, key=lambda x: x[1])
        return similarity[:n_closest]
    else:
        return []
    
def GloVe_to_Word2Vec():
    glove2word2vec(gv.glove_input_file, gv.word2vec_output_file)

def init_GloVe():
    if not os.path.isfile(gv.word2vec_output_file):
        GloVe_to_Word2Vec()
    GloVe = KeyedVectors.load_word2vec_format(gv.word2vec_output_file)
    GloVe.init_sims(replace=True)
    return GloVe

def GloVe_similarity(GloVe,query_sentence,n_closest,actions,sessions,meeting):
    query_tokens = nltk.tokenize.word_tokenize(query_sentence)
    query_tokens = [t.lower() for t in query_tokens]
    query_tokens = [t for t in query_tokens if t in GloVe]
    if query_tokens:
        query_splits = select_splits(actions,sessions,meeting)
        similarity = []
        for s in query_splits:
            tokens = nltk.tokenize.word_tokenize(s.content)
            tokens = [t.lower() for t in tokens]
            tokens = [t for t in tokens if t in GloVe]
            if tokens:
                similarity += [[s.id,GloVe.wmdistance(query_tokens,tokens)]]
        similarity = sorted(similarity, key=lambda x: x[1])
        return similarity[:n_closest]
    else:
        return []

def initialise_bi_encoder(model_name,with_embeddings=False,with_prompt=False,strip=False):
    if with_prompt:
        model = SentenceTransformer("sentence-transformers/"+model_name,prompts={"Similarity":"Identify semantically similar text:"},default_prompt_name="Similarity")
    else:
        model = SentenceTransformer("sentence-transformers/"+model_name)
    if with_embeddings:
        splits = db.session.execute(select(Split.id,Split.content,Split.nor_content).where(Split.id)).all()
        if strip:
            contents = [s.nor_content for s in splits]
        else:
            contents = [s.content for s in splits]
        embeddings = {}
        # also generate embeddings for splits to save time during search
        embeddings["embeddings"] = model.encode(contents)
        embeddings["ids"] = [s.id for s in splits]
        return model, embeddings
    else:
        return model

# generate embedding for query_sentence and compare with precalculated embeddings for splits
def compare_bi_encoder(query_sentence,model,embeddings,n_closest,actions,sessions,meeting,strip=False):
    # limit search by action type and session
    splits = select_splits(actions,sessions,meeting)
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

def initialise_cross_encoder(model_name):
    model = CrossEncoder("cross-encoder/"+model_name,default_activation_function=nn.Sigmoid(), max_length=512)
    return model

# use the Cross-Encoder to find similar results to the query_sentence
# can take a while to run when checks all splits
def compare_cross_encoder(model,query_sentence,n_closest,actions,sessions,meeting,strip=False,ids=[]):
    # find either all splits or only those specified in ids
    if len(ids)==0:
        splits = select_splits(actions,sessions,meeting)
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
        results += [[ids[f],float(scores[f])]]
    results = sorted(results, key=lambda x:x[1],reverse=True)
    return results[:n_closest]

# find similar splits to query_sentence by finding similar splits with tfid and then cross-encoder on top results
# faster than running cross-encoder on all splits
def tfidf_cross_encoder(tfidf,model,query_sentence,n_closest,actions,sessions,meeting,strip=False):
    results = calc_tf_idf(tfidf,query_sentence,n_closest*10,actions,sessions,meeting,strip=strip)
    ids = [r[0] for r in results]
    results = compare_cross_encoder(model,query_sentence,n_closest,actions,sessions,strip=strip,ids=ids)
    return results

def run_similarity(method,query,n_results,acts,sessions,meeting,TFIDF,LSA,WORD2VECS,GLOVE,BI_ENCODER,EMBEDINGS,CROSS_ENCODER,strip):
    if method == gv.SEARCH_METHODS[0]:
        results = word_overlap(query,n_results,acts,sessions,meeting)
    elif method == gv.SEARCH_METHODS[1]:
        results = calc_tf_idf(TFIDF,query,n_results,acts,sessions,meeting,strip=strip)
    elif method == gv.SEARCH_METHODS[2]:
        results = compare_LSA(LSA,TFIDF,query,n_results,acts,sessions,meeting,strip=strip)
    elif method == gv.SEARCH_METHODS[3]:
        results = word2vec_similarity(WORD2VECS,query,n_results,acts,sessions,meeting)
    elif method == gv.SEARCH_METHODS[4]:
        results = GloVe_similarity(GLOVE,query,n_results,acts,sessions,meeting)
    elif method == gv.SEARCH_METHODS[5]:
        results = compare_bi_encoder(query,BI_ENCODER,EMBEDINGS,n_results,acts,sessions,meeting)
    elif method == gv.SEARCH_METHODS[6]:
        results = compare_cross_encoder(CROSS_ENCODER,query,n_results,acts,sessions,meeting)
    elif method == gv.SEARCH_METHODS[7]:
        results = tfidf_cross_encoder(TFIDF,CROSS_ENCODER,query,n_results,acts,sessions,meeting)
    return results
    

def num_tokens():
    splits = db.session.execute(select(Split)).all()
    words = set()
    for s in splits:
        content = s[0].nor_content
        words = words.union(nltk.tokenize.word_tokenize(content))
    print(words)
    print(len(words))