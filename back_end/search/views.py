#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
from .models import Search
import python.search_4 as search_py
from rest_framework import viewsets
from django.http import JsonResponse
from .serializers import SearchSerializer


search_py.load_offsetfile()
search_py.load_titles()


def query_hugging_face(payload, question):
    if question:
        API_URL = "https://api-inference.huggingface.co/models/EleutherAI/gpt-j-6B"
    else:
        API_URL = "https://api-inference.huggingface.co/models/google/pegasus-xsum"
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
        number_hits_wanted = request.GET["hitcount"] # number of hits we want to retrieve
        print(number_hits_wanted)
        search_term = request.GET["query"] # raw text
        print(f"query = {search_term}")
        query = search_term.lower() # raw text but lowercase
        text_to_summarise = ""
        data = search_py.search(query)
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
                text_to_summarise = raw_desc if not i else text_to_summarise
                word_len = 100
                desc_split = raw_desc.split(" ")
                desc = (
                    " ".join(desc_split[:word_len])
                    if len(desc_split) > word_len
                    else raw_desc
                )
                data[i]["description"] = desc

            except KeyError:
                pass

        # if q: is prefix or ? us last char, then it's a question
        ans = ""
        # is_question = ("q:" in query[:2].lower() or search_term[-1] == "?") and len(data) > 0
        # if is_question:
        #     query = search_term[2:] + "?" if search_term[-1] != "?" else search_term[2:]
        #     query = query.replace("q:", "").replace(":", "")
        #     prompt = f"I am a highly intelligent question answering bot. If you ask me a question that is rooted in truth, I will give you the answer. If you ask me a question that is nonsense, trickery, or has no clear answer, I will respond with 'Not sure'.\n\nQ: {query}\nA:"
        #     output = query_hugging_face(
        #         {
        #             "inputs": prompt,
        #         },
        #         question=True,
        #     )
        #     ans = output[0]["generated_text"]
            # ans = ans[ans.index(prompt[-5:]) :]
            # ans = re.search("\nA:(.*)\n|Q:|A:", ans).group(1)

        # if len(text_to_summarise) and not is_question:
        #     output = query_hugging_face(
        #         {
        #             "inputs": " ".join(text_to_summarise.split(" ")[:512]),
        #         },
        #         question=False,
        #     )
        #     print(output)
        #     ans = "Summary of Top Hit: " + output[0]["summary_text"]
        data = [{"title": ans, "description": ans}] + data

    return JsonResponse({"0": data}, safe=True, content_type="application/json")
