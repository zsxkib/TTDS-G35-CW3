
## ==================================================
##
##   Simple Search Programs for Parent Class 
##
## ==================================================

# Imports ------------------------------------------

import enum
import os
import re
import json
import pymongo
import math as m
from time import time
from tqdm import tqdm
from lxml import etree
from pathlib import Path
from itertools import islice
from sklearn import preprocessing
import xml.etree.ElementTree as ET
from nltk.stem.porter import PorterStemmer
from concurrent.futures import ThreadPoolExecutor


class ClassicSearch:

    def __init__(self, path, preindex=['pos'], rerun=False, quiet=True, threads=1, debug=False):
        self.datapath = Path(path)
        self.rerun = rerun
        self.quiet = quiet
        self.errors = {"xml":{}, "index":[]}
        self.threads = threads                          # Multithreaded is only turned on if threads is raised higher than 1
        self.debug = debug
        self.indexpath = lambda label : Path.cwd() / "data" / f"{label}.{self.datapath.name.split('.')[0]}.json"
        start = time()
        self.tags, self.xmldata = self.readXML()
        if self.debug: print(f"Read XML : {time()-start}s")
        if preindex != [] and type(preindex) == list: self.loadIndexes(preindex)

    
    def splitDict(self, data, blocks):
        size = m.ceil(len(data)/blocks)
        for i in range(0, len(data), size):
            yield {k:data[k] for k in islice(iter(data), size)}

    def getErrors(self):
        for i, m in self.xmlerrors.items():
            print(f"XML Error : ID {i} Missing Tags -> {m}")


# --------------------------------------------------
#   Preprocessing
# --------------------------------------------------

    def readXML(self):
        print(f"\nReading XML from {self.datapath}...")
        tags = {}
        data = {}

        tree = ET.parse(self.datapath)
        root = tree.getroot()
        for doc in root:
            try:
                tags[doc.find('id').text] = {"title":doc.find('title').text}
                data[doc.find('id').text] = f"{doc.find('revision').find('text').text}"  
            except:
                missing = []
                for tag in ['text', 'title', 'id']:
                    if doc.find(tag) == None:
                        missing.append(tag)
                    elif doc.find(tag).text == None:
                        missing.append(tag)
                    else:
                        identifier = doc.find(tag).text
                self.errors["xml"][identifier] = missing
                if not self.quiet : print(f"XML Error : ID {identifier} Missing Tags -> {missing}")
        return tags, data


    def preprocessing(self, data):
        print(f"\t- Preprocessing {type(data)}...")

        with open(Path.cwd() / "python" / "stopwords.txt") as f:
            stopwords = f.read().splitlines() 

        tokens = {pid:[word.strip() for word in re.split('[^a-zA-Z0-9]', text) if word != '' and word.lower() not in stopwords] for pid, text in tqdm(data.items())}
        terms  = {pid:[PorterStemmer().stem(word) for word in text] for pid, text in tqdm(tokens.items())}
        return tokens, terms


    def queryprocessing(self, query):
        data = {"QUERY":query}

        with open(Path.cwd() / "python" / "stopwords.txt") as f:
            stopwords = f.read().splitlines() 

        tokens = {pid:[word.strip() for word in re.split('[^a-zA-Z0-9]', text) if word != '' and word.lower() not in stopwords] for pid, text in data.items()}
        terms  = {pid:[PorterStemmer().stem(word) for word in text] for pid, text in tokens.items()}

        print(f"\t- Queryprocessing : {query} --> {terms['QUERY']}")
        return terms["QUERY"]



