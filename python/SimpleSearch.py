
## ==================================================
##
##   Simple Search Programs for Parent Class 
##
## ==================================================

# Imports ------------------------------------------

from __future__ import print_function
import os
import re
import json
import math as m
from time import time
from tqdm import tqdm
from pathlib import Path
from sklearn import preprocessing
import xml.etree.ElementTree as ET
from nltk.stem.porter import PorterStemmer
from concurrent.futures import ThreadPoolExecutor

_allcorpora = ['description', 'developer']

class SimpleSearch:

    def __init__(self, path, preindex=True, rerun=False, quiet=True, threaded='single'):
        self.path = path
        self.rerun = rerun
        self.quiet = quiet
        self.threaded = threaded                          # Multithreaded is only turned on if threads is raised higher than 1
        self.filterCorpora('ALL')
        self.datapath = Path.cwd() / "python" / path
        self.indexpath = lambda label : Path.cwd() / "data" / f"{label}.{path[:-4]}.json"
        start = time()
        self.tags, self.xmldata = self.readXML()
        print(f"Read XML : {time()-start}")
        if preindex: self.fullIndex()

    
    def filterCorpora(self, corpora='ALL'):
        if corpora == 'ALL':
            self.corpora = _allcorpora
        else:
            self.corpora = corpora
        print(f"\nCorpora filter set to {self.corpora}")

    def getErrors(self):
        for i, m in self.xmlerrors.items():
            print(f"XML Error : ID {i} Missing Tags -> {m}")


# --------------------------------------------------
#   Preprocessing
# --------------------------------------------------

    def readXML(self):
        print(f"\nReading XML from {self.datapath}...")
        tags = {}
        data = {corpus:{} for corpus in self.corpora}

        tree = ET.parse(self.datapath)
        root = tree.getroot()
        self.xmlerrors = {}
        for doc in root:
            try:
                tags[doc.find('game_id').text] = {"name":doc.find('game_name').text, "genre":doc.find('genres').text.split(' | ')[0]}
                for corpus in data.keys():
                    data[corpus][doc.find('game_id').text] = f"{doc.find(corpus).text}"       
            except:
                missing = []
                for tag in _allcorpora + ['genres', 'game_name', 'game_id']:
                    if doc.find(tag) == None:
                        missing.append(tag)
                    elif doc.find(tag).text == None:
                        missing.append(tag)
                    else:
                        identifier = doc.find(tag).text
                self.xmlerrors[identifier] = missing
                if not self.quiet : print(f"XML Error : ID {identifier} Missing Tags -> {missing}")
        return tags, data


    def preprocessing(self, data):
        print(f"\t- Preprocessing {type(data)}...")
        if type(data) == str: data = {0:{0:data}}

        with open(Path.cwd() / "python" / "stopwords.txt") as f:
            stopwords = f.read().splitlines() 

        tokens = {corpus:{gid:[word.strip() for word in re.split('[^a-zA-Z0-9]', text) if word != '' and word.lower() not in stopwords] for gid, text in tqdm(entries.items())} for corpus, entries in data.items()}    
        terms  = {corpus:{gid:[PorterStemmer().stem(word) for word in text] for gid, text in tqdm(entries.items())} for corpus, entries in tokens.items()} 

        if type(data) == str: return terms[0][0]
        return tokens, terms


# --------------------------------------------------
#   Indexing
# --------------------------------------------------

    def fullIndex(self):
        print("Getting all indexes:") if self.threaded == 'single' else print("Getting all indexes using {self.threaded} as threads:")
        self.indexes = {'pos':None, 'seq':None, 'bool':None, 'freq':None}
        start = time()
        if not os.path.isfile(self.indexpath('preprocess')) or self.rerun:
            if self.threaded == 'single':
                self.tokens, self.terms = self.preprocessing(self.xmldata)
            else:
                self.tokens, self.terms = {}, {}
                num_threads = len(self.corpora) #if self.threaded == 'corpora' 
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    for subtokens, subterms in executor.map(self.preprocessing, [{corpus:entries} for corpus, entries in self.xmldata.items()]):
                        self.tokens |= subtokens
                        self.terms  |= subterms
                    print(self.tokens)
            with open(self.indexpath('preprocess'), 'w') as f:    
                f.write(json.dumps([self.tokens, self.terms]))
        else:
            with open(self.indexpath('preprocess'), 'r') as f:
                self.tokens, self.terms = json.loads(f.read())
        print(f"Preprocess : {time()-start}")

        start = time()
        for method in self.indexes.keys():
            print(f"\t- Getting Index : {method}")
            if not os.path.isfile(self.indexpath(method)) or self.rerun:
                self.indexes[method] = self.indexing(method)
                with open(self.indexpath(method), 'w') as f:    
                    f.write(json.dumps(self.indexes[method]))
            else:
                with open(self.indexpath(method), 'r') as f:
                    self.indexes[method] = json.loads(f.read())
        print(f"{time()-start}")


    def indexing(self, method):
        print("\t\t Indexing working...")
        index = {}
        if self.threaded == 'single':
            for corpus in self.terms:
                index |= self.perCorporaIndexing(method, corpus)
        else:
            num_threads = len(self.corpora) #if self.threaded == 'corpora' 
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                for subIndex in executor.map(self.preprocessing, [{corpus:entries} for corpus, entries in self.xmldata.items()]):
                    index |= subIndex[0]
        return index


    def perCorporaIndexing(self, method, corpus):
        index = {}
        index[corpus] = {}
        for gid in self.terms[corpus]:
            if method == 'pos':
                for i in range(len(self.terms[corpus][gid])):
                    term = self.terms[corpus][gid][i]
                    if term not in index[corpus]:
                        index[corpus][term] = {}
                    if gid in index[corpus][term]:
                        index[corpus][term][gid].append(i+1)
                    else:
                        index[corpus][term][gid] = [i+1]
            elif method == 'seq':
                index[corpus][gid] = [f"{self.terms[corpus][gid][i-1]}_{self.terms[corpus][gid][i]}" for i in range(len(self.terms[corpus][gid])) if i > 0]
            else:
                for term in self.terms[corpus][gid]:
                    if term not in index[corpus]:
                        index[corpus][term] = {}
                    if method == 'bool':
                        index[corpus][term][gid] = 1
                    else:
                        if gid not in index[corpus][term]:
                            index[corpus][term][gid] = 0
                        index[corpus][term][gid] += 1
        return index


