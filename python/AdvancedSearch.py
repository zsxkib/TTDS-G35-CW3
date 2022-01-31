# Imports ------------------------------------------

from math import log10
from xml.etree.ElementTree import ProcessingInstruction
from gensim.corpora.dictionary import Dictionary
from gensim.models.ldamodel import LdaModel
from numpy.lib import unique
from scipy.sparse import dok_matrix
from sklearn.svm import SVC
import pandas as pd
import numpy as np
from pathlib import Path
import re
import os
import json
from nltk.stem.porter import PorterStemmer
import time

# General Functions --------------------------------

codepath = Path.cwd()
_qrels   = pd.read_csv(codepath / "qrels.csv")
_results = pd.read_csv(codepath / "system_results.csv")

def saveIndex(path):
    with open(codepath / "data" / f"{path[:-4]}.json", 'w') as f:    
        f.write(json.dumps(indexing(path)))

def retrieveIndex(path):
    with open(codepath / "data" / f"{path[:-4]}.json", 'r') as f:
        index = json.loads(f.read())
        return index

with open(codepath / "stopwords.txt") as f:
    stopwords = f.read().splitlines() 


# --------------------------------------------------
#   Part 1 : IR Evaluation
# --------------------------------------------------

# Information Retrieval Function -------------------

def ir_eval(qrels, results, methods=['P', 'R', 'RP', 'AP', 'nDCG'], P_cutoff=10, R_cutoff=50, nDCG_cutoff=10):
    relevance = {}
    for query in qrels.query_id:
        temp = qrels[qrels.query_id == query]
        relevance[query] = {k:v for (k,v) in zip(temp['doc_id'], temp['relevance'])}

    out = {m:{s:{} for s in results.system_number.unique()} for m in methods} 
    for sys in results.system_number.unique():
        for query in results.query_number.unique():
            retrieved = results[(results['system_number'] == sys) & (results['query_number'] == query)]['doc_number'].reset_index()['doc_number']
            _rr = lambda cut, den : retrieved[:cut].isin(relevance[query]).sum() / den
            rel_num = len(relevance[query])
            if 'P' in out:
                out['P'][sys][query]  = _rr(P_cutoff, retrieved[:P_cutoff].shape[0])
            if 'R' in out:
                out['R'][sys][query]  = _rr(R_cutoff, rel_num)
            if 'RP' in out:
                out['RP'][sys][query] = _rr(rel_num, rel_num)
            if 'AP' in out:
                out['AP'][sys][query] = (1/rel_num)*np.sum([_rr(i, i) for i in np.where(retrieved.isin(relevance[query]))[0]+1]) if retrieved.isin(relevance[query]).any() else 0

            if 'nDCG' in out:
                DCG  =   relevance[query][retrieved[0]] if retrieved[0] in relevance[query] else 0
                DCG  +=  np.sum([relevance[query][retrieved[i]]/np.log2(i+1) if retrieved[i] in relevance[query] else 0 for i in range(1, nDCG_cutoff)])
                iDCG =   list(relevance[query].values())[0]  +  np.sum([list(relevance[query].values())[i]/np.log2(i+1) for i in range(1, min(rel_num, nDCG_cutoff))])
                out['nDCG'][sys][query] =  DCG / iDCG

    return out


# Write CSV Function -------------------------------

def write_ir_eval():
    out = ir_eval(_qrels, _results)
    out['nDCG20'] = ir_eval(_qrels, _results, ['nDCG'], nDCG_cutoff=20)['nDCG']

    _val  = lambda m : np.round(out[m][sys][query], 3)
    _mean = lambda m : np.round(np.mean(list(out[m][sys].values())), 3)

    df = pd.DataFrame(columns=['system_number', 'query_number', 'P@10', 'R@50', 'r-precision', 'AP', 'nDCG@10', 'nDCG@20'])
    for sys in out['P']:
        for query in out['P'][sys]:
            inp = [sys, query, _val('P'), _val('R'), _val('RP'), _val('AP'), _val('nDCG'), _val('nDCG20')]
            row = pd.DataFrame([inp], columns=['system_number', 'query_number', 'P@10', 'R@50', 'r-precision', 'AP', 'nDCG@10', 'nDCG@20'])
            df = df.append(row, ignore_index=True)
        inp = [sys, 'mean', _mean('P'), _mean('R'), _mean('RP'), _mean('AP'), _mean('nDCG'), _mean('nDCG20')]
        row = pd.DataFrame([inp], columns=['system_number', 'query_number', 'P@10', 'R@50', 'r-precision', 'AP', 'nDCG@10', 'nDCG@20'])
        df = df.append(row, ignore_index=True)

    df.to_csv(codepath / "ir_eval.csv", index=False, )

print(f'\nPart 1 : IR EVALUATION\n')
print(f"\tWriting IR eval")
write_ir_eval()


# --------------------------------------------------
#   Part 2 : Text Analysis
# --------------------------------------------------

# Preprocessing ------------------------------------

