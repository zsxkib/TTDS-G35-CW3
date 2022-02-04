from django.shortcuts import render
from rest_framework import viewsets
from .serializers import SearchSerializer
from .models import Search

# Create your views here.

class SearchView(viewsets.ModelViewSet):
    serializer_class = SearchSerializer
    queryset = Search.objects.all()