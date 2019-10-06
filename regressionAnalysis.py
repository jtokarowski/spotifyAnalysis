from pymongo import MongoClient
import json
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()  # for plot styling
import numpy as np
import pandas as pd
import sklearn
import matplotlib.pyplot as plt 

#set up mongo client
client = MongoClient('localhost', 27017)
name = '20191005jtokarowski'
db = client[name] #this repo won't change, ok to run tests here
#collection = db.allSongInfo
cursor = db.allSongInfo.find({})  #temp DB that has all songs in it

#blank list for unpacked songs
songs = []

for document in cursor:

    doc = document['audioFeatures']["audio_features"][0]

    if doc==None:
        continue

    an = document['artistNames']
    ai = document['artistIds']

    if len(an)==1:
    	document['artistNames'] = an[0]
    else:
        strList = ",".join(an)
        document['artistNames'] = strList

    if len(ai)==1:
    	document['artistIds'] = ai[0]
    else:
        strList = ",".join(ai)
        document['artistIds'] = strList

    for key,val in doc.items():
        document[str(key)] = val

    del document['audioFeatures']
    del document['type']
    del document['_id']
    del document['track_href']
    del document['id']
    del document['analysis_url']
    del document['uri']
    songs.append(document)


df = pd.read_json(json.dumps(songs) , orient='records')

print(df.head())

# need to import json into pandas dataframe
# need to merge duplicates, set playlist inclusion to be a list

# plt.scatter(energy, valence, color='C1')

# plt.xlabel('energy')
# plt.ylabel('valence')
# plt.title("Simple Plot")
# plt.show()
        