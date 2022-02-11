from django.db import models

# Create your models here.

class Search(models.Model):
    search = models.TextField()
    
    def __str__(self):
        return '{}'.format(self.search)