def preprocessing(path): 
    data = {}
    with open(codepath / path) as f:
        listData = f.read().splitlines()
        for i in range(len(listData)):
            corpus, doc = listData[i].split('\t')
            if corpus not in data:
                data[corpus] = {}
            data[corpus][i+1] = doc
        
    tokens = {corpus:{docno:[x.strip() for x in re.split('[^a-zA-Z0-9]', text) if x != '' and x.lower() not in stopwords] for (docno,text) in docs.items()} for (corpus,docs) in data.items()}    
    terms  = {corpus:{docno:[PorterStemmer().stem(x) for x in text] for (docno,text) in docs.items()} for (corpus,docs) in tokens.items()} 
    return terms


# Indexing -------------------------------------

def getIndex(path):
    if not os.path.isfile(codepath / "data" / f"{path[:-4]}.json"):
        saveIndex(path)
    return retrieveIndex(path)

def indexing(path):
    terms = preprocessing(path)
    index = {c:{} for c in terms}
        
    for corpus in terms:
        for line in terms[corpus]:
            for term in terms[corpus][line]:
                if term not in index[corpus]:
                    index[corpus][term] = {}
                index[corpus][term][line] = 1
    index[0] = {c:len(terms[c]) for c in terms}
    return index


# Text Analysis --------------------------------

def text_analysis(index, method): 
    ns = index['0']
    out = {c:{} for c in index if c != '0'}
    for corpus in out:
        incorpus = list(index.keys()); incorpus.remove(str(corpus))
        num  = ns[corpus]
        inum = ns[incorpus[0]] + ns[incorpus[1]]
        N = np.array([[None, None],[None, None]])
        for term in index[corpus]:
            N[1,1] =  len(index[corpus][term])
            N[0,1] =  num - N[1,1]
            N[1,0] =  len(index[incorpus[0]][term]) if term in index[incorpus[0]] else 0
            N[1,0] += len(index[incorpus[1]][term]) if term in index[incorpus[1]] else 0
            N[0,0] =  inum - N[1,0]

            # Mutual Information ---------------
            if method == "MI":
                _log = lambda i : np.log2((num+inum)*N[i]/(N[i[0],0]+N[i[0],1])/(N[0,i[1]]+N[1,i[1]])) if (N[i[0],0]+N[i[0],1])*(N[0,i[1]]+N[1,i[1]]) != 0 and (num+inum)*N[i] != 0 else 0
                mi = 0
                for i in [(1,1), (0,1), (1,0), (0,0)]:
                    mi += N[i]/(num+inum)*_log(i)
                out[corpus][term] = mi

            # Chi-Squared ----------------------
            else:
                den = (N[1,1]+N[0,1])*(N[1,1]+N[1,0])*(N[0,1]+N[0,0])*(N[1,0]+N[0,0])
                out[corpus][term] = (N[1,1]+N[0,1]+N[1,0]+N[0,0]) * (N[1,1]*N[0,0]-N[1,0]*N[0,1])**2 / den if den != 0 else 0 
        out[corpus] = sorted(out[corpus].items(), key=lambda i:i[1], reverse=True)
    return out


def LDA(path):
    fileLoc = codepath / "data" / f"{path[:-4]}"
    data = preprocessing(path)
    docs = [doc for corpus in data.values() for doc in corpus.values()]
    dct = Dictionary(docs)
    corpora = [dct.doc2bow(doc) for doc in docs]

    if not os.path.isfile(str(fileLoc)):
        LdaModel(corpora, num_topics=20, id2word=dct).save(str(fileLoc))
    lda = LdaModel.load(str(fileLoc))

    ats = {}    # Average Topic Score
    phase = 0
    highest_topics = {}
    for corpus in data:
        ats[corpus] = {}
        for doc in range(len(data[corpus])):
            for id in lda.get_document_topics(corpora[doc+phase]):
                if id[0] not in ats[corpus]:
                    ats[corpus][id[0]] = 0
                ats[corpus][id[0]] += id[1]  
                    
        l = len(data[corpus])
        phase += l
        ats[corpus] = {t:v/l for t, v in ats[corpus].items()}
        max_ats = max(ats[corpus], key=ats[corpus].get)
        highest_topics[corpus] = (max_ats, round(ats[corpus][max_ats], 3), lda.print_topic(max_ats))
    return highest_topics

print(f'\nPart 2 : Text Analysis\n')
print("  Token Analysis:")
path = "train_and_dev.tsv"
index = getIndex(path)
MI = text_analysis(index, 'MI')
X2 = text_analysis(index, 'X2')
for c in MI.keys():
    print(f"\n\t___________{c}___________")
    print(f"\t  MI\t\t  X2")
    for i in range(10):
        if len(MI[c][i][0]) > 7:
            print(f"\t{MI[c][i][0]}\t{X2[c][i][0]}")
        else:
            print(f"\t{MI[c][i][0]}\t\t{X2[c][i][0]}")

