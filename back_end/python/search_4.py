#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import math
from cmath import exp
from pathlib import Path
from collections import defaultdict
from python.index_wiki_dump import remove_stop_words, stem, tokenise

PATH_TO_IDX = sys.argv[1] if Path(sys.argv[1]).is_dir() else "./back_end/python/idx"
WORD_LIST = []
TITLE_LIST = []
TITLE_DICT = defaultdict(int)
OPT_DICT = defaultdict(int)
FIELD_WEIGHTS = {"t": 140, "i": 80, "c": 50, "e": 20}


def load_number_of_docs() -> int:
    global NUMBER_OF_DOCS

    with open(f"{PATH_TO_IDX}/doc_count.txt", "r", encoding="utf8")  as f:
        for line in f:
            NUMBER_OF_DOCS = int(line.strip())
            return NUMBER_OF_DOCS


NUMBER_OF_DOCS = load_number_of_docs()


def load_titles() -> None:
    global TITLE_LIST, TITLE_DICT

    with open(f"{PATH_TO_IDX}/title_offset", "r", encoding="utf8")  as f:
        for line in f:
            line = line.strip().split()
            k, v = int(line[0].strip()), int(line[1].strip())
            TITLE_DICT[k] = v
    TITLE_LIST = sorted(list(TITLE_DICT.keys()))


def load_offsetfile() -> None:
    global OPT_DICT, WORD_LIST

    with open(f"{PATH_TO_IDX}/offset", "r", encoding="utf8") as f:
        for line in f:
            k, v = line.strip().split(":")
            OPT_DICT[k] = v
    WORD_LIST = sorted(list(OPT_DICT.keys()))


def get_title_number_by(docid: int) -> int:
    global TITLE_DICT, TITLE_LIST
    high, low, pos = len(TITLE_LIST) - 1, 0, 0

    while low <= high:
        mid = int((high + low) / 2)
        if int(TITLE_LIST[mid]) == docid:
            return TITLE_DICT[docid]
        elif TITLE_LIST[mid] < docid:
            pos = mid  # ERROR?? moving this really messes with search
            low = mid + 1
        else:
            high = mid - 1
    return TITLE_DICT[TITLE_LIST[pos]]


def get_titles(file_number: int, docid: int) -> str:
    global TITLE_DICT
    with open(f"{PATH_TO_IDX}/title{file_number}", "r", encoding="utf8") as f:
        for line in f:
            line = line.split("-")
            if int(line[0]) == docid:
                return line[1].strip("\n")


def get_file_number_by(word: str) -> int:
    global OPT_DICT, WORD_LIST
    high, low, pos = len(WORD_LIST) - 1, 0, 0

    while low <= high:
        mid = int((high + low) / 2)
        if WORD_LIST[mid] == word:
            return OPT_DICT[word]
        elif WORD_LIST[mid] < word:
            low = mid + 1
        else:
            pos = mid  # ERROR?? moving this really messes with search
            high = mid - 1
    return OPT_DICT[WORD_LIST[pos]]


def create_dict(qdict: defaultdict[list], line: str, val: str) -> defaultdict[list]:
    line = stem(remove_stop_words(tokenise(line)))
    for l in line:
        qdict[l] += [val]
    return qdict


def get_word_from(word: str, file_number: str) -> str:
    found_list = []
    with open(f"{PATH_TO_IDX}/file{file_number}", "r", encoding="utf8")  as fp:
        for line in fp:
            line = line.strip().split("/")

            if line[0] == word:
                found_list = line[1]
                break
    return found_list


