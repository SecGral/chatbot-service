import faiss
import numpy as np
import os
import pickle

INDEX_PATH = "sst_agent/app/data/faiss.index"
META_PATH = "sst_agent/app/data/docs.pkl"

_index = None
_docs = []

def load_index(dim):
    global _index, _docs
    if os.path.exists(INDEX_PATH):
        _index = faiss.read_index(INDEX_PATH)
        _docs = pickle.load(open(META_PATH, "rb"))
    else:
        _index = faiss.IndexFlatL2(dim)
        _docs = []
    return _index

def save():
    faiss.write_index(_index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(_docs, f)

def add_vectors(vectors, documents):
    _index.add(np.array(vectors).astype('float32'))
    _docs.extend(documents)
    save()

def search(query_vector, k=4):
    D, I = _index.search(np.array([query_vector]).astype('float32'), k)
    return [_docs[i] for i in I[0] if i < len(_docs)]
