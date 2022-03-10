#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import math
import heapq
import xml.sax
from pathlib import Path
from _io import TextIOWrapper
from nltk.stem.porter import *
from timeit import default_timer
from collections import defaultdict

SIZE = 5242880
FILE_NUMBER = 0
NUMBER_OF_DOCS = 0
BUFFER_SIZE = 20000
FILE_NUMBER_TITLE = 0
TITLE_OFFSET_FILE = None
WORDS = defaultdict(dict)
PTR_DICT = defaultdict(dict)
STOPWORDS = defaultdict(int)
WORD_DICT = defaultdict(dict)
TITLE_DICT = defaultdict(str)
PATH_TO_STOPWORDS = "./back_end/python/stop_words.txt"
PATH_TO_CORPUS = sys.argv[1] if Path(sys.argv[1]).is_file() else "./wiki-full.xml"
# PATH_TO_IDX = f"./idx_{PATH_TO_CORPUS.split('/')[-1].replace('.', '').replace('/', '').replace('xml', '')}"
PATH_TO_IDX = "./idx"
Path(PATH_TO_IDX).mkdir(parents=True, exist_ok=True)


print(f"Indexing {PATH_TO_CORPUS}...")


with open(PATH_TO_STOPWORDS, "r", encoding="utf8") as f:
    for line in f:
        line = line.strip(" ").strip("\n")
        STOPWORDS[line] = 1


def remove_stop_words(tokens: list) -> list:
    return [key for key in tokens if STOPWORDS[key] != 1]


def stem(tokens: list) -> list:
    stemmer = PorterStemmer()
    return [stemmer.stem(data) for data in tokens]


def tokenise(raw_string: str) -> list:
    return re.findall(r"[a-z]+", raw_string)


def write_file_to_idx(fname: str) -> None:
    global WORDS
    with open(f"{PATH_TO_IDX}/{fname}", "w+", encoding="utf8") as f:
        for wrd in sorted(WORDS.keys()):
            s = f"{wrd}/"
            wrd_k = WORDS[wrd]
            for k in sorted(wrd_k.keys()):
                s += f"{k}-f{sum(WORDS[wrd][k][i] for i in range(5))}:"
                for fld, i in zip("tbice", range(5)):
                    if WORDS[wrd][k][i] > 0:
                        s += f"{fld}{WORDS[wrd][k][i]}:"
                s = f"{s[:-1]};"
            f.write(f"{s[:-1]}\n")


def create_freq_dict(tokens: list) -> defaultdict[int]:
    tokens = stem(remove_stop_words(tokens))
    token_dict = defaultdict(int)
    for tok in tokens:
        token_dict[tok] += 1
    return token_dict


def create_title_dict(raw_string: str) -> defaultdict[int]:
    tokens = re.findall(r"\d+|[\w]+", raw_string.lower())
    return create_freq_dict(tokens)


def create_link_dict(raw_string: str) -> defaultdict[int]:
    links = []
    split_lines = raw_string.split("==external links==")
    if len(split_lines) >= 2:
        lines = split_lines[1].split("\n")
        for line in lines:
            if any(_ in line for _ in ("* [", "*[")):
                split_line = line.split(" ")
                word = [key for key in split_line if "http" not in split_line]
                word = " ".join(word).encode("utf-8")
                links += [word]
    links = tokenise(b" ".join(links).decode())
    return create_freq_dict(links)


def write_title_to_idx(fname: str) -> None:
    global TITLE_DICT, FILE_NUMBER_TITLE, TITLE_OFFSET_FILE
    with open(f"{PATH_TO_IDX}/{fname}", "w+", encoding="utf8") as f:
        li = sorted(TITLE_DICT.keys())
        TITLE_OFFSET_FILE.write(f"{str(li[0])} {str(FILE_NUMBER_TITLE)}\n")
        for doc_id in li:
            f.write(f"{str(doc_id)}-{str(TITLE_DICT[doc_id])}\n")


def create_text_dict(raw_string: str) -> defaultdict[int]:
    body_text, info_box, category = [], [], []
    raw_string = raw_string.lower()
    ext = create_link_dict(raw_string)
    txt = raw_string.replace("_", " ").replace(",", "").split("\n")
    length_txt = len(txt)
    line, count, is_body_finished = 0, 0, False
    while line < length_txt:
        if "{{infobox" in txt[line]:
            line_by_infobox = txt[line].split("{{infobox")
            count += line_by_infobox[1].count("{{") - line_by_infobox[1].count("}}") + 1
            info_box += [line_by_infobox[1]]
            body_text += [line_by_infobox[0]]
            line += 1
            while count >= 1 and line < length_txt:
                count += txt[line].count("{{") - txt[line].count("}}")
                info_box += [txt[line]]
                line += 1
        elif not is_body_finished:
            body_text += [txt[line]]
            if any(_ in txt[line] for _ in ("[[category", "==external links==")):
                is_body_finished = True
        else:
            if "[[category" in txt[line]:
                line_by_infobox = txt[line].replace("[[category:", "")
                category += [line_by_infobox]
        line += 1
    category = tokenise(" ".join(category))
    body_text = tokenise(" ".join(body_text))
    info_box = tokenise(" ".join(info_box))
    return (
        create_freq_dict(category),
        create_freq_dict(body_text),
        create_freq_dict(info_box),
        ext,
    )


def make_dict(line: str, heap: list, f: TextIOWrapper) -> bool:
    global WORD_DICT
    line = line.strip().split("/")
    is_first_line_in_word_dict = line[0] in WORD_DICT
    if not is_first_line_in_word_dict:
        heapq.heappush(heap, line[0])
        PTR_DICT[line[0]] = f
    for l in line[1].split(";"):
        a, b = l.split("-")
        WORD_DICT[line[0]][int(a)] = b
    return is_first_line_in_word_dict