def get_field_query_dict(query_string: str) -> defaultdict[list]:
    t, r, b, i, c, e = [""] * 6
    ft, fb, fc, fe, fr, fi = [0] * 6
    val = len(query_string) - 1
    for first_letter, second_letter in zip(query_string, query_string[1:]):
        two_contig_letters = first_letter + second_letter
        if two_contig_letters == "i:":
            fi = 1
            continue
        elif two_contig_letters == "t:":
            ft = 1
            continue
        elif two_contig_letters == "b:":
            fb = 1
            continue
        elif two_contig_letters == "c:":
            fc = 1
            continue
        elif two_contig_letters == "e:":
            fe = 1
            continue
        elif two_contig_letters == "r:":
            fr = 1
            continue
        t += first_letter if ft == 1 else ""
        b += first_letter if fb == 1 else ""
        c += first_letter if fc == 1 else ""
        e += first_letter if fe == 1 else ""
        r += first_letter if fr == 1 else ""
        i += first_letter if fi == 1 else ""

    l = len(query_string) - 1
    f_list = [t, b, c, e, r, i]
    for fx_i, fx in enumerate((ft, fb, fc, fe, fr, fi)):
        if fx == 1:
            f_list[fx_i] += query_string[l]

    qdict = defaultdict(list)
    for field, field_letter in zip(f_list, ("t", "b", "c", "e", "r", "i")):
        qdict = create_dict(qdict, field, field_letter)
    return qdict


def rank_simple_query_results(posting_dict: defaultdict[str]) -> defaultdict[float]:
    global NUMBER_OF_DOCS
    ranked_list = defaultdict(float)

    for word in posting_dict.keys():
        postlist = posting_dict[word]

        if len(postlist):
            postlist = postlist.split(";")
            df = len(postlist)
            idf = math.log10(10 / df)

            for doc in postlist:
                doc = doc.split("-")
                line = doc[1].split(":")[0]
                frequency = int(line[1:])
                tf = math.log10(1 + frequency)
                doc_id = int(doc[0])
                ranked_list[doc_id] += tf * idf
    return ranked_list


def rank_field_query_results(
    posting_dict: defaultdict[str], query_dict: defaultdict[str]
) -> defaultdict[float]:
    global NUMBER_OF_DOCS, FIELD_WEIGHTS
    ranked_list = defaultdict(float)

    for word in posting_dict.keys():
        postlist = posting_dict[word]

        if len(postlist):
            postlist = postlist.split(";")
            df = len(postlist)
            idf = math.log10(NUMBER_OF_DOCS / df)

            for doc in postlist:
                doc = doc.split("-")
                doc_id = int(doc[0])
                line = doc[1].split(":")
                fields_to_match = query_dict[word]
                frequency = 0

                for l in line:
                    if l[0] == "b":
                        frequency += int(l[1:])

                for field in fields_to_match:
                    for l in line:
                        if field != "b" and field == l[0]:
                            frequency += int(l[1:]) * FIELD_WEIGHTS[l[0]]

                tf = math.log10(1 + frequency)
                ranked_list[doc_id] += tf * idf
    return ranked_list


def search(query: str, hits_wanted: int = 5) -> list:
    global TITLE_DICT
    # query = "t:" + query
    is_field_search = any(_ in query for _ in ("t:", "b:", "i:", "c:", "e:"))
    if is_field_search:
        # field search
        query_dict = get_field_query_dict(query)
        qwords = list(query_dict.keys())
    else:
        # classic search
        qwords = stem(remove_stop_words(tokenise(query)))
    posting_dict = defaultdict(list)
    hits = []

    for word in qwords:
        file_number = get_file_number_by(word)
        posting_dict[word] = get_word_from(word, file_number)
    ranked_docids = (
        rank_field_query_results(posting_dict, query_dict)
        if is_field_search
        else rank_simple_query_results(posting_dict)
    )

    if len(ranked_docids):
        sorted_ranked_docids = sorted(
            ranked_docids, key=ranked_docids.get, reverse=True
        )
        hit_counter, i = 0, 0

        while True:
            if i > len(sorted_ranked_docids) or hit_counter > hits_wanted or i > 1000:
                break
            try:
                file_number = get_title_number_by(sorted_ranked_docids[i])
                hit = get_titles(
                    file_number, sorted_ranked_docids[i]
                )  # very slightly broken
            except IndexError:
                break
            if hit is not None:
                hits += [
                    {
                        "title": hit,
                        "link": f"http://en.wikipedia.org/?curid={sorted_ranked_docids[i]}",
                        "description": "",
                    }
                ]
                hit_counter += 1
            i += 1
    else:
        print("No Matches Found")
    return hits


def main() -> None:
    pass


if __name__ == "__main__":
    main()
