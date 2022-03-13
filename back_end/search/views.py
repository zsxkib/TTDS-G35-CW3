#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from time import sleep
import requests
from .models import Search
import python.search_4 as search_py
from rest_framework import viewsets
from django.http import JsonResponse
from .serializers import SearchSerializer
from django.utils.datastructures import MultiValueDictKeyError


search_py.load_offsetfile()
search_py.load_titles()


def query_hugging_face(payload, question):
    if question:
        API_URL = "https://api-inference.huggingface.co/models/EleutherAI/gpt-j-6B"
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
        number_hits_wanted = request.GET[
            "hitcount"
        ]  # number of hits we want to retrieve
        search_term = request.GET["query"]
        print(f"query = {search_term}")
        data = search_py.search(
            query=search_term.lower(), hits_wanted=int(number_hits_wanted)
        )
        text_to_summarise = ""
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
                text_to_summarise = (
                    raw_desc if text_to_summarise == "" else text_to_summarise
                )
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

        ans = ""
        try:  # QUESTION ANSWERING / SUMMARY
            _ = request.GET["question"]

            # if q: is prefix or ? us last char, then it's a question
            is_question = (
                "q:" in search_term[:2].lower() or "?" in search_term[-1]
            ) and len(data) > 0
            if is_question:
                query = search_term
                query = query.replace("q:", "").replace("Q:", "")
                query = query + "?" if query[-1] != "?" else query
                prompt = f"Q: {query}\nA:" ""
                output = query_hugging_face(
                    payload={
                        "inputs": prompt,
                    },
                    question=True,
                )
                ans = output[0]["generated_text"]
                # ans = ans[len(prompt):]#.split("\n")[0]
                print(ans)
            # ans = ans[len(prompt) :]
            # ans = re.search("\nA:(.*)\n|Q:|A:", ans).group(1)

            elif len(text_to_summarise):
                output = query_hugging_face(
                    payload={
                        "inputs": " ".join(text_to_summarise.split(" ")[:250]),
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