def write_dict(word: str, f: TextIOWrapper) -> None:
    line = f"{word}/"
    for l in sorted(WORD_DICT[word]):
        line += f"{l}-{WORD_DICT[word][l]};"
    f.write(f"{line[:-1]}\n")


def merge_files():
    global PTR_DICT, SIZE, NUMBER_OF_DOCS
    count = 0
    f_file = open(f"{PATH_TO_IDX}/file" + str(count), "w+", encoding="utf8")
    f_offset = open(f"{PATH_TO_IDX}/offset", "w+", encoding="utf8")
    heap = []
    NUMBER_OF_DOCS = (
        max(
            max(
                map(int, filter(str.isdigit, [f[-1] for f in os.listdir(PATH_TO_IDX)]))
            ),
            NUMBER_OF_DOCS,
        )
        + 1
    )
    for n in range(NUMBER_OF_DOCS):
        try:
            f = open(f"{PATH_TO_IDX}/temp{n}", "r", encoding="utf-8", errors="ignore")
        except FileNotFoundError:
            break
        line = f.readline()
        while line != "" and make_dict(line, heap, f):
            line = f.readline()
    while len(heap) > 0:
        word = heapq.heappop(heap)
        f_ptr = PTR_DICT[word]
        write_dict(word, f_file)
        if f_file.tell() >= SIZE:
            f_file.close()
            f_offset.write(f"{word}:{count}\n")
            count += 1
            f_file = open(f"{PATH_TO_IDX}/file{count}", "w+", encoding="utf8")
        PTR_DICT.pop(word)
        WORD_DICT.pop(word)
        line = f_ptr.readline()
        while line != "" and make_dict(line, heap, f_ptr):
            line = f_ptr.readline()
    f_offset.write(f"{word}:{count}\n")
    f_offset.close()
    f_file.close()
    for ptr_dict in PTR_DICT:
        for word in ptr_dict:
            for f in ptr_dict[word]:
                f.close()
    for ptr_dict in WORD_DICT:
        for word in ptr_dict:
            for f in ptr_dict[word]:
                f.close()


class WikipediaDumpContentHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.id = 0
        self.text = 0
        self.page = 0
        self.title = 0
        self.count = 0
        self.count_title = 0
        self.bufid = ""
        self.cat_words = defaultdict(int)
        self.body_words = defaultdict(int)
        self.title_words = defaultdict(int)
        self.infobox_words = defaultdict(int)
        self.extLinks_words = defaultdict(int)

    def create_index(self) -> None:
        global WORDS, TITLE_DICT, FILE_NUMBER, FILE_NUMBER_TITLE
        title, cat, body, info, ext = (
            self.title_words,
            self.cat_words,
            self.body_words,
            self.infobox_words,
            self.extLinks_words,
        )
        all_words = set(title.keys())
        all_words = all_words.union(ext.keys())
        all_words = all_words.union(cat.keys())
        all_words = all_words.union(body.keys())
        all_words = all_words.union(info.keys())
        for i in all_words:
            WORDS[i][int(self.bufid)] = [title[i], body[i], info[i], cat[i], ext[i]]
        if self.count > BUFFER_SIZE:
            write_file_to_idx(f"temp{FILE_NUMBER}")
            self.count = 0
            FILE_NUMBER += 1
            WORDS = defaultdict(dict)
        if self.count_title > BUFFER_SIZE:
            write_file_to_idx(f"title{FILE_NUMBER_TITLE}")
            TITLE_DICT = defaultdict(str)
            FILE_NUMBER_TITLE += 1
            self.count_title = 0

    def startElement(self, tag, attr) -> None:
        global NUMBER_OF_DOCS
        if "id" in tag and not self.page:
            self.bufid = ""
            self.page = 1
            self.id = 1
            NUMBER_OF_DOCS += 1
        elif "title" in tag:
            self.title = 1
            self.buftitle = ""
        elif "text" in tag:
            self.text = 1
            self.buftext = ""

    def characters(self, data) -> None:
        if self.id == self.page == 1:
            self.bufid += data
            TITLE_DICT[int(self.bufid)] = self.buftitle
        elif self.title == 1:
            self.buftitle += data
        elif self.text == 1:
            self.buftext += data

    def endElement(self, tag) -> None:
        if "page" in tag:
            self.page = 0
            self.count += 1
            self.count_title += 1
        if "title" in tag:
            self.title = 0
            self.title_words = create_title_dict(self.buftitle)
        if "id" in tag:
            self.id = 0
        if "text" in tag:
            self.text = 0
            (
                self.cat_words,
                self.body_words,
                self.infobox_words,
                self.extLinks_words,
            ) = create_text_dict(self.buftext)
            WikipediaDumpContentHandler.create_index(self)


def main():
    global TITLE_OFFSET_FILE, PATH_TO_CORPUS
    TITLE_OFFSET_FILE = open(f"{PATH_TO_IDX}/title_offset", "w+", encoding="utf8")
    Parser = xml.sax.make_parser()
    Parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    Parser.setContentHandler(WikipediaDumpContentHandler())
    Parser.parse(PATH_TO_CORPUS)
    with open(f"{PATH_TO_IDX}/doc_count.txt", "w+", encoding="utf8") as f:
        f.write(str(NUMBER_OF_DOCS))
    write_file_to_idx(f"temp{FILE_NUMBER}")
    write_title_to_idx(f"title{FILE_NUMBER_TITLE}")
    TITLE_OFFSET_FILE.close()
    merge_files()


if __name__ == "__main__":
    start = default_timer()
    main()
    print(f"Time Taken To Index: {default_timer() - start:.3f} seconds")
