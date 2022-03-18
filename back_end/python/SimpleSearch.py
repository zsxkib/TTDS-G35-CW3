
## ==================================================
##
##   Simple Search Programs for Parent Class 
##
## ==================================================

# Imports ------------------------------------------

import os
import re
import xml
import json
import math as m
from time import sleep, time
from tqdm import tqdm
from pathlib import Path
from nltk.stem.porter import PorterStemmer
from concurrent.futures import ProcessPoolExecutor



class ClassicSearch:

    def __init__(self, indexpath):
        self.indexpath = Path(indexpath)

        with open("/home/dan/TTDS-G35-CW3/back_end/python/stopwords.txt") as f:
            self.stopwords = f.read().splitlines() 

        with open(self.indexpath / "_pids.json", 'r') as f:
            self.pids = json.loads(f.read())



# --------------------------------------------------
#   Preprocessing
# --------------------------------------------------

    def textprocessing(self, text, printer=False):
        tokens = [word.strip() for word in re.split('[^a-zA-Z0-9]', text) if word != '' and word.lower() not in self.stopwords]
        terms  = [PorterStemmer().stem(word) for word in tokens]

        if printer: print(f"\t- Queryprocessing : {text} --> {terms}")
        return terms


# --------------------------------------------------
#   Index Translation
# --------------------------------------------------

    def index(self, term, pid=None):
        try:
            with open(self.indexpath / term[:3], 'r') as f:
                data = json.loads(f.read())
                if pid != None:
                    return data[term][pid]
                else:
                    return data[term]
        except:
            return {}


# --------------------------------------------------
#   Query Exectution
# --------------------------------------------------

    def rankedIR(self, query):
        print(f'\tRunning Ranked IR with query : {query}.')
        N = len(self.pids)

        tf = lambda term, pid : len(self.index(term, pid)) 
        df = lambda term : len(self.index(term))
        weight = lambda term, pid : (1 + m.log10(tf(term, pid))) * m.log10(N / df(term))

        queryTerms = self.textprocessing(query)
        docScores = {}

        for term in queryTerms:
            print(term)
            for pid in self.index(term):
                if pid not in docScores:
                    docScores[pid] = 0
                print("\t", pid)
                docScores[pid] += weight(term, pid)
        return docScores


    # Proximity Search Functions -------------------

    def proxRec(self, queryTerms, d, absol, out=None):
        if queryTerms == []:
            return out
        else:
            term = queryTerms.pop()
            if out == None:
                return self.proxRec(queryTerms, d, absol, self.index(term))
            for pid in out:
                if pid in self.index(term):
                    for n in list(out[pid]):
                        if absol and True not in [n+a in self.index(term, pid) for a in range(-d,d+1) if a != 0]:
                            out[pid].remove(n)
                        if not absol and True not in [n+a in self.index(term, pid) for a in range(0,d+1) if a != 0]:
                            out[pid].remove(n)
                if pid not in self.index(term) or out[pid] == []:
                    out.pop(pid)
            return self.proxRec(queryTerms, d, absol, out)


    def proximitySearch(self, query, distance=0, absol=True):
        print(f"\n\tRunning Proxmimity Search with query : {query} and allowed distance : {distance}.")

        query = self.textprocessing(query)
        query.reverse()
        return self.proxRec(query, distance+len(query), absol)


    # Boolean Search Functions ---------------------

    def getLocations(self, i, cmds):
        if cmds[i] != 'NOT':
            return set(self.proxRec(self.textprocessing(cmds[i])[::-1], 1, False).keys())
        else:
            return set(self.proxRec(self.textprocessing(cmds[i+1])[::-1], 1, False).keys()).symmetric_difference(set(self.tags.keys()))


    def booleanSearch(self, query):
        print(f'\n\tRunning Boolean Search with query : {query.strip()}.')
        cmds = [x[1:-1] if x[0] == '"' else x for x in re.split("( |\\\".*?\\\"|'.*?')", query) if x != '' and x != ' ']

        output = self.getLocations(0, cmds)
        for i in range(len(cmds)):
            if cmds[i] == 'AND':
                output &= self.getLocations(i+1, cmds) # Updating Intesect
            if cmds[i] == 'OR':
                output |= self.getLocations(i+1, cmds) # Updating Union
        return output



class IRSearch():

    def __init__(self, indexpath):
        self.indexpath = Path(indexpath)

        with open("/home/dan/TTDS-G35-CW3/back_end/python/stopwords.txt") as f:
            self.stopwords = f.read().splitlines() 

        with open(self.indexpath / "_pids.txt", 'r') as f:
            self.pids = {}
            for t in f.read().split('\n'):
                if t == "": break
                pid, title = t.split('>')
                self.pids[pid] = title
        


    def textprocessing(self, text, printer=False):
        tokens = [word.strip() for word in re.split('[^a-zA-Z0-9]', text) if word != '' and word.lower() not in self.stopwords]
        terms  = [PorterStemmer().stem(word) for word in tokens]

        if printer: print(f"\t- Queryprocessing : {text} --> {terms}")
        return terms


    def rankedIR(self, query):
        N = len(self.pids)

        weight = lambda tf, df : (1 + m.log10(tf)) * m.log10(N / df)

        queryTerms = self.textprocessing(query)
        docScores = {}

        for term in queryTerms:
            if not os.path.isfile(self.indexpath / term): continue
            with open(self.indexpath / term) as f:
                info = f.read().split('\n')
                for page in info[1:]:
                    pid, num = page.split(':')
                    if pid not in docScores:
                        docScores[pid] = 0
                    docScores[pid] += weight(int(num), int(info[0]))
                
        return docScores




# Test Executions ----------------------------------


# print("Running...")
# start = time()

# classic = ClassicSearch(
#     Path.cwd() / "TTDS-G35-CW3/back_end/index/positionalIndex/Index", 
#     )
# ranked = IRSearch(
#     Path.cwd() / "TTDS-G35-CW3/back_end/index/rankedIndex/Index", 
#     )


# Question = "orange"

# print(f"\nResults : {classic.booleanSearch(Question)}")
# print(f"\nResults : {ranked.rankedIR(Question)}")
# print(f"IR Search Executed in {round(time()-start, 1)} secs\n")
