#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import python.search_4 as search_py
from .models import Search

# from python.SimpleSearch import ClassicSearch, IRSearch
from rest_framework import viewsets
from django.http import JsonResponse
from .serializers import SearchSerializer
from django.utils.datastructures import MultiValueDictKeyError


search_py.load_offsetfile()
search_py.load_titles()

# classic = ClassicSearch("/home/dan/TTDS-G35-CW3/back_end/index/positionalIndex/Short")
# ranked  = IRSearch("/home/dan/TTDS-G35-CW3/back_end/index/rankedIndex/Short")


def query_hugging_face(payload, question):
    if question:
        # API_URL = "https://api-inference.huggingface.co/models/EleutherAI/gpt-j-6B"
        API_URL = (
            "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"
        )
    else:
        API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    API_TOKEN = "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"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


class SearchView(viewsets.ModelViewSet):
    serializer_class = SearchSerializer
    queryset = Search.objects.all()


def search(request):
    data = []
    if request.method == "GET":
        number_hits_wanted = request.GET["hitcount"]
        search_term = request.GET["query"]
        print(f"query = {search_term}")
        choice = request.GET["choice"]

        # if choice == "ranked":
        #     hits = classic.rankedIR(search_term)
        #     data = [{"title":classic.pids[k], "link":f"http://en.wikipedia.org/?curid={k}", "description":""} for k,s in sorted(hits.items(), key=lambda i: i[1])[:number_hits_wanted]]
        # elif choice == "rankedbeta":
        #     data = ranked.rankedIR(search_term)
        #     data = [{"title":classic.pids[h], "link":f"http://en.wikipedia.org/?curid={h}", "description":""} for h in sorted(hits.items(), key=lambda i: i[1])[:number_hits_wanted]]
        # elif choice == "boolean":
        #     data = classic.booleanSearch(search_term)
        # elif choice == "question":
        #     pass
        # elif choice == "vector":
        #     pass
        # else:
        #     data = classic.rankedIR(search_term)

        data = search_py.search(
            query="t:" + search_term.lower(), hits_wanted=int(number_hits_wanted)
        )
        text_to_summarise = []

        for i, d in enumerate(data):
            title = d["title"]
            API_URL = (
                "https://en.wikipedia.org/w/api.php?format=json&origin=*&action=query&prop=extracts&explaintext=1&exintro&titles="
                + title.replace(" ", "%20")
            )
            try:
                response = requests.get(API_URL).json()["query"]["pages"]
                pid = list(response.keys())[0]
                raw_desc = response[pid]["extract"]
                text_to_summarise += [(data[i]["title"], raw_desc)]
                desc_len = 100
                desc_split = raw_desc.split(" ")
                desc = (
                    " ".join(desc_split[:desc_len])
                    if len(desc_split) > desc_len
                    else raw_desc
                )
                data[i]["description"] = desc

            except KeyError:
                text_to_summarise += [(data[i]["title"], "")]
                pass

        ans = ""
        try:  # QUESTION ANSWERING / SUMMARY
            _ = request.GET["question"]

            # if q: is prefix or ? us last char, then it's a question
            is_question = (
                "q:" in search_term[:2].lower() or "?" in search_term[-1]
            ) and len(data) > 0
            if is_question:
                query = search_term
                query = query.replace("q:", "").replace("Q:", "").replace("t:", "")
                query = query + "?" if query[-1] != "?" else query
                context = ""
                abstract = ""

                # 512 words from top 3 hits as context
                for _, desc_to_summarise in text_to_summarise[:3]:
                    if len(desc_to_summarise):
                        abstract += " ".join(desc_to_summarise.split(" ")[:250])
                print(abstract + "\n\n")
                if len(abstract):
                    prepro = query_hugging_face(
                        payload={
                            "inputs": " ".join(abstract.split(" ")),
                            "parameters": {"do_sample": False, "min_length": 200},
                        },
                        question=False,
                    )
                    context += prepro[0]["summary_text"]
                print(context)
                if len(context):
                    prompt = f"Q: {query}\nA:" ""
                    output = query_hugging_face(
                        payload={"question": prompt, "context": context,},
                        question=True,
                    )
                    try:
                        score = output["score"]
                        ans = (
                            "Wikibot is {:.2f}% sure of the answer \n".format(score)
                            + prompt
                            + " "
                            + output["answer"]
                        )
                        # ans = ans[len(prompt):]#.split("\n")[0]
                        print(ans)
                    except KeyError:
                        ans = "Sorry, I don't know the answer to that question"
                else:
                    ans = "Sorry, I don't know the answer to that question"
            # ans = ans[len(prompt) :]
            # ans = re.search("\nA:(.*)\n|Q:|A:", ans).group(1)
            elif len(text_to_summarise[0][1]):
                output = query_hugging_face(
                    payload={
                        "inputs": " ".join(text_to_summarise[0][1].split(" ")[:512]),
                    },
                    question=False,
                )
                print(output[0]["summary_text"])
                ans = "Summary of Top Hit: " + output[0]["summary_text"]
            else:
                pass
        except MultiValueDictKeyError:
            pass
        data = [{"title": ans, "description": ans}] + data

    return JsonResponse({"0": data}, safe=True, content_type="application/json")

