
## ==================================================
##
##   Simple Search Programs for Parent Class 
##
## ==================================================

# Imports ------------------------------------------

import os
import re
import json
import copy
import shutil
import pymongo
import math as m
import numpy as np
from time import time
from tqdm import tqdm
from pathlib import Path
from itertools import islice
from sklearn import preprocessing
from ssh_pymongo import MongoSession
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


    def proximitySearch(self, query, distance=0, absol=True):
        print(f"\n\tRunning Proxmimity Search with query : {query} and allowed distance : {distance}.")
        try: index = copy.deepcopy(self.indexes['pos'])
        except: 
            self.errors['index'].append("Index Error : Positional index missing for proximitySearch")
            if not self.quiet: print(self.errors['index'][-1], "(try running : .loadIndexes(['pos']) )")
            return "ERROR"

        query = self.queryprocessing(query)
        query.reverse()
        return self.proxRec(index, query, distance+len(query), absol)


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

    def __init__(self, path, rerun=False, quiet=True, threads=2, debug=False):
        self.datapath = Path(path)
        self.dataname = self.datapath.name.split('.')[0]
        self.rerun = rerun
        self.quiet = quiet
        self.errors = {"xml":{}, "index":[]}
        self.threads = threads                          # Multithreaded is only turned on if threads is raised higher than 1
        self.debug = debug

        # session = MongoSession('20.58.1.234', port=22, user='dan', password='FJackv8w0Lf6', uri=f'mongodb://localhost:27017/')
        # self.database = session.connection[self.dataname]

        self.client = pymongo.MongoClient(f"mongodb://localhost:27017/")
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
            data.append({"pid": int(re.split('<.?id>', page)[1]), "title": re.split('<.?title>', page)[1], "text": re.sub('&\w*;', '', re.split('<.?text[^>]*>', page)[1])})
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
            self.database['index'].insert_one({"term": term, "pid":page['pid'], "loc":i+1})


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
            print(term)
            for pid in docs(term):
                if pid not in docScores:
                    docScores[pid] = 0
                docScores[pid] += weight(term, pid)
                print('\t', pid)
        return docScores


    def proximitySearch(self, query, distance=0, absol=True, loud=True):
        if loud: print(f"\n\tRunning Proxmimity Search with query : {query} and allowed distance : {distance}.")
        self.database.temp.drop()
        out = None
        query = self.textprocessing(query, loud)
        d = distance+len(query)
        # query.reverse()

        for term in query:
            if out == None:
                out = self.database.temp
                out.insert_many(self.index.find({"term":term}))
            else:
                for line in out.find({}):
                    if self.index.count_documents({"$and": [{"term":term, "pid": line["pid"], "loc": {"$gte":line["loc"]-d}}, {"term":term, "pid": line["pid"], "loc": {"$lte":line["loc"]+d}}]}) == 0:
                        out.delete_one({"pid": line["pid"], "loc": line["loc"]})
                    elif not absol and self.index.count_documents({"$and": [{"term":term, "pid": line["pid"], "loc": {"$gte":line["loc"]}}, {"term":term, "pid": line["pid"], "loc": {"$lte":line["loc"]+d}}]}) == 0:
                        out.delete_one({"pid": line["pid"], "loc": line["loc"]})
        output = {}
        for line in out.find({}):
            if line["pid"] not in output:
                output[line["pid"]] = []
            output[line["pid"]].append(line["loc"])
        return output


    # Boolean Search Functions ---------------------

    def getLocations(self, i, cmds):
        if cmds[i] != 'NOT':
            return set(self.proximitySearch(cmds[i], 0, False, False).keys())
        else:
            return set(self.proximitySearch(cmds[i+1], 0, False, False).keys()).symmetric_difference(set(self.tags.keys()))


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


