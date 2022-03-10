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


def query_hugging_face(payload):
    API_TOKEN = "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"
    API_URL = "https://api-inference.huggingface.co/models/EleutherAI/gpt-j-6B"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


class SearchView(viewsets.ModelViewSet):
    serializer_class = SearchSerializer
    queryset = Search.objects.all()


def search(request):
    data = []
    if request.method == "GET":
        search_term = request.GET["query"]
        print(f"query = {search_term}")
        query = search_term.lower()

        data = search_py.search(query)

        # query has prefix q: indicating it's a question and there's hits!
        if "Q:" in query[:2] and len(data) > 0:
            query = search_term[2:] + "?"
            # output = query_hugging_face({
            #         "inputs": f"Q:{search_term} A:",
            #         })
            output = "example answer"
            ans = re.search("\nA:(.*)\n|Q:", output[0]["generated_text"]).group(1)
            data = [{"answer": ans}] + data
        else:
            data = [{"answer": ""}] + data

        print(f"Top 5 Hits = {data[:5]}")
    return JsonResponse({"0": data}, safe=True, content_type="application/json")
