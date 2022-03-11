import os
from pathlib import Path
from urllib.request import urlretrieve
from time import sleep

while True:
    link = "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2"
    urlretrieve(link, Path.cwd() / "back_end/python/wiki-full.xml.bz2")

    os.chdir(Path.cwd() / "back_end/python/")
    os.system("bzip2 -d wiki-full.xml.bz2")

    os.system(f"python3 index_wiki_dump wiki-full.xml idx/")
    
    os.remove("wiki-full.xml.bz2")
    os.remove("wiki-full.xml")
    sleep(604800)