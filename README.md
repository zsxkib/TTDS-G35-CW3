# Introduction

Wikipedia is one of the most popular websites in the world, ranking as the 7th most visited globally as of February 2022 according to Similarweb. This is up on previous months and previous years, showing a growing popularity. The site is especially popular amongst students who use it to get quick access to summaries about topics they are researching. We tasked ourselves to create a search engine to aid students with this task.


# What's is this?

We have created a search engine with two unique indices. The first is ranked IR which uses the classical TF-IDF to rank documents for their relevance. The second index converts documents into word embeddings using a GPU and clusters, using a query term's euclidean distance to the documents to find the most relevant matches. The front-end was created with React and the back-end was created using Django and Python 3.7.x. This search engine also provides AI powered summaries and question answering capapilities using the Hugging Face API.
 
To view the full version of the site, please go to: http://ttds.dtbmail.com/

## Vector Index

The first step in the creation of this index is to start with a mapping: `page id` to the text data. The text data has to be embedded and we create the `wikidata vectors`. To do this, we use a sentence transformers library. BERT (Bidirectional Encoder Representations from Transformers) is the best performing library available for this task. It removes the constraint imposed on normal transformers and adding bidirectionality using a Masked Language Model. However, due to the substantial size of our dataset, using this would be too slow. Instead, we use a DistilBERT model. The performance of this is not quite on the level of BERT, but due to being 40% lighter, it comes with a significant speed increase. From this, we use the `distilbert-base-nli-stsb-mean-tokens` library, which is the best performing DistilBERT version on on Semantic Textual Similarity tasks.

Vector similarity searches can be conducted efficiently using Faiss, a Facebook library. This will be built around the index containing the searchable vectors. To further speed up searching, we segment the dataset into pieces by defining Voronoi cells in d-dimensions and a query will only look at the relevant cell when searching (plus potentially some neighbouring ones).

To carry out this task, we create an IndexFlatL2 index, also known as the quantizer. This gets passed the dimensions of the embedded vectors and its task is to assign vectors to Voronoi cells. Each cell is defined by a centroid and this index tracks, for each vector in `wikidata`, the closest centroid via L2 norm and therefore which Voronoi cell each vector belongs to.

The quantizer is then passed onto the next index, the IndexIVFFlat index. This also gets passed the number of desired Voronoi cells and the location of the centroids depends on this number. The role of this index is to only look at database vectors $y$ that are contained within the cell that query $x$ falls into at search time (plus some near neighbours). This index requires training on a dataset with the same distribution as ours. We simply train it on our embedded vectors.


# Data Collection 

The first task in creating this search engine was to collect the data that our users would be searching through. For our purposes, we chose to use all of English Wikipedia. Not only would using all of Wikipedia have created a dataset that could be too large to handle, but also our methods specifically made sense for the English language (see preprocessing). The English language section of Wikipedia is the largest section and, unlike other languages, is all human generated, thus removing bot translation issues that could arise when trying to group Wikipedia articles.

We had the option of using web scraping to get our data. However, the decision was eventually made to avoid this. Not only would this increase the time taken for our task, but scraping data could lead to infringements on the rules of website owners and their protection of their products. While this was not seen as an issue for Wikipedia, we felt this would limit any potential expansion we may look to make to our search engine in the future.

Instead, we chose to collect data using data dumps, which results in a slightly different size of database each collection, but is $\sim 80$GB. In our recent dump, this was 79.4GB. This includes over 6 million articles and over 4 billion words


# Pre-Proccessing

Creating an index from the 80GB data dump required us to parse the XML and preprocess the data. The methods for doing so were as follows:

* Parsing: We parsed through the XML using the SAX parser. Using this we created a `WikiHandler` class that looked at the XML tags relevant to us (`page id, title, text`) and stored them before they could then be passed to another job, before moving onto the next page of Wikipedia.
* Casefolding: The task of removing any case differences between letters was simple using the `lower()` method built into Python.
* Tokenization: Using `regex`, we split sentences into the tokens we wanted.
* Stop Words: A list of 571 words was referred to in order to remove stop words.
* Stemming: We used the `nltk` library's `PorterStemmer` to stem the remaining words.

Once preprocessing is complete, individual index files are created with tokens and their respective posting list. All the indexed files created in the previous step are merged (k-way merge sort). Then we split the index into separate files in alphabetically sorted order. The index is now ready for querying. To query we use the offset file to find the correct index file and conduct a binary search to find the desired token, we then retrieved document IDs and term frequencies weighted TF-IDF and return the top hits.

# How do I run it locally?