# --------------------------------------------------
#   Indexing
# --------------------------------------------------

    def loadIndexes(self, methods):
        print("Getting {methods} indexes:") if self.threads == 1 else print("Getting {methods} indexes using {self.threads} as threads:")
        self.indexes = {method:None for method in methods}
        start = time()
        if not os.path.isfile(self.indexpath('preprocess')) or self.rerun:
            if self.threads == 1:
                self.tokens, self.terms = self.preprocessing(self.xmldata)
            else:
                self.tokens, self.terms = {}, {}
                with ThreadPoolExecutor(max_workers=self.threads) as executor:
                    for subtokens, subterms in executor.map(self.preprocessing, self.splitDict(self.xmldata, self.threads)):
                        self.tokens |= subtokens
                        self.terms  |= subterms
                    if self.debug: print(self.tokens)
            with open(self.indexpath('preprocess'), 'w') as f:    
                f.write(json.dumps([self.tokens, self.terms]))
        else:
            with open(self.indexpath('preprocess'), 'r') as f:
                self.tokens, self.terms = json.loads(f.read())
        if self.debug: print(f"Preprocess : {time()-start}s")

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
        if self.debug: print(f"Indexed : {time()-start}s")


    def indexing(self, method):
        print("\t\t Indexing working...")
        if self.threads == 1:
            index = self.subIndexing(method)
        else:
            index = {}
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                for subIndex in executor.map(self.subIndexing, self.splitDict(self.terms, self.threads)):
                    index |= subIndex[0]
        return index


    def subIndexing(self, method):
        index = {}
        for pid in self.terms:
            if method == 'pos':
                for i in range(len(self.terms[pid])):
                    term = self.terms[pid][i]
                    if term not in index:
                        index[term] = {}
                    if pid in index[term]:
                        index[term][pid].append(i+1)
                    else:
                        index[term][pid] = [i+1]
            elif method == 'seq':
                index[pid] = [f"{self.terms[pid][i-1]}_{self.terms[pid][i]}" for i in range(1, len(self.terms[pid]))]
            else:
                for term in self.terms[pid]:
                    if term not in index:
                        index[term] = {}
                    if method == 'bool':
                        index[term][pid] = 1
                    else:
                        if pid not in index[term]:
                            index[term][pid] = 0
                        index[term][pid] += 1
        return index


# --------------------------------------------------
#   Query Exectution
# --------------------------------------------------

    def phraseSearch(self, query):
        print(f'\n\tRunning Phrase Search with query : {query}.')
        try: index = self.indexes['seq']
        except: 
            self.errors['index'].append("Index Error : Sequential index missing for phraseSearch)")
            if not self.quiet: print(self.errors['index'][-1], "(try running : .loadIndexes(['seq']) )")
            return "ERROR"
        processedQuery = self.queryprocessing(query)
        seqQuery = f"{processedQuery[0]}_{processedQuery[1]}"
        
        out = {}
        for pid in index:
            for pos in range(len(index[pid])):
                if index[pid][pos] == seqQuery:
                    if pid not in out:
                        out[pid] = []
                    out[pid].append(pos+1)
        return out


    def rankedIR(self, query):
        print(f'\tRunning Ranked IR with query : {query}.')
        try: index = self.indexes['pos']
        except: 
            self.errors['index'].append("Index Error : Positional index missing for rankedIR")
            if not self.quiet: print(self.errors['index'][-1], "(try running : .loadIndexes(['pos']) )")
            return "ERROR"
        N = len(self.tags.keys())

        tf = lambda term, pid : len(index[term][pid]) 
        df = lambda term : len(index[term])
        weight = lambda term, pid : (1 + m.log10(tf(term, pid))) * m.log10(N / df(term))

        queryTerms = self.queryprocessing(query)
        docScores = {}

        for term in queryTerms:
            print(term)
            for pid in index[term]:
                if pid not in docScores:
                    docScores[pid] = 0
                print("\t", pid)
                docScores[pid] += weight(term, pid)
                
        return docScores


    # Proximity Search Functions -------------------

    def proxRec(self, index, queryTerms, d, absol, out=None):
        if queryTerms == []:
            return out
        else:
            term = queryTerms.pop()
            if term not in index:
                return {}
            if out == None:
                return self.proxRec(index, queryTerms, d, absol, index[term])
            for pid in dict(out):
                if pid in index[term]:
                    for n in list(out[pid]):
                        if absol and True not in [n+a in index[term][pid] for a in range(-d,d+1) if a != 0]:
                            out[pid].remove(n)
                        if not absol and True not in [n+a in index[term][pid] for a in range(0,d+1) if a != 0]:
                            out[pid].remove(n)
                if pid not in index[term] or out[pid] == []:
                    out.pop(pid)
            return self.proxRec(index, queryTerms, d, absol, out)


    def proximitySearch(self, query, distance=1, absol=True):
        print(f"\n\tRunning Proxmimity Search with query : {query} and allowed distance : {distance}.")
        try: index = self.indexes['pos']
        except: 
            self.errors['index'].append("Index Error : Positional index missing for proximitySearch")
            if not self.quiet: print(self.errors['index'][-1], "(try running : .loadIndexes(['pos']) )")
            return "ERROR"

        query = self.queryprocessing(query)
        query.reverse()
        return self.proxRec(index, query, distance, absol)


    # Boolean Search Functions ---------------------

    def getLocations(self, i, index, cmds):
        if cmds[i] != 'NOT':
            return set(self.proxRec(index, self.queryprocessing(cmds[i])[::-1], 1, False).keys())
        else:
            return set(self.proxRec(index, self.queryprocessing(cmds[i+1])[::-1], 1, False).keys()).symmetric_difference(set(self.tags.keys()))


    def booleanSearch(self, query):
        print(f'\n\tRunning Boolean Search with query : {query.strip()}.')
        try: index = self.indexes['pos']
        except: 
            self.errors['index'].append("Index Error : Positional index missing for booleanSearch")
            if not self.quiet: print(self.errors['index'][-1], "(try running : .loadIndexes(['pos']) )")
            return "ERROR"

        cmds = [x[1:-1] if x[0] == '"' else x for x in re.split("( |\\\".*?\\\"|'.*?')", query) if x != '' and x != ' ']

        output = self.getLocations(0, index, cmds)
        for i in range(len(cmds)):
            if cmds[i] == 'AND':
                output &= self.getLocations(i+1, index, cmds) # Updating Intesect
            if cmds[i] == 'OR':
                output |= self.getLocations(i+1, index, cmds) # Updating Union
        return output


