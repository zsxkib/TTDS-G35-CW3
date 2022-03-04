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
  ]

# dummyData = [
#         {"title": "69171296",
#           "link": "https://en.wikipedia.org/?curid=69171296", 
#           "description": "69171296"
#         },
#         {"title": "69171296",
#           "link": "https://en.wikipedia.org/?curid=69171296", 
#           "description": "69171296"
#         },
#           ]

# {
#   "0": [
#     {
#       "title": "Apple",
#       "link": "https://en.wikipedia.org/wiki/Apple",
#       "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. In in elit mollis tortor consectetur porta ut vel massa. Proin viverra ex non lectus semper, vel vulputate risus aliquam. Aeneaneu auctor quam. Pellentesque ac turpis est. Etiam facilisis lacus mauris, quis faucibus sapien molestiut. Phasellus ultricies, magna a egestas pulvinar, risus mauris aliquam orci,in porta eros nunc in ligula. Done lobortis interdum lectus. Quisque tristique tinciduntdiam quis euismod. Integer quis egestas massa."
#     },
#     {
#       "title": "Banana",
#       "link": "https://en.wikipedia.org/wiki/Banana",
#       "description": "xxxLorem ipsum dolor sit amet, consectetur adipiscing elit. In in elit mollis tortor consectetur porta ut vel massa. Proin viverra ex non lectus semper, vel vulputate risus aliquam. Aeneaneu auctor quam. Pellentesque ac turpis est. Etiam facilisis lacus mauris, quis faucibus sapien molestiut. Phasellus ultricies, magna a egestas pulvinar, risus mauris aliquam orci,in porta eros nunc in ligula. Done lobortis interdum lectus. Quisque tristique tinciduntdiam quis euismod. Integer quis egestas massa."
#     }
#   ]
# }




# path_to_corpus = Path("back_end/python/data/wikidata_short.xml")
path_to_corpus = Path("python/data/wikidata_short.xml")
classic = ClassicSearch(
  Path.cwd() / path_to_corpus, 
  rerun=False, 
  debug=True,
  )

class SearchView(viewsets.ModelViewSet):
    serializer_class = SearchSerializer
    queryset = Search.objects.all()

def search(request):
    if request.method == "GET":
        search_term = request.GET["query"]
        data = dummyData
        print(search_term) 
        search_term = "Economic AND Systems "
        results = classic.booleanSearch(search_term)
        data = []
        for pid in results:
          data += [{"title": pid, 
                   "link": f"https://en.wikipedia.org/?curid={pid}", 
                   "description": pid}]
        print(f"\nResults : {data}")
        if "?" in search_term:
          # TODO add api call here
          return 
        
        # jsonstring = mongo_search.searchtojson(search_term)
        else:
          return JsonResponse({'0': data}, safe=True, content_type="application/json")
    else:
        # TODO: ERROR HANDLING
        pass

    # return render(request, "search.html")
