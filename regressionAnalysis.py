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
for document in cursor:
	print(document)
	input('waiting')

# need to import json into pandas dataframe
# need to merge duplicates, set playlist inclusion to be a list

#{ "_id" : ObjectId("5d98f7bb9fbf27e2f4ab6663"),
# "trackName" : "IBetMyLife-AlexAdairRemix",
# "trackId" : "3bnEhDlFFXeCyyYhbRszW7",
# "artistNames" : [ "Imagine Dragons" ],
# "artistIds" : [ "53XhwfbYqKCa1cC15pYq2q" ],
# "collection" : "DbMajorSet5.17",
# "audioFeatures" : { "audio_features" : [ { "danceability" : 0.643, "energy" : 0.504, "key" : 1, "loudness" : -9.082, "mode" : 1, "speechiness" : 0.276, "acousticness" : 0.0809, "instrumentalness" : 0.000207, "liveness" : 0.152, "valence" : 0.625, "tempo" : 117.016, "type" : "audio_features", "id" : "3bnEhDlFFXeCyyYhbRszW7", "uri" : "spotify:track:3bnEhDlFFXeCyyYhbRszW7", "track_href" : "https://api.spotify.com/v1/tracks/3bnEhDlFFXeCyyYhbRszW7", "analysis_url" : "https://api.spotify.com/v1/audio-analysis/3bnEhDlFFXeCyyYhbRszW7", "duration_ms" : 190280, "time_signature" : 4 } ] } }





#initialize the blank lists for attribute values
# energy = []
# valence = []

# #loop thru all collections, append the data to the master lists
# iterator = 0
# for collection in collections:
# 	collection = db[collections[iterator]]
# 	cursor = collection.find({})
# 	#print(collections[iterator])
# 	iterator += 1

# 	for document in cursor:
# 		energy.append(document['energy'])
# 		valence.append(document['valence'])
	


# plt.scatter(energy, valence, color='C1')

# plt.xlabel('energy')
# plt.ylabel('valence')
# plt.title("Simple Plot")
# plt.show()
        

#merge all playlists into 1 master repo, split the attributes into vectors
#label each song with the playlist (or playlists) that contained it
#run analysis to see the differences by playlist
#perhaps color code the plotted points by playlist so i can visualize it


#select the relevant info from each entry (specific attribute) then insert into new db that only stores attributes

#k-means goes here

#put k-means output into new DB