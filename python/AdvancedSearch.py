## ==================================================
##
##   Advanced Search Programs for Child Class 
##
## ==================================================

# Imports ------------------------------------------

import os
import numpy as np
from time import time
from math import log10
from pathlib import Path
from sklearn.svm import SVC
from scipy.sparse import dok_matrix
from SimpleSearch import SimpleSearch
from gensim.models.ldamodel import LdaModel
from gensim.corpora.dictionary import Dictionary


class AdvancedSearch(SimpleSearch):

    def __init__(self, path, preindex=True, rerun=False, quiet=True):
        super().__init__(path, preindex, rerun, quiet)


# --------------------------------------------------
#   Text Analysis
# --------------------------------------------------

# Text Analysis --------------------------------

    def analysis(self, method, corpora): 
        print(f"\n\tRunning Text Analysis on {corpora} using {method} method.")
        if len(corpora) != 3: print("\tText Analysis currently only works when using 3 corpora."); return None

        Ngids = {corpus:len(self.terms[corpus]) for corpus in corpora}
        index = self.indexes['bool']
        out = {corpus:{} for corpus in corpora}
        for corpus in out:
            incorpus = list(index.keys()); incorpus.remove(str(corpus))
            num  = Ngids[corpus]
            inum = Ngids[incorpus[0]] + Ngids[incorpus[1]]
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


    def lda(self):
        print(f"\n\tRunning the LDA Model on {self.corpora}.")
        fileLoc = Path.cwd() / "data" / f"LDA_{self.path[:-4]}"
        #docs = [doc for corpus in self.terms.values() for doc in corpus.values()]
        docs = [doc for corpus, entries in self.terms.items() for doc in entries.values() if corpus in self.corpora]
        dct = Dictionary(docs)
        corpora = [dct.doc2bow(doc) for doc in docs]

        if not os.path.isfile(str(fileLoc)) or self.rerun:
            LdaModel(corpora, num_topics=20, id2word=dct).save(str(fileLoc))
        lda = LdaModel.load(str(fileLoc))

        ats = {}    # Average Topic Score
        phase = 0
        highest_topics = {}
        for corpus in self.terms:
            ats[corpus] = {}
            for doc in range(len(self.terms[corpus])):
                for id in lda.get_document_topics(corpora[doc+phase]):
                    if id[0] not in ats[corpus]:
                        ats[corpus][id[0]] = 0
                    ats[corpus][id[0]] += id[1]  
                        
            l = len(self.terms[corpus])
            phase += l
            ats[corpus] = {t:v/l for t, v in ats[corpus].items()}
            max_ats = max(ats[corpus], key=ats[corpus].get)
            highest_topics[corpus] = (max_ats, round(ats[corpus][max_ats], 3), lda.print_topic(max_ats))
        return highest_topics


    # --------------------------------------------------
    #   Text Classification
    # --------------------------------------------------

    def classifier(self, tag, stem=False, idf=False, C=1000):
        print(f"\n\tRunning the Tag Classifier on {self.corpora} using {tag} tag.")

        if stem:
            tokerms = self.terms
        else:
            tokerms = self.tokens

        # Extract Features -----------------------

        self.uniqueTokerms = []
        self.uniqueGIDs = []
        self.uniqueTags = []

        for corpus in self.corpora:
            for gids, text in tokerms[corpus].items():
                for gid in gids:
                    if gid not in self.uniqueGIDs:
                        self.uniqueGIDs.append(gid)
                for tokerm in text:
                    if tokerm not in self.uniqueTokerms:
                        self.uniqueTokerms.append(tokerm)

        for gids in self.tags.values():
            for genre in gids[tag]:
                if genre not in self.self.uniqueTags:
                    self.uniqueTags.append(genre)

        X, y = self.getXy(tokerms, tag, idf)

        # SVC Fit --------------------

        self.model = SVC(C=C)
        self.model.fit(X, y)


    def createXy(self, tokerms, tag, idf=False):
        y = np.empty(len(self.uniqueGIDs))
        X = dok_matrix((len(self.uniqueGIDs), len(self.uniqueTokerms)))
        for i, gid in enumerate(self.uniqueGIDs):
            y[i] = self.self.uniqueTags.index(self.tags[gid][tag])  # Zero as more than one genre!
            for corpus in self.corpora:
                for tokerm in tokerms[corpus][i][1]:
                    if tokerm in self.uniqueTokerms:
                        X[i, self.uniqueTokerms.index(tokerm)] += 1

        if idf:           
            df = [sum([1 for corpus in tokerms.values() for doc in corpus.values() if token in doc]) for token in self.uniqueTokerms]
            for corpus in self.corpora:
                for tokerm in tokerms[corpus][i][1]:
                    for tokerm in tokerms[i][1]:
                        if tokerm in self.uniqueTokerms:
                            j = self.uniqueTokerms.index(tokerm)
                            if type(X[i, j]) == float:
                                X[i, j] = (1+ np.log10(X[i, j]))*log10(len(self.uniqueGIDs)/df[j])
        return X, y


    def classifierStats(self, X, y):
        pred = self.model.predict(X)
        stats = {}
        for c in range(len(self.corpora)):
            P  = sum(np.logical_and(y == c, pred == c)) / sum(pred == c)
            R  = sum(np.logical_and(y == c, pred == c)) / sum(y == c)
            F1 = 2*P*R/(P+R)
            stats[self.corpora[c]] = {'P':P, 'R':R, 'F1':F1}
        return stats



# Test Executions ----------------------------------

# print("Running...")
# start = time()
# test = AdvancedSearch("test.xml")
# data = AdvancedSearch("data.xml")
# print(f"\nExecuted in {round(time()-start, 1)} secs")
