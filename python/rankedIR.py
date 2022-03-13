import re
import os
import shutil
import math as m
from tqdm import tqdm
from time import time
from pathlib import Path
from nltk.stem.porter import PorterStemmer


class RankedIR():

    def __init__(self) -> None:
        self.datapath =  Path.cwd() / "back_end/python/data/wikidata_short.xml"
        self.indexpath = Path.cwd() / "back_end/indexv2"
        self.N = 0
        for i in self.readPages():
            self.N += 1
        # print("Deleting Old Data", end="...  ")
        # shutil.rmtree(self.indexpath, True)
        # os.mkdir(self.indexpath)
        # print("Deleted")

        with open(Path.cwd() / "python" / "stopwords.txt") as f:
            self.stopwords = f.read().splitlines() 

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
        for page in self.readPages():
            termerised = extract(page)
            for term in tqdm(termerised['terms']):
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

print("Running...")
start = time()
rir = RankedIR()
print(f"\nResults : {rir.rankedIR('wave walker')}")
print(f"Classic Executed in {round(time()-start, 1)} secs\n")