print("\n  Topic Analysis:")
highest_topics = LDA(path)
for c in highest_topics:
    print(f'\t{c} : Topic {highest_topics[c][0]} with score {highest_topics[c][1]}\n\t\t{highest_topics[c][2]}\n')

# --------------------------------------------------
#   Part 3 : Text Classification
# --------------------------------------------------

def text_classifier(path, test_path, frac=0.9, stem=False, idf=False, C=1000):

    # Preprocessing ---

    data_train = []
    data_dev = []
    data_test = []
    with open(codepath / path) as f:
        listData = f.read().splitlines()
        np.random.shuffle(listData)
        for i in range(len(listData)):
            if i < frac*len(listData):
                data_train.append(listData[i].split('\t'))
            else:
                data_dev.append(listData[i].split('\t'))

    with open(codepath / test_path) as f:
        listData = f.read().splitlines()
        for i in range(len(listData)):
            data_test.append(listData[i].split('\t'))


    tokenize = lambda data : [[y[0], [x.strip() for x in re.split('[^a-zA-Z0-9]', y[1]) if x != '' and x.lower() not in stopwords]] for y in data]
    termerize  = lambda tokens : [[y[0], [PorterStemmer().stem(x) for x in y[1]]] for y in tokens]

    tokens_train, tokens_dev, tokens_test = tokenize(data_train), tokenize(data_dev), tokenize(data_test)
    if stem:
        tokens_train, tokens_dev, tokens_test = termerize(data_train), termerize(data_dev), termerize(data_test)

    # Extract Features -----------------------

    corpora = []
    unique_tokens = []
    for info in tokens_train:
        if info[0] not in corpora:
            corpora.append(info[0])
        for token in info[1]:
            if token not in unique_tokens:
                unique_tokens.append(token)

    def getXy(tokens):
        num = len(tokens)
        y = np.empty(num)
        X = dok_matrix((num, len(unique_tokens)))
        if idf:
            df = [sum([1 for line in tokens if token in line[1]]) for token in unique_tokens]
        for i in range(num):
            y[i] = corpora.index(tokens[i][0])
            for t in tokens[i][1]:
                if t in unique_tokens:
                    X[i, unique_tokens.index(t)] += 1
            if idf:
                for t in tokens[i][1]:
                    if t in unique_tokens:
                        j = unique_tokens.index(t)
                        if type(X[i, j]) == float:
                            X[i, j] = (1+ np.log10(X[i, j]))*log10(num/df[j])
        return X, y

    X_train, y_train = getXy(tokens_train)
    X_dev,  y_dev  = getXy(tokens_dev)
    X_test, y_test  = getXy(tokens_test)

    # SVC Fit --------------------

    model = SVC(C=C)
    model.fit(X_train, y_train)

    def model_stats(X, y):
        y_pred = model.predict(X)
        corpora_stats = {}
        for c in range(len(corpora)):
            P  = sum(np.logical_and(y == c, y_pred == c)) / sum(y_pred == c)
            R  = sum(np.logical_and(y == c, y_pred == c)) / sum(y == c)
            F1 = 2*P*R/(P+R)
            corpora_stats[corpora[c]] = {'P':P, 'R':R, 'F1':F1}
        return corpora_stats

    return {'train':model_stats(X_train, y_train), 'dev':model_stats(X_dev, y_dev), 'test':model_stats(X_test, y_test)}


def write_text_classifier():
    path, test = "train_and_dev.tsv", "test.tsv"
    out = {'baseline':text_classifier(path, test), 'improved':text_classifier(path, test, idf=True, C=6)}
    _val  = lambda c, m : np.round(out[sys][split][c][m], 3)
    _mean = lambda m : np.round(np.mean([stats[m] for stats in out[sys][split].values()]), 3)

    def _mean(m):
        temp = []
        for stats in out[sys][split].values():
            temp.append(stats[m])
        return np.round(np.mean(temp), 3)


    df = pd.DataFrame(columns=['system', 'split', 'p-quran', 'r-quran', 'f-quran', 'p-ot', 'r-ot', 'f-ot', 'p-nt', 'r-nt', 'f-nt', 'p-macro', 'r-macro', 'f-macro'])
    for sys in out:
        for split in out[sys]:
            inp = [sys, split, _val('Quran', 'P'), _val('Quran', 'R'), _val('Quran', 'F1'), _val('OT', 'P'), _val('OT', 'R'), _val('OT', 'F1'), _val('NT', 'P'), _val('NT', 'R'), _val('NT','F1'), _mean('P'), _mean('R'), _mean('F1')]
            row = pd.DataFrame([inp], columns=['system', 'split', 'p-quran', 'r-quran', 'f-quran', 'p-ot', 'r-ot', 'f-ot', 'p-nt', 'r-nt', 'f-nt', 'p-macro', 'r-macro', 'f-macro'])
            df = df.append(row, ignore_index=True)
    
    df.to_csv(codepath / "classification.csv", index=False)

print(f'\nPart 3 : Text Classification\n')
print(f"\tWriting classification")
write_text_classifier()
