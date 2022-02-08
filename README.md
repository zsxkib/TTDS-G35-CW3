## TTDS Project
Dear TTDS students,

Thank you for submitting the group membership form for TTDS. Your group ID is 35. Please use this number in your submission and for all questions and comments you may have relating to your group. Please avoid contacting us by email if possible - use Piazza instead, where you can make your question private if necessary. This ensures that all instructors can see your post and you get a reply as soon as possible. 

Note: If you are receiving this email, then you have been named by the group representative as a member of the group. Please let us know immediately if this is an error.

Provisional title: TTDS Group Project (Video Games?)

Group representative: Sakib Ahamed

Names of other group members:
Dan Buxton
Kenza Amira
Wini Lau
Mansoor Ahmad

I will be on leave until 10 January. Happy holidays and a happy new year!

Best,

Björn

## Documentation
### Scraping

---

 - spider.py: File containing the code for the web crawler
 - test.txt: File containing all the urls to look at (not sure I've covered everything)

To run the scraper make sure you first **install scrapy** on your machine by running: `pip install scrapy`

Then go to the right directory and run `scrapy runspider spider.py` to run the spider. 
If you wish you can add `-o file_name.json` to save the output to a json file with the desired *file_name*.

> Note: It's a lot of scraping so it's very likely to take a while


### Creating SSH Keys

---

1. In terminal run `ssh-keygen` and press enter through all the options
2. Go to the location where the ssh key was stored by default, generally a folder called .ssh in your home directory
3. Find the file with the extension .pub, probably id_rsa.pub, 
    1. Open it as a text folder and copy the contents and send it to me
    2. Alternatively put the file in the keys folder on the github, renaming it with your name

### Accessing Local Server

---

1. Open SSH client of choice:
    1. For vscode look in the bottom left for a blue button an click connect to host and enter the `user@address`...
    2. MobaXTerm right click on side bar and click new session and then enter address details...
    3. For terminal simply type `ssh user@address`
2. For the user and address, the user is just your first name in lowercase and the address is `176.252.92.24`. If this doesn't work this IP may have changed. 
    - Logging into the server **requires** key authentication, so if you haven’t sent me you ssh key you will not be able to access the server.
3. However you will need a password for root access, I have texted you a password however if you want to change it, you can use `passwd`.
4. All the files including the GitHub are stored in the Public folder in your Home directory.

<aside>
⚠️ If you get To continue type in the phrase ‘Yes, do as I say!’, stop. This is an important system warning you are about to delete something integral!

</aside>

## Using Git from Terminal

---

- Getting repo : `git clone <url>`
- Update repo : `git fetch` then `git pull`
- Push update : `git commit -a -m <description>` then `git push origin <branch>`
    - You will need to give yourself a name and email: `git config --global user.name <name>` and `git config --global user.email <email>`

<aside>
⚠️ https://docs.gitlab.com/ee/gitlab-basics/start-using-git.html

</aside>

### Accessing the GCP Disk

---

1. Make sure I have your ssh key and have added it to GCP
2. In terminal run `ssh {username}@34.65.79.224` where the username is the username on the computer created the ssh key. You can check what this by looking at the end of your ssh key and see the name before the @.

Eg. `ssh winilau@34.77.94.231`

<aside>
⚠️ I am going to change this at somepoint to use OAuth as it’s recommended and easier for you to add new PCs.

</aside>

### Running React Site

---

1. Install nvm (alternatively nodejs and npm)
    1. Linux or WSL2 :  `curl -o- [https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh](https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh) | bash`
        1. If you are on WSL2, have your git folder in the WSL directory otherwise it’s really slow
    2. Mac with homebrew `brew install nvm`
2. In directory with package.json, either **frontend/my app** or **web**, run `npm install`
3. Run `npm start`, this can take a while to start

### **Using Simple and Advanced Search Python Files**

---

There are two files AdvancedSearch.py and SimpleSearch.py. AdvancedSearch is a child of and imports all of SimpleSearch so can be used alone. This can be done directly or by importing them like a package.

1. Install the prequiste python packages
    - You can do that with `pip install -r python/requirements.txt` in repository
2. Import AdvancedSearch using `from AdvancedSearch import AdvancedSearch` 
3. Running for testing AdvancedSearch by `python3 -i python/AdvancedSearch` 
4. For both you can then create the class as objects with `AdvancedSearch(path, preindex, rerun, quiet)`
    - path : path to XML file stored within python folder
    - preindex=True : whether or not to preprocess and index XML file during init
    - rerun=False : whether to rerun and overwrite the stored json files for the indexes
    - quiet=True : whether to output the XML errors (can be printed with `getErrors()`)

#### Advanced Search Variables

- datapath
- quiet
- threaded
- corpora
- tags
- xmldata
- xmlerrors
- tokens
- terms
- indexes[method]
- uniqueTokerms
- uniqueGIDs
- uniqueTags
- model

#### Advanced Search Commands

- filterCorpora(corpora)
    - corpora=’ALL’ : allows you to filter the active corpora being searched
- getErrors()
- readXML()
- preprocessing(data)
- fullIndex
- indexing(method)
- phraseSearch(query)
- rankedIR(query)
- proximitySearch(query, proximity, absolute)
- booleanSearch(query)
- analysis(method)
- lda()
- classifier(tag, stem, idf, C)
- createXy(tokerms, tag, idf)
- classifierStats(X, y)
