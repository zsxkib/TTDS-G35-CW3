from django.apps import AppConfig

import os
# import python.SimpleSearch as SimpleSearch
from python.SimpleSearch import *
# import AdvancedSearch
# import SmartSearch
from pathlib import Path

class StartupConfig(AppConfig):
    name = 'startup'#

    def ready(self):
        # pass # startup code here
        print("STARTUP!!")
        print(os.getcwd())
        
        path_to_corpus = Path("back_end/python/data/wikidata_short.xml")
        # simple_search = ClassicSearch(path_to_corpus, rerun=True)
        

        # # TODO: INDEX if not already indexed!
        # print("INDEXING CODE (WILL ONLY BE RUN ONCE)")

        # pth2data = "wikidata_short.xml"
        # simple_search_obj = SimpleSearch.SimpleSearch(pth2data, rerun=True)
        
        # TODO: Search (this shouldn't be done here, but it's here for clarity)
        # assuming indexing has already been done, look at ./backend/search/views.py
        # that's where the searching part is done
        # simple_search_obj.rankedIR("Anarchism")

