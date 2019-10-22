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

    def __init__(self, dbName, collection):
        #unpacks database into dataframe     
        #set up mongo client
        client = MongoClient('localhost', 27017)
        db = client[dbName] 
        dbCollection = db[collection]
        cursor = dbCollection.find({})  #temp DB that has all songs in it
        #blank list for unpacked songs
        songs = []
        for document in cursor:
            doc = document['audioFeatures']
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

    def kMeans(self, featuresList, means):

        X = self.df

        #featuresList = ['acousticness','danceability','energy','instrumentalness','liveness','speechiness','valence']
        kmeans = KMeans(n_clusters=means)
        Xlabels = X[['trackId']]
        Xselect = X[featuresList]  #'key','loudness',
        kmeans.fit(Xselect)
        y_kmeans = kmeans.predict(Xselect)
        X['kMeansAssignment'] = y_kmeans
        centers = kmeans.cluster_centers_
  
        X['euclideanDistance']=X.apply(lambda x: stats.euclideanDistance(x,featuresList,centers), axis=1)

        X.sort_values('euclideanDistance',ascending=True,inplace=True)
        
        self.X = X
        self.centers = centers

        return

    def euclideanDistance(x, featuresList, centers):
            totalEuclideanDistance = 0
            assignedCenter = centers[x['kMeansAssignment']]
            for i in range(len(featuresList)):
                diff = (x[featuresList[i]]*100) - (assignedCenter[i]*100)
                totalEuclideanDistance += diff * diff

            return totalEuclideanDistance


    def plotting(self):

        df = self.X
        data0 = df.loc[df['kMeansAssignment'] == 0]
        data0.drop(['trackId','artistIds','key','loudness','tempo','time_signature','collection','kMeansAssignment'],axis=1,inplace=True)

        data1 = df.loc[df['kMeansAssignment'] == 1]
        data1.drop(['trackId','artistIds','key','loudness','tempo','time_signature','collection','kMeansAssignment'],axis=1,inplace=True)

        #print(data1.head())
        #input("waiting.........")

        # data to plot
        n_groups = 7
        avg0 = data0.mean()
        avg1 = data1.mean()
        #means_frank = (90, 55, 40, 65)
        #means_guido = (85, 62, 54, 20)

        # create plot
        fig, ax = plt.subplots()
        index = np.arange(n_groups)
        bar_width = 0.35
        opacity = 0.8

        rects1 = plt.bar(index, avg0, bar_width,
            alpha=opacity,
            color='b',
            label='cluster0')

        rects2 = plt.bar(index + bar_width, avg1, bar_width,
            alpha=opacity,
            color='g',
            label='Guido')

        plt.xlabel('Cluster')
        plt.ylabel('Value')
        #plt.title('Scores by person')
        plt.xticks(index + bar_width, ('acousticness', 'danceability', 'energy', 'instrumentalness','liveness','speechiness','valence'))
        plt.legend()
        plt.tight_layout()
        plt.show()

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

