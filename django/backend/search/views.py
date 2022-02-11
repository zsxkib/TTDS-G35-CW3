from pyexpat import model
from re import search
from django.http import JsonResponse
from .serializers import SearchSerializer
from rest_framework import viewsets
from .models import Search

# Create your views here.

class SearchView(viewsets.ModelViewSet):
    serializer_class = SearchSerializer
    queryset = Search.objects.all()

latest_search = str (Search.objects.latest('search'))
print(latest_search)
