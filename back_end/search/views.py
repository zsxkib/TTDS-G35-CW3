from .serializers import SearchSerializer
from rest_framework import viewsets
from .models import Search
from django.http import JsonResponse
import python.search_4 as search_py

search_py.load_offsetfile()
search_py.load_titles()

class SearchView(viewsets.ModelViewSet):
    serializer_class = SearchSerializer
    queryset = Search.objects.all()

def search(request):
    if request.method == "GET":
        search_term = request.GET["query"]
        query = search_term.lower()
        print(f"query = {query}")

        if any(_ in query for _ in ("t:", "b:", "i:", "c:", "e:")):
            data = search_py.field_query(query)
        else:
            data = search_py.simple_query(query)
        return JsonResponse({'0': data}, safe=True, content_type="application/json")
    else:
        # TODO: ERROR HANDLING
        pass