Due to the limiations of github, we can not upload the whole ranked IR index or our vector index, instead we index a small subset of the data and include it in this repo. Thi means that you will be able to clone and run locally!

## Installing depencandies

```
$ conda env create --file=req_conda.ym --name ttds
$ conda activate ttds
```

## Starting the back-end

To start the back-end you must open the port 8000 and then run the following:

```
$ python3 back_end/manage.py runserver 0:8000
```

## Starting the front-end

To start the back-end you must open the port 3000 and then run the following:

```
$ cd  front_end
$ npm install
$ npm start
```

## How to index
### Ranked IR
For creating indexes use the following command:

```
python3 index_wiki_dump.py ../enwiki-xxxxxxxx-pages-articles-multistream.xml ./back_end/python/idx
```

### Vector Search
The path to the wikipedia xml is hard-coded within this file, so you may have to change it.

```
vector_index_wiki_dump.py
```

# Evaluation

We set ourselves the challenge of creating a product aimed at students that would streamline their task of research. Using English Wikipedia as our dataset, we achieved our goal of creating such a search engine. However, there are further improvements that could be made as well as limitations in the tasks we carried out.

# Further Tasks

The first additional task to improve usability of our search engine would be a spell check. 1 in 10 Google queries contain a misspelled word, suggesting that spelling mistakes are very common when using search engines. A simple spell checker could be used to look at the query as entered by the user and the back end could provide a possible phrase correction. This would work in a similar fashion to Google's "Did you mean..." feature.

Another improvement for our search engine's usability would be to implement an auto-complete feature for when the user is searching. Due to the amount of data we have, this could be very difficult so would by requirement be a more simple version. This would maybe be auto-complete only on Wikipedia article titles.

# Reflections

The aims for this project were, by design, very ambitious. The dataset we collected was massive and thus proved very difficult to handle. Due to its size, there were lots of tasks that took too many resources, including time, for us to be able to carry them out efficiently. In this section, we look at the limitations of our final product and the issues we ran into.

The first, and main, issue we ran into was a lack of processing power. We had to store and then create an index from 80GB of data. While we had access to GCP credits, these ran low quickly. The same happened with Azure credits. Unfortunately, both these platforms were overly complicated to renew and use for our purposes so the decision eventually had to be made to store the data, index, and host, on a local computer.

The indexing was done in RAM, which was very limited and thus we could only index a small amount of Wikipedia pages at a time. Had we had access to more resources, this would have significantly sped up the process. The priority was to create the primary index and this was done. However, both the positional index as well as the vector index were built on a subset of the entire dataset. This is why we kept the first index as the primary functioning one for our search engine. The subset used was approximately one-third of the entirety of English Wikipedia. This meant that, instead of working on all 6 million articles, we used around 2 million.

Given more time or better resources, we would have been able to create these indexes without any extra trouble. However, it has to be admitted that we went too far in what we attempted to do with the resources and time we had available. Upon reflection, with the time taken to create any index, splitting the available time between 3 was ill advised.

The performance of the vector index was our best. In pages it had been indexed for, results were fetched with great semantic similarity to the query. If we were to repeat this task, we would prioritise creating this index. Unfortunately, as it only used a subset of our dataset, results from queries related to pages it hasn't indexed are very poor.

In addition to our search function, we chose to add an AI component. The decision was made to add these extra features as they fit in well with the targets for our project. The aim was to create a search engine streamlining the process of research for student. Being able to summarise Wikipedia articles not only provides a quick introduction for the user into their topic (and the majority of students use Wikipedia as an introductory resource in their research), but also quickly allows the user to determine whether the page is relevant to what they are looking for. This functions well, but could stand to be improved. With more time, we would have conducted further testing in order to fine tune the parameters of the model.

The question answering component was also important to achieving our aims. This is the largest time save for the user, being able to ask a question on a topic and receive a quick answer rather than manually reading the first 3 Wikipedia articles to find it. Despite chaining AI in order to have context for the `roberta-base-squad2` model, we were able to gain good results. However, this was dependent on the quality of the search results. If the top 3 results were seen to be related to the topic of the question, we were able to provide good answers. Unfortunately, our best index and search, the vector index, was not indexed on all of our dataset. This meant the top 3 results were not always the best possible options.

The design of our search engine was simple, but effective. With further tasks, such as auto-complete, more designing would have to be done. The light colour scheme fits with Wikipedia's light scheme, but is more pleasing to look at due to not being black text on a white background. This adds readability, especially for those with visual or learning difficulties. The body of the text is in a sans-serif font, further aiding readability.
