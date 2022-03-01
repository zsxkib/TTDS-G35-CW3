from pyexpat import model
from re import search
from urllib import request
from .serializers import SearchSerializer
from rest_framework import viewsets
from .models import Search
from django.shortcuts import render
import json
from python.SimpleSearch import *
from django.http import HttpResponse, JsonResponse

dummyData = [
    {
      "title": "Apple",
      "link": "https://en.wikipedia.org/wiki/Apple",
      "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. In in elit mollis tortor consectetur porta ut vel massa. Proin viverra ex non lectus semper, vel vulputate risus aliquam. Aeneaneu auctor quam. Pellentesque ac turpis est. Etiam facilisis lacus mauris, quis faucibus sapien molestiut. Phasellus ultricies, magna a egestas pulvinar, risus mauris aliquam orci,in porta eros nunc in ligula. Done lobortis interdum lectus. Quisque tristique tinciduntdiam quis euismod. Integer quis egestas massa.",
    },
    {
      "title": "Banana",
      "link": "https://en.wikipedia.org/wiki/Banana",
      "description": "xxxLorem ipsum dolor sit amet, consectetur adipiscing elit. In in elit mollis tortor consectetur porta ut vel massa. Proin viverra ex non lectus semper, vel vulputate risus aliquam. Aeneaneu auctor quam. Pellentesque ac turpis est. Etiam facilisis lacus mauris, quis faucibus sapien molestiut. Phasellus ultricies, magna a egestas pulvinar, risus mauris aliquam orci,in porta eros nunc in ligula. Done lobortis interdum lectus. Quisque tristique tinciduntdiam quis euismod. Integer quis egestas massa.",
    },
  ];
# path_to_corpus = Path("back_end/python/data/wikidata_short.xml")
# mongo_search = MongoSearch(path_to_corpus, rerun=True, threads=8)

# Create your views here.
class SearchView(viewsets.ModelViewSet):
    serializer_class = SearchSerializer
    queryset = Search.objects.all()

def search(request):
    if request.method == "GET":
        search_term = request.GET["query"]
        print(search_term) 
        if "?" in search_term:
          # TODO add api call here
          return 
        
        # jsonstring = mongo_search.searchtojson(search_term)
        else:
          return JsonResponse({'0': dummyData}, safe=True, content_type="application/json")
    else:
        # TODO: ERROR HANDLING
        pass

    # return render(request, "search.html")