class YieldSearch:

    def __init__(self, datapath, indexpath, rerun=False, quiet=True, threads=25, debug=False):
        self.datapath = Path(datapath)
        self.indexpath = Path(indexpath)
        self.rerun = rerun
        self.quiet = quiet
        self.errors = {"xml":{}, "index":[]}
        self.threads = threads                          # Multithreaded is only turned on if threads is raised higher than 1
        self.debug = debug
        start = time()

        with open(Path.cwd() / "python" / "stopwords.txt") as f:
            self.stopwords = f.read().splitlines() 

        self.checkIndexes(2**13)
        if self.debug: print(f"Checked Index : {time()-start}s")

    
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

    def readPages(self):
        page = ""
        for row in open(self.datapath, 'r', encoding="utf8"):
            if "<page>" in row:
                page = row
            if "<page>" in page:
                page += row
            if "</page>" in row:
                yield page
                page = ""


    def preprocessing(self, block):
        extract = lambda page : {"pid": int(re.split('<.?id>', page)[1]), "title": re.split('<.?title>', page)[1], "terms": self.textprocessing(re.sub('&\w*;', '', re.split('<.?text[^>]*>', page)[1]))}
        def process(data):
            for page in data:
                doc = extract(page)
                with open(self.indexpath / "Terms" / f"{doc['pid']}.json", "w") as f:
                    f.write(json.dumps(doc))

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            pages = []
            for page in self.readPages():
                pages.append(page)
                if len(pages) >= block:
                    executor.submit(process, pages)
                    pages = []
        # by this point, len(pages) < block, and we need to give an equal number of pages to each thread!
        # executor = ThreadPoolExecutor(max_workers=self.threads)
        # executor.map(process, np.array_split(pages, self.threads))
        # executor.shutdown()
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            page_chunks = map(list, np.array_split(pages, self.threads))
            for page in page_chunks:
                    executor.submit(process, page)
                

    def textprocessing(self, text, printer=False):
        tokens = [word.strip() for word in re.split('[^a-zA-Z0-9]', text) if word != '' and word.lower() not in self.stopwords]
        terms  = [PorterStemmer().stem(word) for word in tokens]

        if printer: print(f"\t- Queryprocessing : {text} --> {terms}")
        return terms


# --------------------------------------------------
#   Indexing
# --------------------------------------------------

    def terms(self):
        for doc in os.listdir(self.indexpath / "Terms"):
            with open(self.indexpath / "Terms" / doc, "r") as f:
                yield json.loads(f.read())

    def checkIndexes(self, block):
        print("Checking index:") if self.threads == 1 else print(f"Checking index using {self.threads} threads:")
        if not os.path.isdir(self.indexpath / "Terms") or self.rerun:
            print(f"\t- Preprocessing data in size {block} blocks...")
            if self.rerun and os.path.isdir(self.indexpath / "Terms"): shutil.rmtree(self.indexpath / "Terms", ignore_errors=True)
            os.mkdir(self.indexpath / "Terms")
            start = time()
            self.preprocessing(block)
            if self.debug: print(f"Preprocessed : {time()-start}s")

        if not os.path.isdir(self.indexpath / "Index") or self.rerun:
            print(f"\t- Indexing data with {self.threads} threads...")
            if self.rerun and os.path.isdir(self.indexpath / "Index"): shutil.rmtree(self.indexpath / "Index", ignore_errors=True)
            os.mkdir(self.indexpath / "Index")
            start = time()
            # with ThreadPoolExecutor(max_workers=self.threads) as executor:
            docs = []
            for doc in tqdm(self.terms()):
                docs.append(doc)
                if len(docs) >= block:
                    self.indexer(docs)
                    # executor.submit(self.indexer, docs)
                    docs = []
            self.indexer(docs)
            # by this point, len(docs) < block, and we need to give an equal number of docs to each thread!
            # ThreadPoolExecutor(max_workers=self.threads)
            # executor.map(self.indexer, np.array_split(docs, self.threads))
            # executor.shutdown()
            # with ThreadPoolExecutor(max_workers=self.threads) as executor:
            #     doc_chunks = map(list, np.array_split(docs, self.threads))
            #     for doc in doc_chunks:
            #         executor.submit(self.indexer, docs)

            if self.debug: print(f"Indexed : {time()-start}s")


    def indexer(self, docs):
        index = {}
        for doc in docs:
            for i in range(len(doc['terms'])):
                term = doc['terms'][i]
                if not os.path.isdir(self.indexpath / "Index" / term):
                    os.mkdir(self.indexpath / "Index" / term)
                if not os.path.isdir(self.indexpath / "Index" / term / str(doc['pid'])):
                    os.mkdir(self.indexpath / "Index" / term / str(doc['pid']))
                os.mkdir(self.indexpath / "Index" / term / str(doc['pid']) / str(i))
        

# --------------------------------------------------
#   Translator
# --------------------------------------------------

    def indexes(term=None, pid=None):
        terms_pth = self.indexpath / "Index" / term #back_end\index\Index\0 (term)\1000 (doc)\5000 (loc)
        idx_term = os.listdir(terms_pth)
        if not pid: 
            return idx_term

        idx_term_pids = []
        for idx_term_pid in idx_term:
            idx_term_pid += json.loads(self.indexpath / "Term" / f"{idx_term_pid}.json")["terms"]
        return idx_term_pid

# --------------------------------------------------
#   Query Exectution
# --------------------------------------------------

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
        # tf_os = lambda term : len(indexes(term, pid))
        # df_os = lambda term : len(indexes(term))

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


    def proximitySearch(self, query, distance=0, absol=True):
        print(f"\n\tRunning Proxmimity Search with query : {query} and allowed distance : {distance}.")
        try: index = copy.deepcopy(self.indexes['pos'])
        except: 
            self.errors['index'].append("Index Error : Positional index missing for proximitySearch")
            if not self.quiet: print(self.errors['index'][-1], "(try running : .loadIndexes(['pos']) )")
            return "ERROR"

        query = self.queryprocessing(query)
        query.reverse()
        return self.proxRec(index, query, distance+len(query), absol)


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


