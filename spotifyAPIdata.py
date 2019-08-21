import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from pymongo import MongoClient
import json

#Spotify Data Retrieval Layer
#John Tokarowski 2019
#
# This program gets all playlists for a spotify user, retrieves the songs in those playlists
# retrieves the attributes for each song in the playlist, stores it in mongo in collection
# named for the playlist in which the song exists

#retrieves the credentials from config.json
with open('config.json') as json_data_file:
    configData = json.load(json_data_file)

cid = configData["spotify"]["cid"]
secret = configData["spotify"]["secret"]
username = configData["spotify"]["username"]

client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret) 
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

#set up db instance - will need to change this to create DB per each user
client = MongoClient('localhost', 27017)
db = client.spotifyData

#remove old collections to start fresh
oldCollections = db.list_collection_names()
iterator = 0
for h in oldCollections:
	db.drop_collection(oldCollections[iterator])
	iterator += 1

# Get read access to your library
scope = 'user-library-read'
token = util.prompt_for_user_token(username,scope,client_id=cid,client_secret=secret,redirect_uri='http://localhost/')

#this is the actual request to spotify for data
if token:
	#shortname for the retrieval program
    sp = spotipy.Spotify(auth=token)

    #retrieve user playlists
    currentUserPlaylistsRaw = sp.current_user_playlists()
    playlistCount = currentUserPlaylistsRaw['total']
    playlistCount2 = len(currentUserPlaylistsRaw['items'])

    #if playlistCount > playlistCount2
    # loop through first 100
    # else
    #loop through playlistCount
    
    #loop through playlists, pull analysis on each one, enter into DB as new collection
    for i in range(playlistCount2): #temp set to pull limit to avoid bug, need longer term fix 
    	currentPlayList = currentUserPlaylistsRaw['items'][i]
    	name = currentPlayList['name']
    	uri = currentPlayList['uri']

    	#name the collection based on the playlist it is retrieving from
    	name = name.title()
    	name = name.replace(" ", "")
    	print(i, name)
    	collection = db[name]
    	#print(collection)

    	#retrieve all songs in playlist
    	apiresults = sp.user_playlist_tracks(username, uri)
    	#apiresults2 = sp.user_playlist_tracks(username, uri)
    
    	#form an empty list of spotify URI's
    	uriList = []
    	nameList = []

    	# grab the relevant data from each track
    	
    	playlistTracks = apiresults['items']
    	lengthResults = apiresults['total'] # number of results spotify wants to return
    	lengthResults2 = len(playlistTracks) #number of results returned based on limit
    	#print(lengthResults)
    	#print(lengthResults2)
    	#if 

    	for j in range(lengthResults2): #temp set to shorter of the two, until longer term fix instituted
    		uriList.append(playlistTracks[j]['track']['uri'])
    		nameList.append(playlistTracks[j]['track']['name'])
    		#print(uriList)

    		# need to loop through uri list, grab attributes for each, store multiple in collection with insert_many code
    		#then need to retrieve all entries in DB collection
    		#then go back thru code and rename db collections, automate naming by underlying playlist ID, date, time, etc

    	indexK = 0
    	for k in uriList:
    		attributes = sp.audio_features(uriList[indexK])
    		#print(nameList[indexK])
    		indexK = indexK +1
    		#should edit this to embed song titles along with attributes for readability
    		attributeID = collection.insert_one(attributes[0]).inserted_id
    		#print(attributeID)
    		#print(attributes)
		   	#print(collection.find())
     

else:
    print("Can't get token for", username)
