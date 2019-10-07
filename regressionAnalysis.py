from pymongo import MongoClient
import json
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()  # for plot styling
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
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
#df.loc[df['UBP'] == 1]
#print(df.head())

x_train, x_test, y_train, y_test = train_test_split(df.drop('UBP',axis=1), df['UBP'], test_size=0.50, random_state=101)

x_trainMap = x_train[['trackId','artistIds','collection']]
x_testMap = x_test[['trackId','artistIds','collection']] 

x_train.drop(['trackId','artistIds','collection'],axis=1, inplace=True)
x_test.drop(['trackId','artistIds','collection'],axis=1, inplace=True)

#print(x_train.head())
#print(x_test.head())

#create an instance and fit the model 
logmodel = LogisticRegression()
logmodel.fit(x_train, y_train)
#predictions
Predictions = logmodel.predict(x_test)
print(Predictions)

print(classification_report(y_test,Predictions))
print(confusion_matrix(y_test, Predictions))