# --------------------------------------------------
#   Query Exectution
# --------------------------------------------------

    def phraseSearch(self, query):
        print(f'\n\tRunning Phrase Search on {self.corpora} with query : {query}.')
        index = self.indexes['seq']
        processedQuery = self.preprocessing(query)
        seqQuery = f"{processedQuery[0]}_{processedQuery[1]}"
        
        out = {}
        for corpus in self.corpora:
            for gid in index[corpus]:
                for pos in range(len(index[corpus][gid])):
                    if index[gid][corpus][pos] == seqQuery:
                        if gid not in out:
                            out[gid] = {}
                        if corpus not in out[gid]:
                            out[gid][corpus] = []
                        out[gid][corpus].append(pos+1)
        return out

    def rankedIR(self, query):
        print(f'\tRunning Ranked IR on {self.corpora} with query : {query}.\n')
        index = self.indexes['pos']
        N = len(self.tags.keys())

        tf = lambda corpus, term, gid : len(index[corpus][term][gid]) 
        df = lambda corpus, term : len(index[corpus][term])
        weight = lambda corpus, term, gid : (1 + m.log10(tf(corpus, term, gid))) * m.log10(N / df(corpus, term))

        queryTerms = self.preprocessing(query)
        docScores = {}

        for corpus in self.corpora:
            for term in queryTerms:
                for gid in index[corpus][term]:
                    if gid not in docScores:
                        docScores[gid] = {}
                    if corpus not in docScores[gid]:
                        docScores[gid][corpus] = 0
                    docScores[gid][corpus] += weight(corpus, term, gid)
                
        return docScores

    # Proximity Search Functions -------------------

    def proxRec(self, queryTerms, d, absol, out=None):
        index = self.indexes['pos']
        if queryTerms == []:
            return out
        else:
            term = queryTerms.pop()
            if out == None:
                return self.proxRec(queryTerms, d, absol, {corpus:index[corpus][term] for corpus in self.corpora if term in index[corpus]})
            for corpus in self.corpora:
                if term not in index[corpus]:
                    out.pop(corpus)
                for gid in dict(out[corpus]):   
                    if gid in index[corpus][term]:
                        for n in list(out[corpus][gid]):
                            if absol and True not in [n+a in index[corpus][term][gid] for a in range(-d,d+1) if a != 0]:
                                out[corpus][gid].remove(n)
                            if not absol and True not in [n+a in index[corpus][term][gid] for a in range(0,d+1) if a != 0]:
                                out[corpus][gid].remove(n)
                    if gid not in index[corpus][term] or out[corpus][gid] == []:
                        out[corpus].pop(gid)
            return self.proxRec(queryTerms, d, absol, out)

    def proximitySearch(self, query, distance=1, absol=True):
        print(f'\n\tRunning Proxmimity Search on {self.corpora} with query : {query} and allowed distance : {distance}.')

        queryTerms = query
        if type(query) == str: queryTerms = preprocessing(query)
        
        queryTerms.reverse()
        return self.proxRec(queryTerms, distance, absol)

    # Boolean Search Functions ---------------------

    def getLocations(self, i, cmds, corpus):
        if cmds[i] != 'NOT':
            return set(self.proximitySearch(self.indexes[corpus]['pos'], cmds[i], absol=False).keys())
        else:
            return set(self.proximitySearch(self.indexes[corpus]['pos'], cmds[i+1], absol=False).keys()).symmetric_difference(set(self.tags.keys()))

    def booleanSearch(self, query):
        print(f'\n\tRunning Boolean Search on {self.corpora} with query : {query.strip()}.')

        cmds = [x[1:-1] if x[0] == '"' else x for x in re.split("( |\\\".*?\\\"|'.*?')", query) if x != '' and x != ' ']

        output = {}
        for corpus in self.corpora:
            output[corpus] = self.getLocations(0, cmds, corpus)
            for i in range(len(cmds)):
                if cmds[i] == 'AND':
                    output[corpus] &= self.getLocations(i+1, cmds, corpus) # Updating Intesect
                if cmds[i] == 'OR':    
                    output[corpus] |= self.getLocations(i+1, cmds, corpus) # Updating Union
        return output


# Test Executions ----------------------------------

# print("Running...")
# start = time()
# test = SimpleSearch("test.xml")
# data = SimpleSearch("data.xml")
# print(f"\nExecuted in {round(time()-start, 1)} secs")
