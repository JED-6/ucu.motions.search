from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
def compare(sentences,sentence,model):
    embeddings = model.encode(sentences+[sentence])
    similarities = model.similarity(embeddings[:-1],embeddings[-1])
    similarities = [similarities[i].item() for i in range(0,len(sentences))]
    return similarities