class MongoSearch:

    def __init__(self, path, mongoaddress="localhost:27017", rerun=False, quiet=True, threads=2, debug=False):
        self.datapath = Path(path)
        self.dataname = self.datapath.name.split('.')[0]
        self.rerun = rerun
        self.quiet = quiet
        self.errors = {"xml":{}, "index":[]}
        self.threads = threads                          # Multithreaded is only turned on if threads is raised higher than 1
        self.debug = debug

        self.client = pymongo.MongoClient(f"mongodb://{mongoaddress}/")
        self.database = self.client[self.dataname]

        with open(Path.cwd() / "python" / "stopwords.txt") as f:
            self.stopwords = f.read().splitlines() 
        self.checkIndexes()

    
    def getErrors(self):
        for i, m in self.xmlerrors.items():
            print(f"XML Error : ID {i} Missing Tags -> {m}")


# --------------------------------------------------
#   Preprocessing
# --------------------------------------------------

    def readPages(self):
        page = ""
        for row in open(self.datapath, 'r'):
            if "<page>" in row:
                page = row
            if "<page>" in page:
                page += row
            if "</page>" in row:
                yield page
                page = ""


    def preprocessing(self, block):
        multprocessing = lambda d : {"pid":d["pid"], "title":d["title"], "text":self.textprocessing(d["text"])}
        def processtodb(data):
            terms = []
            with ThreadPoolExecutor(max_workers=block) as executor:
                for page in executor.map(multprocessing, data):
                    terms.append(page)
            self.database['terms'].insert_many(terms)
        
        print(f"\t- Preprocessing data in size {block} blocks...")
        data = []
        for page in self.readPages():
            data.append({"pid": int(re.split('<.?id>', page)[1]), "title": re.split('<.?title>', page)[1], "text": re.split('<.?text[^>]*>', page)[1]})
            if len(data) == block:
                processtodb(data)
                data = []
        processtodb(data)


    def textprocessing(self, text, printer=False):
        tokens = [word.strip() for word in re.split('[^a-zA-Z0-9]', text) if word != '' and word.lower() not in self.stopwords]
        terms  = [PorterStemmer().stem(word) for word in tokens]

        if printer: print(f"\t- Queryprocessing : {text} --> {terms}")
        return terms



# --------------------------------------------------
#   Indexing
# --------------------------------------------------

    def checkIndexes(self):
        print("Checking index:") if self.threads == 1 else print(f"Checking index using {self.threads} threads:")
        if "terms" not in self.database.list_collection_names() or self.rerun:
            start = time()
            self.database.terms.drop()
            self.preprocessing(self.threads)
            if self.debug: print(f"Preprocessed : {time()-start}s")

        if "index" not in self.database.list_collection_names() or self.rerun:
            print(f"\t- Indexing data with {self.threads} threads...")
            start = time()
            self.database.index.drop()
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                executor.map(self.subIndexing, self.database['terms'].find())
            if self.debug: print(f"Indexed : {time()-start}s")
        self.terms = self.database['terms']
        self.index = self.database['index']


    def subIndexing(self, page):
        for i, term in enumerate(page['text']):
            self.database['index'].insert_one({"term": term, "pid":page['pid'], "loc":i})


