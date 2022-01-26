# Imports ------------------------------------------

import os
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import re
import math as m
from time import time
from nltk.stem.porter import PorterStemmer



# General Functions --------------------------------

codepath = Path.cwd()

def saveIndex(path, method='freq'):
    print(f'\t\tSaving new index file.')
    tags, index = indexing(path, method)
    if not os.path.isfile(codepath / "data" / f"tags.{path[:-4]}.json"):
        with open(codepath / "data" / f"tags.{path[:-4]}.json", 'w') as t:
            t.write(json.dumps(tags))
    with open(codepath / "data" / f"{method}.{path[:-4]}.json", 'w') as f:    
        #f.write(str(indexing(path, method)))
        f.write(json.dumps(index))

def retrieveIndex(path, method='freq'):
    print(f'\t\tRetrieving index file.')
    with open(codepath / "data" / f"{method}.{path[:-4]}.json", 'r') as f:
        #return eval(f.read())
        index = json.loads(f.read())
    with open(codepath / "data" / f"tags.{path[:-4]}.json", 'r') as f:
        tags = json.loads(f.read())
    return tags, index

def dictPrinter(dictionary):
    for key in dictionary:
        print(f" {key}  :   {dictionary[key]}")


# --------------------------------------------------
#   Lab 1 : Preprocessing
# --------------------------------------------------

def preprocessing(path):

    # Read Data ------------------------------------

    tags = {}
    data = {}
    if type(path) == str:
        if path[-3:] == 'xml':
            tree = ET.parse(codepath / 'data_collection' / path)
            root = tree.getroot()
            for doc in root:
                tags[doc.find('game_id').text] = {"name":doc.find('game_name').text, "developer":doc.find('developer').text}
                data[doc.find('game_id').text] = (f"{doc.find('description').text}")
        else:
            raise Exception("Incorrect file type in path (must be XML)")
    elif type(path) == dict:
        data = dict(path)
    else:
        for i in range(len(path)):
            data[i+1] = path[i]

    with open(codepath / 'source' / "stopwords.txt") as f:
        stopwords = f.read().splitlines() 

    # Tokenisation ---------------------------------|

    tokens = {}
    for docno in data:
        tokens[docno] = ([x.strip() for x in re.split('[^a-zA-Z0-9]', data[docno]) if x != '' and x.lower() not in stopwords])
        
    terms = {key:[PorterStemmer().stem(x) for x in vals] for (key,vals) in tokens.items()}

    return tags, terms


# --------------------------------------------------
#   Lab 2 : Indexing and Query Exectution
# --------------------------------------------------

# Index Matrix -------------------------------------

def getIndex(path, method=''):
    print(f'\nGetting Index from {path} using method : {method}.')
    if not os.path.isfile(codepath / "data" / f"{method}.{path[:-4]}.json"):
        saveIndex(path, method)
    return retrieveIndex(path, method)

def indexing(path, method):
    tags, terms = preprocessing(path)
    index = {}

    for line in terms:
        if method == 'pos':
            for i in range(len(terms[line])):
                term = terms[line][i]
                if term not in index:
                    index[term] = {}
                if line in index[term]:
                    index[term][line].append(i+1)
                else:
                    index[term][line] = [i+1]
        elif method == 'seq':
            index[line] = [f"{terms[line][i-1]}_{terms[line][i]}" for i in range(len(terms[line])) if i > 0]
        else:
            for term in terms[line]:
                if term not in index:
                    index[term] = {}
                if method == 'bool':
                    index[term][line] = 1 # Slightly redundant
                else:
                    if line not in index[term]:
                        index[term][line] = 0
                    index[term][line] += 1
    
    return tags, index


# Querying -----------------------------------------

def phraseSearch(path, query):
    if type(path) == dict:
        index = path
    else:
        __, index = getIndex(path, 'seq')
    print(f'\n\tRunning Phrase Search with query : {query}.')
    seqQuery = f"{preprocessing([query])[1][0]}_{preprocessing([query])[1][1]}"
    
    out = {}
    for line in index:
        for pos in range(len(index[line])):
            if index[line][pos] == seqQuery:
                if line not in out:
                    out[line] = []
                out[line].append(pos+1)
    return out

