from pymongo import MongoClient
import json
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()  # for plot styling
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt 

class stats:

    def __init__(self):
        #unpacks database     
        #later- have this function take in the database name coming from app.py
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
            del document['id']
            del document['track_href']
            del document['_id']
            del document['analysis_url']
            del document ['uri']
    
            songs.append(document)

        #convert songs to dataFrame
        df = pd.read_json(json.dumps(songs) , orient='records')
        #remove dupes in playlists
        dropRows = df.duplicated(['trackId','collection'])
        df.drop(dropRows,inplace=True)

        #combine rows where track is in multiple playlists
        df = df.groupby(['trackId','acousticness','artistIds','danceability','energy','instrumentalness','key','liveness','loudness','speechiness','tempo','time_signature','valence'])['collection'].apply(','.join).reset_index()
    
        self.df = df

    def logReg(self):

        #add funcitonality here to take in playlist name to use as Y
        df = self.df

        df["UBP"] = df["collection"].map(lambda x: 1 if "UpbeatPiano" in x else 0)

        x_train, x_test, y_train, y_test = train_test_split(df.drop('UBP',axis=1), df['UBP'], test_size=0.50, random_state=101)
        x_trainMap = x_train[['trackId','artistIds','collection']]
        x_testMap = x_test[['trackId','artistIds','collection']] 
        x_train.drop(['trackId','artistIds','collection'],axis=1, inplace=True)
        x_test.drop(['trackId','artistIds','collection'],axis=1, inplace=True)

        #create an instance and fit the model 
        logmodel = LogisticRegression()
        logmodel.fit(x_train, y_train)
        #predictions
        Predictions = logmodel.predict(x_test)
        #print(Predictions)
        #print(classification_report(y_test,Predictions))
        confMat = confusion_matrix(y_test, Predictions)

        return confMat

    def kMeans(self):

        X = self.df

        kmeans = KMeans(n_clusters=5)
        Xlabels = X[['trackId']]
        Xselect = X[['acousticness','danceability','energy','instrumentalness','key','liveness','loudness','speechiness','valence']]
        kmeans.fit(Xselect)
        y_kmeans = kmeans.predict(Xselect)
        X['kMeansAssignment'] = y_kmeans
        centers = kmeans.cluster_centers_
        
        #print(X)
        #print(centers)

        return X


    #def plotting(self):

        #UBP = df.loc[df['UBP'] == 1]

        #playlist level
        #sns.distplot(UBP['valence'].dropna(), kde=False, bins=20, color='Green')
        #sns.distplot(UBP['energy'].dropna(), kde=False, bins=20, color='Blue')
        #sns.distplot(UBP['danceability'].dropna(), kde=False, bins=20, color='Black')

        #population level
        #sns.distplot(df['valence'].dropna(), kde=False, bins=100, color='Green')
        #sns.distplot(df['energy'].dropna(), kde=False, bins=100, color='Blue')
        #sns.distplot(df['danceability'].dropna(), kde=False, bins=100, color='Black')
        #plt.show()