# --------------------------------------------------
#   Query Exectution
# --------------------------------------------------

    def rankedIR(self, query):
        print(f'\tRunning Ranked IR with query : {query}.')
        N = self.terms.count_documents({})

        termfreq = lambda term, pid : self.index.count_documents({"term":term, "pid":pid})
        docs = lambda term : self.index.find({"term":term}).distinct("pid")
        weight = lambda term, pid : (1 + m.log10(termfreq(term, pid))) * m.log10(N / len(docs(term)))

        queryTerms = self.textprocessing(query, True)
        docScores = {}

        for term in queryTerms:
            for pid in docs(term):
                if pid not in docScores:
                    docScores[pid] = 0
                docScores[pid] += weight(term, pid)
        return docScores


    # Proximity Search Functions -------------------

    def proxRec(self, index, queryTerms, d, absol, out=None):
        if queryTerms == []:
            return out
        else:
            term = queryTerms.pop()
            if term not in index:
                return {}
            if out == None:
                return self.proxRec(index, queryTerms, d, absol, index[term])
            for pid in dict(out):
                if pid in index[term]:
                    for n in list(out[pid]):
                        if absol and True not in [n+a in index[term][pid] for a in range(-d,d+1) if a != 0]:
                            out[pid].remove(n)
                        if not absol and True not in [n+a in index[term][pid] for a in range(0,d+1) if a != 0]:
                            out[pid].remove(n)
                if pid not in index[term] or out[pid] == []:
                    out.pop(pid)
            return self.proxRec(index, queryTerms, d, absol, out)


    def proximitySearch(self, query, distance=1, absol=True):
        print(f"\n\tRunning Proxmimity Search with query : {query} and allowed distance : {distance}.")
        try: index = self.indexes['pos']
        except: 
            self.errors['index'].append("Index Error : Positional index missing for proximitySearch")
            if not self.quiet: print(self.errors['index'][-1], "(try running : .loadIndexes(['pos']) )")
            return "ERROR"

        query = self.queryprocessing(query)
        query.reverse()
        return self.proxRec(index, query, distance, absol)


    # Boolean Search Functions ---------------------

    def getLocations(self, i, index, cmds):
        if cmds[i] != 'NOT':
            return set(self.proxRec(index, self.queryprocessing(cmds[i])[::-1], 1, False).keys())
        else:
            return set(self.proxRec(index, self.queryprocessing(cmds[i+1])[::-1], 1, False).keys()).symmetric_difference(set(self.tags.keys()))


    def booleanSearch(self, query):
        print(f'\n\tRunning Boolean Search with query : {query.strip()}.')
        try: index = self.indexes['pos']
        except: 
            self.errors['index'].append("Index Error : Positional index missing for booleanSearch")
            if not self.quiet: print(self.errors['index'][-1], "(try running : .loadIndexes(['pos']) )")
            return "ERROR"

        cmds = [x[1:-1] if x[0] == '"' else x for x in re.split("( |\\\".*?\\\"|'.*?')", query) if x != '' and x != ' ']

        output = self.getLocations(0, index, cmds)
        for i in range(len(cmds)):
            if cmds[i] == 'AND':
                output &= self.getLocations(i+1, index, cmds) # Updating Intesect
            if cmds[i] == 'OR':
                output |= self.getLocations(i+1, index, cmds) # Updating Union
        return output


class YieldSearch:
    pass

# Test Executions ----------------------------------

# print("Running...")

# start = time()
# classic = ClassicSearch(Path.cwd() / "python/data/wikidata_short.xml", rerun=False)
# print(f"\nResults : {classic.rankedIR('aggression violence')}")
# print(f"Classic Executed in {round(time()-start, 1)} secs\n")

# start = time()
# mongo = MongoSearch(Path.cwd() / "python/data/wikidata_short.xml", threads=6, rerun=True, debug=False, quiet=False)
# print(f"\nResults : {mongo.rankedIR('aggression violence')}")
# print(f"Mongo Executed in {round(time()-start, 1)} secs\n")

