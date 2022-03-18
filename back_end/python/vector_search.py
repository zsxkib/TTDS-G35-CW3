# %% [markdown]
# <a href="https://colab.research.google.com/github/Sakib56/TTDS-G35-CW3/blob/main/back_end/python/vector_search.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

# %% [markdown]
# ### Uncomment and run the following cells if you work on GCP. Change runtime type to GPU.

# %%
# !pip install transformers>=3.3.1 sentence-transformers>=0.3.8 pandas>=1.1.2 faiss-cpu>=1.6.1 numpy>=1.19.2 folium>=0.2.1 streamlit>=0.62.0

# %%
# !pip install sentence-transformers

# %%
# !pip install faiss-cpu

# %% [markdown]
# 
# 
# ---
# This is mounting my (Kenza) drive to the collab notebook. I stored the wikidata there.
# 

# %%
# from google.colab import drive
# drive.mount('/content/drive')

# %% [markdown]
# ### Before we begin, make sure you restart (not factory reset) the runtime so that the relevant packages are used

# %%
# %load_ext autoreload

# %%
# %autoreload 2

# Used to create the dense document vectors.
import torch
from sentence_transformers import SentenceTransformer
import sys

# Used to create and store the Faiss index.
import faiss
import numpy as np
import pickle
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor

import xml

from nltk.stem import PorterStemmer
import re
ps = PorterStemmer()

# %%
def vector_search(query, model, index, num_results=10):
    """Tranforms query to vector using a pretrained, sentence-level 
    DistilBERT model and finds similar vectors using FAISS.
    Args:
        query (str): User query that should be more than a sentence long.
        model (sentence_transformers.SentenceTransformer.SentenceTransformer)
        index (`numpy.ndarray`): FAISS index that needs to be deserialized.
        num_results (int): Number of results to return.
    Returns:
        D (:obj:`numpy.array` of `float`): Distance between results and query.
        I (:obj:`numpy.array` of `int`): Paper ID of the results.
    
    """
    # query = ps.stem(query)
    vector = model.encode(list(query))
    D, I = index.search(np.array(vector).astype("float32"), k=num_results)
    return D, I


def id2details(I):
    """Returns the paper titles based on the paper index."""
    return [worker.pids[str(idx)] for idx in I[0]]

# %% [markdown]
# The [Sentence Transformers library](https://github.com/UKPLab/sentence-transformers) offers pretrained transformers that produce SOTA sentence embeddings. Checkout this [spreadsheet](https://docs.google.com/spreadsheets/d/14QplCdTCDwEmTqrn1LH4yrbKvdogK4oQvYO1K1aPR5M/) with all the available models.
# 
# In this tutorial, we will use the `distilbert-base-nli-stsb-mean-tokens` model which has the best performance on Semantic Textual Similarity tasks among the DistilBERT versions. Moreover, although it's slightly worse than BERT, it is quite faster thanks to having a smaller size.

# %%
# Instantiate the sentence-level DistilBERT
model = SentenceTransformer('distilbert-base-nli-stsb-mean-tokens')
# Check if GPU is available and use it
if torch.cuda.is_available():
    model = model.to(torch.device("cuda"))
print(model.device)

# %%
class wikiHandler(xml.sax.ContentHandler):

    def __init__(self, searchClass):
        self.tag = ""
        self.pid = ""
        self.title = ""
        self.text = ""
        self.searcher = searchClass

    def ended(self):
        self.executor.shutdown()

    def startElement(self, tag, argument):
        self.tag = tag

    def characters(self, content):
        if self.tag == "id" and not content.isspace() and (self.pid == "" or len(self.pid) == 0):
            self.pid = content
        if self.tag == "title":
            self.title += content
        if self.tag == "text":
            self.text += content

    def endElement(self, tag):
        if tag == "page":
            self.searcher.perpage({"pid":self.pid, "title":self.title, "text":self.text})
            self.pid = ""
            self.title = ""
            self.text = ""

