
## ==================================================
##
##   Wiki Indexer for SimpleSearch 
##
## ==================================================

# Imports ------------------------------------------

import os
import re
import sys
import xml
import json
import numpy as np
from time import time
from tqdm import tqdm
from pathlib import Path
from nltk.stem.porter import PorterStemmer



class wikiHandler(xml.sax.ContentHandler):

    def __init__(self, method, indexpath, stoppath):
        self.tag = ""
        self.pid = None
        self.title = ""
        self.text = ""
        self.method = method
        self.indexpath = indexpath
        self.batch = {}
        self.pids = {}
        self.start = time()
        # self.timings = {"A":[], "B":[], "C":[], }
        self.progress = tqdm(total=7e7, leave=False)

        with open(stoppath, 'r') as f:
            self.stopwords = f.read().splitlines() 
        open(self.indexpath / "_pids.json", "w").close()


    def textprocessing(self, text, printer=False):
        tokens = [word.strip() for word in re.split('[^a-zA-Z0-9]', text) if word != '' and word.lower() not in self.stopwords]
        terms  = [PorterStemmer().stem(word) for word in tokens]

        if printer: print(f"\t- Queryprocessing : {text} --> {terms}")
        return terms

        
    def storeBatch(self):
        print(f"Batch Created {self.pid}")
        with open(self.indexpath / f"{self.pid}.json", "w") as f:
            f.write(json.dumps(self.batch))
        with open(self.indexpath / "_pids.json", "w") as f:
            f.write(json.dumps(self.pids))
        self.batch = {}


    def classicIndex(self, page):
        # start = time()
        if page['pid'] not in self.pids:
            self.pids[page['pid']] = page['title'].strip()

            for i, term in enumerate(self.textprocessing(page['text'])):
                if term not in self.batch:
                    self.batch[term] = {}
                if page["pid"] not in self.batch[term]:
                    self.batch[term][page["pid"]] = []
                self.batch[term][page["pid"]].append(i+1)

        if time() - self.start > 120:
            self.storeBatch()
            self.start = time()
        self.progress.update(1)


    def rankedIndex(self, page):
        if page['pid'] not in self.pids:
            self.pids[page['pid']] = page['title'].strip()
            with open(self.indexpath / "_pids.txt", 'a') as f:
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
        self.progress.update(1)


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
        if tag == "page":
            if self.method == "classic":
                wikiHandler.classicIndex(self, {"pid":self.pid, "title":self.title, "text":self.text})
            else:
                wikiHandler.rankedIndex(self, {"pid":self.pid, "title":self.title, "text":self.text})
            self.pid = None
            self.title = ""
            self.text = ""



# Test Executions ----------------------------------


print("Running...")
start = time()

parser = xml.sax.make_parser()
parser.setFeature(xml.sax.handler.feature_namespaces, 0)
handler = wikiHandler("classic", Path(r"D:\Index"), Path(r"D:\TTDS-G35-CW3\back_end\python\stopwords.txt"))
# handler = wikiHandler("ranked", Path.cwd() / "TTDS-G35-CW3/back_end/index/rankedIndex/Index")
parser.setContentHandler(handler)

parser.parse(Path(r"D:\enwiki-20220301-pages-articles-multistream.xml"))
handler.storeBatch()
print(f"Indexing Executed in {round(time()-start, 1)} secs\n")
# handler.ended()
