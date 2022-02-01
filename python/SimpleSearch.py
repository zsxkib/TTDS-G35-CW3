
## ==================================================
##
##   Simple Search Programs for Parent Class 
##
## ==================================================

# Imports ------------------------------------------

import os
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import re
import math as m
from time import time
from nltk.stem.porter import PorterStemmer
from sklearn import preprocessing

class SimpleSearch:

    def __init__(self, path, preindex=True, rerun=False):
        self.path = path
        self.datapath = Path.cwd() / "python" / path
        self.indexpath = lambda label : Path.cwd() / "data" / f"{label}.{path[:-4]}.json"
        self.tags, self.xmldata = self.readXML()
        if preindex: self.fullIndex(rerun)

    
    def filterCorpora(self, corpora):
        if corpora == 'ALL':
            self.corpora = list(self).indexes['pos'].keys())
        else:
            self.corpora = corpora


# --------------------------------------------------
#   Preprocessing
# --------------------------------------------------

    def readXML(self):
        tags = {}
        data = {}

        tree = ET.parse(self.datapath)
        root = tree.getroot()
        for doc in root:                                                                                                        # Use dictionary comprehension
            try:
                tags[doc.find('game_id').text] = {"name":doc.find('game_name').text}
                data[doc.find('game_id').text] = {corpus:f"{doc.find(corpus).text}" for corpus in ['description'] if doc.find(corpus) != None}
            except:
                missing = []
                for tag in ['description', 'game_name', 'game_id']:
                    if doc.find(tag) == None:
                        missing.append(tag)
                    else:
                        identifier = doc.find(tag).text
                print(f"XML Error : ID {identifier} Missing Tags -> {missing}")
        return tags, data


    def preprocessing(self, data):
        if type(data) == str: data = {0:{0:data}}

        with open(Path.cwd() / "source" / "stopwords.txt") as f:
            stopwords = f.read().splitlines() 

        tokens = {gid:{corpus:[word.strip() for word in re.split('[^a-zA-Z0-9]', text) if word != '' and word.lower() not in stopwords] for corpus, text in corpora.items()} for gid, corpora in data.items()}
        terms  = {gid:{corpus:[PorterStemmer().stem(word) for word in text] for corpus, text in corpora.items()} for gid, corpora in tokens.items()}

        if type(data) == str: return terms[0][0]
        return terms


# --------------------------------------------------
#   Indexing
# --------------------------------------------------

    def fullIndex(self, rerun):
        self.terms = None
        self.indexes = {'pos':None, 'seq':None, 'bool':None, 'freq':None}
        for method in self.indexes.keys():
            if not os.path.isfile(self.indexpath(method)) or rerun:
                self.terms = self.preprocessing(self.xmldata) if self.terms == None else self.terms
                self.indexes[method] = self.indexing(method)
                with open(self.indexpath(method), 'w') as f:    
                    f.write(json.dumps(self.indexes[method]))
            else:
                with open(self.indexpath(method), 'r') as f:
                    self.indexes[method] = json.loads(f.read())


    def indexing(self, method):
        index = {}
        
        for gid in self.terms:
            for corpus in self.term[gid]:
                index[corpus] = {}
                if method == 'pos':
                    for i in range(len(self.terms[gid][corpus])):
                        term = self.terms[gid][corpus][i]
                        if term not in index[corpus]:
                            index[corpus][term] = {}
                        if gid in index[corpus][term]:
                            index[corpus][term][gid].append(i+1)
                        else:
                            index[corpus][term][gid] = [i+1]
                elif method == 'seq':
                    index[corpus][gid] = [f"{self.terms[gid][corpus][i-1]}_{self.terms[gid][corpus][i]}" for i in range(len(self.terms[gid][corpus])) if i > 0]
                else:
                    for term in self.terms[gid][corpus]:
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
        print(f'\n\tRunning Proxmimity Search with query : {query} and allowed distance : {distance}.')

        queryTerms = query
        if type(query) == str: queryTerms = preprocessing(query)
        
        queryTerms.reverse()
        return self.proxRec(queryTerms, distance, absol)

    # Boolean Search Functions ---------------------

    def getLocations(self, i, cmds):
        if cmds[i] != 'NOT':
            return set(self.proximitySearch(self.indexes[corpus]['pos'], cmds[i], absol=False).keys())
        else:
            return set(self.proximitySearch(self.indexes[corpus]['pos'], cmds[i+1], absol=False).keys()).symmetric_difference(set(self.tags.keys()))

    def booleanSearch(self, query):
        print(f'\n\tRunning Boolean Search with query : {query.strip()}.')

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
# test = SimpleSearch("data.xml", rerun=True)

# a = test.indexes

# print(f"\nExecuted in {time()-start} secs")