# %%
# Convert abstracts to vectors
# Convert abstracts to vectors
class encoder():
    def __init__(self):
        self.embeddings = []
        self.partials = []
        self.partial_ids={}
        self.pids = {}
        self.quantizer = faiss.IndexFlatL2(768)
        self.nlist = 256
        self.index = faiss.IndexIVFFlat(self.quantizer, 768, self.nlist)
        self.count = 0

    def perpage(self, text):
        train_timer = 9984
        f = f"./faiss_index{self.nlist}_{train_timer}_.pickle"
        try:
            self.pids[text["pid"]] = text["title"]
            self.partial_ids[text["pid"]] = text["title"]
            encoding = model.encode(text["text"])
            self.embeddings.append(encoding)
            self.partials.append(encoding)
            self.count += 1
            if self.count % train_timer == 0:
                self.partials = np.array([embedding for embedding in self.partials]).astype("float32")
                self.index.train(self.partials)
                index = faiss.IndexIDMap(self.index)
                index.add_with_ids(self.partials, np.array(list(self.partial_ids.keys())).astype('int64'))
                with open(f, "ab+") as h:
                    pickle.dump(faiss.serialize_index(index), h)
                self.partials = []
                self.partial_ids = {}
                index.reset()
        except KeyboardInterrupt:
            sys.exit()
        except Exception as e:
            self.partials = []
            self.partial_ids = {}
            if 'index' in locals():
                if index is not None:
                    index.reset()
            print(self.count, e)
            pass
        print(self.count, end="\r")

worker = encoder()
parser = xml.sax.make_parser()  
parser.setFeature(xml.sax.handler.feature_namespaces, 0)
handler = wikiHandler(worker)
parser.setContentHandler(handler)

##### INPUT PATH TO LONG XML!!!!!
parser.parse("./enwiki-20220301-pages-articles-multistream.xml")

# %%
# Should the entire thing run properly, try running this to make sure index is 100% correct:
quantizer = faiss.IndexFlatL2(768)
nlist = 256
index = faiss.IndexIVFFlat(quantizer, 768, nlist)
worker.embeddings = np.array([embedding for embedding in worker.embeddings]).astype("float32")
index.train(worker.embeddings)
index = faiss.IndexIDMap(index)
# index.add_with_ids(worker.embeddings, np.array(list(worker.pids.keys())).astype('int64'))
index.add_with_ids(
  worker.embeddings, 
  np.array(list(worker.pids.keys())).astype('int64')[:worker.embeddings.shape[0]].astype('int64'))
with open("./final_faiss_index2.pickle", "ab+") as h:
  pickle.dump(faiss.serialize_index(index), h)

# %%
print(f'Number of articles processed: {len(worker.embeddings)}')

# %% [markdown]
# 
# ## Putting all together
# 
# So far, we've built a Faiss index using the wikidata text vectors we encoded with a sentence-DistilBERT model. That's helpful but in a real case scenario, we would have to work with unseen data. To query the index with an unseen query and retrieve its most relevant documents, we would have to do the following:
# 
# 1. Encode the stemmed query with the same sentence-DistilBERT model we used for the rest of the abstract vectors.
# 2. Change its data type to float32.
# 3. Search the index with the encoded query.
# 
# IDEA: Use the Answer of the Question Answering option as the input query for vector search or let the user write a query for vector search or both.
# 

# %%
user_query = """Artificial Intelligence"""

# %%
# For convenience, I've wrapped all steps in the vector_search function.
# It takes four arguments: 
# A query, the sentence-level transformer, the Faiss index and the number of requested results
D, I = vector_search([user_query], model, index, num_results=10)
print(f'L2 distance: {D.flatten().tolist()}\n\nMAG paper IDs: {I.flatten().tolist()}')

# %%
# Fetching the paper titles based on their index
id2details(I)

# %%
# Run Search from Pickle Index
with open(r'faiss_index.pickle','rb') as infile:
        index = pickle.load(infile)
index = faiss.deserialize_index(index)
user_query = """Artificial Intelligence"""
D, I = vector_search([user_query], model, index, num_results=10)
print(f'L2 distance: {D.flatten().tolist()}\n\nMAG paper IDs: {I.flatten().tolist()}')


