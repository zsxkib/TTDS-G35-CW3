## ==================================================
##
##   Advanced Search Programs for Child Class 
##
## ==================================================

# Imports ------------------------------------------

from SimpleSearch import SimpleSearch
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
from nltk.stem.porter import PorterStemmer
from time import time


class AdvancedSearch(SimpleSearch):

    def __init__(self, path, preindex=True, rerun=False):
        super().__init__(path, preindex, rerun)


# --------------------------------------------------
#   Text Analysis
# --------------------------------------------------

# Text Analysis --------------------------------

    def text_analysis(self, method): 
        ns = self.tags.keys()
        index = self.indexes['pos']
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

    # print(f'\nPart 2 : Text Analysis\n')
    # print("  Token Analysis:")
    # path = "train_and_dev.tsv"
    # index = getIndex(path)
    # MI = text_analysis(index, 'MI')
    # X2 = text_analysis(index, 'X2')
    # for c in MI.keys():
    #     print(f"\n\t___________{c}___________")
    #     print(f"\t  MI\t\t  X2")
    #     for i in range(10):
    #         if len(MI[c][i][0]) > 7:
    #             print(f"\t{MI[c][i][0]}\t{X2[c][i][0]}")
    #         else:
    #             print(f"\t{MI[c][i][0]}\t\t{X2[c][i][0]}")

    # print("\n  Topic Analysis:")
    # highest_topics = LDA(path)
    # for c in highest_topics:
    #     print(f'\t{c} : Topic {highest_topics[c][0]} with score {highest_topics[c][1]}\n\t\t{highest_topics[c][2]}\n')

    # --------------------------------------------------
    #   Text Classification
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

# Executions ---------------------------------------

print("Running...")
start = time()
test = AdvancedSearch("test.xml")

a = test.indexes
print(a)

print(f"\nExecuted in {time()-start} secs")
