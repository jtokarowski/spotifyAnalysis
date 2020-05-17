import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix

class stats:

    def __init__(self, rawSongs):
        
        dfReadySongs = []
        for song in rawSongs:

            songAudioFeatures = song['audioFeatures']
            if songAudioFeatures == None:
                continue

            artistNames = song['artistNames']
            artistIDs = song['artistIDs']

            if len(artistNames)==1:
                song['artistNames'] =artistNames[0]
            else:
                song['artistNames'] = ",".join(artistNames)

            if len(artistIDs)==1:
                song['artistIDs'] = artistIDs[0]
            else:
                song['artistIDs'] = ",".join(artistIDs)

            for key,val in songAudioFeatures.items():
                song[str(key)] = val

            del song['audioFeatures']
            del song['id']
    
            dfReadySongs.append(song)
        
        #convert songs to dataFrame
        dataframe = pd.read_json(json.dumps(dfReadySongs) , orient='records')
        self.df = dataframe

    def logReg(self):

        #add funcitonality here to take in playlist name to use as Y
        df = self.df

        df["UBP"] = df["collection"].map(lambda x: 1 if "UpbeatPiano" in x else 0)

        x_train, x_test, y_train, y_test = train_test_split(df.drop('UBP',axis=1), df['UBP'], test_size=0.50, random_state=101)
        x_trainMap = x_train[['trackId','artistIDs','collection']]
        x_testMap = x_test[['trackId','artistIdD','collection']] 
        x_train.drop(['trackId','artistIDs','collection'],axis=1, inplace=True)
        x_test.drop(['trackId','artistIdD','collection'],axis=1, inplace=True)

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
        X.drop_duplicates('trackID', inplace = True)
        X.reset_index(inplace=True)
        self.df = X

        return

    def kMeans(self, featuresList, means):

        stats.removeDupes(self)

        X = self.df

        kmeans = KMeans(n_clusters=means, random_state=101,init='random')
        Xlabels = X[['trackID']]
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
        if type(centers)==list:
            assignedCenter = centers
        else:
            assignedCenter = centers[x['kMeansAssignment']]

        for i in range(len(featuresList)):
            diff = (x[featuresList[i]]*100) - (assignedCenter[i]*100)
            totalEuclideanDistance += diff * diff

        return totalEuclideanDistance