def proxRec(index, queryTerms, d, absol, out=None):
    if queryTerms == []:
        return out
    else:
        key = queryTerms.pop()
        if out == None:
            return proxRec(index, queryTerms, d, absol, index[key])
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
        return proxRec(index, queryTerms, d, absol, out)

def proximitySearch(path, query, distance=1, absol=True):
    if type(path) == dict:
        index = path
    else:
        __, index = getIndex(path, 'pos')
    print(f'\n\tRunning Proxmimity Search with query : {query} and allowed distance : {distance}.')

    if type(query) == str:
        queryTerms = preprocessing([query])[1]
    else:
        queryTerms = query
    queryTerms.reverse()
    return proxRec(index, queryTerms, distance, absol)

def getLocations(i, cmds, posIndex, docs):
    if cmds[i] != 'NOT':
        return set(proximitySearch(posIndex, cmds[i], absol=False).keys())
    else:
        return set(proximitySearch(posIndex, cmds[i+1], absol=False).keys()).symmetric_difference(set(docs))

def booleanSearch(path, query):
    tags, posIndex = getIndex(path, 'pos')

    print(f'\n\tRunning Boolean Search with query : {query.strip()}.')

    cmds = [x[1:-1] if x[0] == '"' else x for x in re.split("( |\\\".*?\\\"|'.*?')", query) if x != '' and x != ' ']

    output = getLocations(0, cmds, posIndex, tags.keys())
    for i in range(len(cmds)):
        if cmds[i] == 'AND':
            output &= getLocations(i+1, cmds, posIndex, tags.keys()) # Updating Intesect
        if cmds[i] == 'OR':    
            output |= getLocations(i+1, cmds, posIndex, tags.keys()) # Updating Union
    return output


# --------------------------------------------------
#   Lab 3 : Ranked Information Retrieval
# --------------------------------------------------

def rankedIR(path, query):
    tags, index = getIndex(path, 'pos')
    print(f'\tRunning Ranked IR with query : {query}.\n')
    N = len(tags.keys())

    tf = lambda term, line : len(index[term][line]) 
    df = lambda term : len(index[term])
    weight = lambda term, line : (1 + m.log10(tf(term, line))) * m.log10(N / df(term))

    queryTerms = preprocessing([query])[1]
    docScores = {}

    for term in queryTerms:
        for line in index[term]:
            if line not in docScores:
                docScores[line] = 0
            docScores[line] += weight(term, line)
            
    return docScores


# --------------------------------------------------
#   Coursework : File Output
# --------------------------------------------------

def indexOutput():
    with open(codepath / "coursework" / "index.txt", 'w') as f:    
        __, index = getIndex('trec.5000.xml', 'pos')
        output = ''
        for term in index:
            output += f'{term}:{len(index[term])}\n'
            for line in index[term]:
                output += f'\t{line}: {str(index[term][line])[1:-1]}\n'
        f.write(output)

def resultsOutput(method):
    with open(codepath / "coursework" / f"results.{method}.txt", 'w') as f:    
        with open(codepath / "data" / f"queries.{method}.txt", 'r') as queries:
            results = []    
            for query in queries.readlines():
                query = re.sub('^.*? ', '', query)
                if method == 'ranked':
                    results.append(rankedIR("trec.5000.xml", query))
                elif query[0] == '#':
                    dist, text = query.split('(')
                    results.append([int(x) for x in proximitySearch("trec.5000.xml", text[:-2].replace(",", " "), int(dist[1:])).keys()])
                else:
                    results.append(booleanSearch("trec.5000.xml", query))

            output = ''
            for i in range(len(results)):
                if method == 'ranked': # Order the results
                    count = 0
                    for val in {k:v for k, v in sorted(results[i].items(), key=lambda item: item[1], reverse=True)[:150]}:
                        #count += 1
                        #if count <= 150:
                        output += f'{i+1},{val},{round(results[i][val], 4)}\n'
                else:
                    for val in sorted(results[i], key=float):
                        output += f'{i+1},{val}\n'
            f.write(output)


# Executions ---------------------------------------

print("Running...")
start = time()

a,b,c = getIndex("test.xml", 'pos')
print(f"\n\n{a}\n\n\n{b}\n\n\n{c}")

print(f"\nExecuted in {time()-start} secs")
