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

# need to check if this fully works
dropRows = df.duplicated(['trackId','collection'])

#print(df.columns.values)
df.drop(dropRows,inplace=True)

#df = df.groupby('trackId').agg({'trackId':'first', 'collection': ', '.join}).reset_index()
df = df.groupby(['trackId','acousticness','artistIds','danceability','energy','instrumentalness','key','liveness','loudness','speechiness','tempo','time_signature','valence'])['collection'].apply(','.join).reset_index()

df["UBP"] = df["collection"].map(lambda x: 1 if "UpbeatPiano" in x else 0)
df.loc[df['UBP'] == 1]
print(df.head())

