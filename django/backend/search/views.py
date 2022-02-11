from pyexpat import model
from re import search
from django.http import HttpResponse
from .serializers import SearchSerializer
from rest_framework import viewsets
from .models import Search
from django.shortcuts import render

# Create your views here.

class SearchView(viewsets.ModelViewSet):
    serializer_class = SearchSerializer
    queryset = Search.objects.all()

def home(request):
    return render(request,'search/home.html')

def search(request):
    search_term = request.GET['show_search']
    print(search_term)
    print('hiii')