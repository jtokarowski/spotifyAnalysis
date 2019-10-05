from pymongo import MongoClient
import json
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()  # for plot styling
import numpy as np

#set up mongo client
client = MongoClient('localhost', 27017)
db = client.spotifyData20190731 #this repo won't change, ok to run tests here
collections = db.list_collection_names()


#initialize the blank lists for attribute values
energy = []
valence = []

#loop thru all collections, append the data to the master lists
iterator = 0
for collection in collections:
	collection = db[collections[iterator]]
	cursor = collection.find({})
	#print(collections[iterator])
	iterator += 1

	for document in cursor:
		energy.append(document['energy'])
		valence.append(document['valence'])
	


plt.scatter(energy, valence, color='C1')

plt.xlabel('energy')
plt.ylabel('valence')
plt.title("Simple Plot")
plt.show()
        

#merge all playlists into 1 master repo, split the attributes into vectors
#label each song with the playlist (or playlists) that contained it
#run analysis to see the differences by playlist
#perhaps color code the plotted points by playlist so i can visualize it


#select the relevant info from each entry (specific attribute) then insert into new db that only stores attributes

#k-means goes here

#put k-means output into new DB