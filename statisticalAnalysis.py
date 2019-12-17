from pymongo import MongoClient
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix

class stats:

    def __init__(self, songs):
        
        songsfinal = []
        for song in songs:

            doc = song['audioFeatures']
            if doc==None:
                continue

            an = song['artistNames']
            ai = song['artistIds']

            if len(an)==1:
                song['artistNames'] = an[0]
            else:
                strList = ",".join(an)
                song['artistNames'] = strList

            if len(ai)==1:
                song['artistIds'] = ai[0]
            else:
                strList = ",".join(ai)
                song['artistIds'] = strList

            for key,val in doc.items():
                song[str(key)] = val

            del song['audioFeatures']
            del song['type']
            del song['id']
            del song['track_href']
            del song['analysis_url']
    
            songsfinal.append(song)
        
        #convert songs to dataFrame
        df = pd.read_json(json.dumps(songsfinal) , orient='records')
 
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

    def removeDupes(self):
        X = self.df
        X.drop_duplicates('trackId', inplace = True)
        X.reset_index(inplace=True)
        self.df = X

        return

    def kMeans(self, featuresList, means):

        stats.removeDupes(self)

        X = self.df

        kmeans = KMeans(n_clusters=means, random_state=101,init='random')
        Xlabels = X[['trackId']]
        Xselect = X[featuresList]
        kmeans.fit(Xselect)
        y_kmeans = kmeans.predict(Xselect)
        X['kMeansAssignment'] = y_kmeans
        centers = kmeans.cluster_centers_
  
        X['euclideanDistance']=X.apply(lambda x: stats.euclideanDistance(x,featuresList,centers), axis=1)

        X.sort_values('euclideanDistance',ascending=True,inplace=True)
        
        self.df = X
        self.centers = centers

        return

    def euclideanDistance(x, featuresList, centers):
        totalEuclideanDistance = 0
        assignedCenter = centers[x['kMeansAssignment']]
        for i in range(len(featuresList)):
            diff = (x[featuresList[i]]*100) - (assignedCenter[i]*100)
            totalEuclideanDistance += diff * diff

        return totalEuclideanDistance