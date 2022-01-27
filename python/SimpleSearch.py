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
        self.datapath = Path.cwd() / "source" / path
        self.indexpath = lambda label : Path.cwd() / "data" / f"{label}.{path[:-4]}.json"
        self.tags, self.xmldata = self.readXML()
        if preindex: self.fullIndex(rerun)


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
                data[doc.find('game_id').text] = (f"{doc.find('description').text}")
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
        if type(data) == str: data = {0:data}

        with open(Path.cwd() / "source" / "stopwords.txt") as f:
            stopwords = f.read().splitlines() 

        tokens = {}
        for docno in data:                                                                                                              # Use dictionary comprehension
            tokens[docno] = ([x.strip() for x in re.split('[^a-zA-Z0-9]', data[docno]) if x != '' and x.lower() not in stopwords])
            
        terms = {key:[PorterStemmer().stem(x) for x in vals] for (key,vals) in tokens.items()}

        if type(data) == str: return terms[0]
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

        for line in self.terms:
            if method == 'pos':
                for i in range(len(self.terms[line])):
                    term = self.terms[line][i]
                    if term not in index:
                        index[term] = {}
                    if line in index[term]:
                        index[term][line].append(i+1)
                    else:
                        index[term][line] = [i+1]
            elif method == 'seq':
                index[line] = [f"{self.terms[line][i-1]}_{self.terms[line][i]}" for i in range(len(self.terms[line])) if i > 0]
            else:
                for term in self.terms[line]:
                    if term not in index:
                        index[term] = {}
                    if method == 'bool':
                        index[term][line] = 1 # Slightly redundant
                    else:
                        if line not in index[term]:
                            index[term][line] = 0
                        index[term][line] += 1
        return index


# --------------------------------------------------
#   Query Exectution
# --------------------------------------------------

    def phraseSearch(self, query):
        print(f'\n\tRunning Phrase Search with query : {query}.')
        index = self.indexes['seq']
        processedQuery = self.preprocessing(query)
        seqQuery = f"{processedQuery[0]}_{processedQuery[1]}"
        
        out = {}
        for line in index:
            for pos in range(len(index[line])):
                if index[line][pos] == seqQuery:
                    if line not in out:
                        out[line] = []
                    out[line].append(pos+1)
        return out

    def rankedIR(self, query):
        index = self.indexes['pos']
        print(f'\tRunning Ranked IR with query : {query}.\n')
        N = len(self.tags.keys())

        tf = lambda term, line : len(index[term][line]) 
        df = lambda term : len(index[term])
        weight = lambda term, line : (1 + m.log10(tf(term, line))) * m.log10(N / df(term))

        queryTerms = self.preprocessing(query)
        docScores = {}

        for term in queryTerms:
            for line in index[term]:
                if line not in docScores:
                    docScores[line] = 0
                docScores[line] += weight(term, line)
                
        return docScores

    # Proximity Search Functions -----------------------------------------------

    def proxRec(self, queryTerms, d, absol, out=None):
        index = self.indexes['pos']
        if queryTerms == []:
            return out
        else:
            key = queryTerms.pop()
            if out == None:
                return self.proxRec(index, queryTerms, d, absol, index[key])
            if key not in index:
                return {}
            for l in dict(out):
                if l in index[key]:
                    for n in list(out[l]):
                        if absol and True not in [n+a in index[key][l] for a in range(-d,d+1) if a != 0]:
                            out[l].remove(n)
                        if not absol and True not in [n+a in index[key][l] for a in range(0,d+1) if a != 0]:
                            out[l].remove(n)
                if l not in index[key] or out[l] == []:
                    out.pop(l)
            return self.proxRec(queryTerms, d, absol, out)

    def proximitySearch(self, query, distance=1, absol=True):
        print(f'\n\tRunning Proxmimity Search with query : {query} and allowed distance : {distance}.')

        queryTerms = query
        if type(query) == str: queryTerms = preprocessing(query)
        
        queryTerms.reverse()
        return self.proxRec(queryTerms, distance, absol)

    # Boolean Search Functions -------------------------------------------------

    def getLocations(self, i, cmds):
        if cmds[i] != 'NOT':
            return set(self.proximitySearch(self.indexes['pos'], cmds[i], absol=False).keys())
        else:
            return set(self.proximitySearch(self.indexes['pos'], cmds[i+1], absol=False).keys()).symmetric_difference(set(self.tags.keys()))

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


# Executions ---------------------------------------

# print("Running...")
# start = time()
# test = SimpleSearch("data.xml", rerun=True)

# a = test.indexes

# print(f"\nExecuted in {time()-start} secs")