class IRSearch():

    def __init__(self, datapath, indexpath, rerun=False, threads=4, debug=False):
        self.datapath = Path(datapath)
        self.indexpath = Path(indexpath)
        self.threads = threads
        self.rerun = rerun
        self.debug = debug

        self.N = 0
        for i in self.readPages():
            self.N += 1
        
        if rerun:
            print("Deleting Old Data", end="...  ")
            shutil.rmtree(self.indexpath, True)
            os.mkdir(self.indexpath)
            print("Deleted")

            with open(Path.cwd() / "python" / "stopwords.txt") as f:
                self.stopwords = f.read().splitlines() 
            
            self.createIndex()

    def readPages(self):
        page = ""
        for row in open(self.datapath, 'r', encoding="utf8"):
            if "<page>" in row:
                page = row
            if "<page>" in page:
                page += row
            if "</page>" in row:
                yield page
                page = ""


    def textprocessing(self, text, printer=False):
        tokens = [word.strip() for word in re.split('[^a-zA-Z0-9]', text) if word != '' and word.lower() not in self.stopwords]
        terms  = [PorterStemmer().stem(word) for word in tokens]

        if printer: print(f"\t- Queryprocessing : {text} --> {terms}")
        return terms


    def createIndex(self):
        extract = lambda page : {'pid': int(re.split('<.?id>', page)[1]),  'terms': self.textprocessing(re.sub('&\w*;', '', re.split('<.?text[^>]*>', page)[1]))}
        
        def indexpage(page):
            termerised = extract(page)
            for term in tqdm(termerised['terms'], leave=False):
                if os.path.isfile(self.indexpath / term):
                    with open(self.indexpath / term, 'r') as f:
                        text = f.read().split(',')
                else:
                    text = ['0']
                with open(self.indexpath / term, 'w') as f:
                    notfound = True
                    for i in range(len(text)):
                        if ':' in text[i]:
                            pid, num = text[i].split(':')
                            if int(pid) == termerised['pid']:
                                text[i] = f"{pid}:{int(num)+1}"
                                notfound = False
                    if notfound:
                        text[0] = str(int(text[0])+1)
                        text.append(f"{termerised['pid']}:1")
                    f.write(','.join(text))
       
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for page in self.readPages():
                executor.submit(indexpage, page)


    def rankedIR(self, query):
        print(f'\tRunning Ranked IR with query : {query}.')

        weight = lambda tf, df : (1 + m.log10(tf)) * m.log10(self.N / df)

        queryTerms = self.textprocessing(query, True)
        docScores = {}

        for term in queryTerms:
            if not os.path.isfile(self.indexpath / term): continue
            with open(self.indexpath / term) as f:
                info = f.read().split(',')
                for page in info[1:]:
                    pid, num = page.split(':')
                    if pid not in docScores:
                        docScores[pid] = 0
                    docScores[pid] += weight(int(num), int(info[0]))
                
        return docScores

# Test Executions ----------------------------------

Question = "Economic Systems "
d = 10

# print("Running...")
# start = time()
# classic = ClassicSearch(Path.cwd() / "python/data/wikidata_short.xml", rerun=False)
# print(f"\nResults : {classic.booleanSearch(Question)}")
# print(f"Classic Executed in {round(time()-start, 1)} secs\n")

# start = time()
# mongo = MongoSearch(Path.cwd() / "python/data/wikidata_short.xml", threads=6, rerun=True, debug=False, quiet=False)
# print(f"\nResults : {mongo.booleanSearch(Question)}")
# print(f"Mongo Executed in {round(time()-start, 1)} secs\n")

# start = time()
# yields = YieldSearch(
#     Path.cwd() / "back_end/python/data/wikidata_notsoshort.xml", 
#     Path.cwd() / "back_end/index", 
#     rerun=True,
#     debug=True, 
#     threads=os.cpu_count()*5,
#     )
# # yields = YieldSearch(Path.cwd() / "back_end/python/data/all_wiki.xml", Path.cwd() / "back_end/index", rerun=True, debug=True)
# print(f"\nResults : {yields.booleanSearch(Question)}")
# print(f"Yield Executed in {round(time()-start, 1)} secs\n")


start = time()
irs = IRSearch(
    Path.cwd() / "back_end/python/data/wikidata_short.xml", 
    Path.cwd() / "back_end/indexv2", 
    rerun=True,
    threads=os.cpu_count()*5
    )
print(f"\nResults : {irs.rankedIR(Question)}")
print(f"IR Search Executed in {round(time()-start, 1)} secs\n")

