
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
from time import time
from tqdm import tqdm
from pathlib import Path
from nltk.stem.porter import PorterStemmer
from concurrent.futures import ProcessPoolExecutor



class ClassicSearch:

    def __init__(self, indexpath, quiet=True, threads=1, debug=False):
        self.indexpath = Path(indexpath)
        self.quiet = quiet
        self.errors = {"xml":{}, "index":[]}
        self.threads = threads                          # Multithreaded is only turned on if threads is raised higher than 1
        self.debug = debug
        with open("/home/dan/TTDS-G35-CW3/back_end/python/stopwords.txt") as f:
            self.stopwords = f.read().splitlines() 

        with open(self.indexpath / "pids.txt", 'r') as f:
            self.pids = {}
            for t in f.read().split('\n'):
                if t == "": break
                pid, title = t.split('>')
                self.pids[pid] = title



    def getErrors(self):
        for i, m in self.xmlerrors.items():
            print(f"XML Error : ID {i} Missing Tags -> {m}")


# --------------------------------------------------
#   Preprocessing
# --------------------------------------------------

    def textprocessing(self, text, printer=False):
        tokens = [word.strip() for word in re.split('[^a-zA-Z0-9]', text) if word != '' and word.lower() not in self.stopwords]
        terms  = [PorterStemmer().stem(word) for word in tokens]

        if printer: print(f"\t- Queryprocessing : {text} --> {terms}")
        return terms


# --------------------------------------------------
#   Indexing
# --------------------------------------------------

    def indexPage(self, page):
        if page['pid'] not in self.pids:
            self.pids[page['pid']] = page['title'].strip()
            with open(self.indexpath / "pids.txt", 'a') as f:
                f.write(f"{page['pid']}>{page['title'].strip()}\n")

        for i, term in enumerate(self.textprocessing(page['text'])):
            store = term[:3]
            if os.path.isfile(self.indexpath / store):
                with open(self.indexpath / store, 'r') as f:
                    data = json.loads(f.read())
            else:
                data = {}
            with open(self.indexpath / store, 'w') as f:
                if term not in data:
                    data[term] = {}
                if page["pid"] not in data[term]:
                    data[term][page["pid"]] = []
                data[term][page["pid"]].append(i+1)
                f.write(json.dumps(data))


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

    def __init__(self, indexpath, debug=False):
        self.indexpath = Path(indexpath)
        self.debug = debug

        with open(self.indexpath / "pids.txt", 'r') as f:
            self.pids = {}
            for t in f.read().split('\n'):
                if t == "": break
                pid, title = t.split('>')
                self.pids[pid] = title
        
        with open("/home/dan/TTDS-G35-CW3/back_end/python/stopwords.txt") as f:
            self.stopwords = f.read().splitlines() 


    def textprocessing(self, text, printer=False):
        tokens = [word.strip() for word in re.split('[^a-zA-Z0-9]', text) if word != '' and word.lower() not in self.stopwords]
        terms  = [PorterStemmer().stem(word) for word in tokens]

        if printer: print(f"\t- Queryprocessing : {text} --> {terms}")
        return terms


    def indexPage(self, page):
        if page['pid'] not in self.pids:
            self.pids[page['pid']] = page['title'].strip()
            with open(self.indexpath / "pids.txt", 'a') as f:
                f.write(f"{page['pid']}>{page['title'].strip()}\n")

        for term in self.textprocessing(page['text']):
            if os.path.isfile(self.indexpath / term):
                with open(self.indexpath / term, 'r') as f:
                    text = f.read().split('\n')
            else:
                text = ['0']
            with open(self.indexpath / term, 'w') as f:
                notfound = True
                for i in range(len(text)):
                    if ':' in text[i]:
                        pid, num = text[i].split(':')
                        if pid == page['pid']:
                            text[i] = f"{pid}:{int(num)+1}"
                            notfound = False
                if notfound:
                    text[0] = str(int(text[0])+1)
                    text.append(f"{page['pid']}:1")
                f.write('\n'.join(text))


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



class wikiHandler(xml.sax.ContentHandler):

    def __init__(self, searchClass):
        self.tag = ""
        self.pid = None
        self.title = ""
        self.text = ""
        self.searcher = searchClass
        self.executor = ProcessPoolExecutor(max_workers=1)
        self.progress = tqdm(total=20)

    def ended(self):
        self.progress.close()
        self.executor.shutdown()

    def startElement(self, tag, argument):
        self.tag = tag

    def characters(self, content):
        if self.tag == "id" and not content.isspace() and self.pid == None:
            self.pid = content
        if self.tag == "title":
            self.title += content
        if self.tag == "text":
            self.text += content

    def endElement(self, tag):
        self.progress.update(1)
        if tag == "page":
            self.executor.submit(self.searcher.indexPage, {"pid":self.pid, "title":self.title, "text":self.text})
            self.pid = None
            self.title = ""
            self.text = ""



# Test Executions ----------------------------------


print("Running...")
start = time()

classic = ClassicSearch(
    Path.cwd() / "TTDS-G35-CW3/back_end/index/positionalIndex", 
    )
ranked = IRSearch(
    Path.cwd() / "TTDS-G35-CW3/back_end/index/rankedIndex/Short", 
    )

parser = xml.sax.make_parser()  
parser.setFeature(xml.sax.handler.feature_namespaces, 0)
handler = wikiHandler(ranked)
parser.setContentHandler(handler)

parser.parse("/home/dan/TTDS-G35-CW3/back_end/python/data/wikidata_short.xml")

Question = "apple"

print(f"\nResults : {classic.booleanSearch(Question)}")
print(f"\nResults : {ranked.rankedIR(Question)}")
print(f"IR Search Executed in {round(time()-start, 1)} secs\n")
# handler.ended()
