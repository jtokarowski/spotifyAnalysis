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

#work to do::::
#convert the spotify api request into a group pull of up to 100 ids
#convert the mongo insert to a master large insert at the very end

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
db = client.spotifyData3

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
    playlistCount2 = len(currentUserPlaylistsRaw['items']) #this corrects for 50 limit

    #if playlistCount > playlistCount2
    # loop through first 100
    # else
    #loop through playlistCount
    
    #loop through playlists, pull analysis on each one, enter into DB as new collection
    for i in range(playlistCount2): #retrieve up to limit worth of playlists
        currentPlayList = currentUserPlaylistsRaw['items'][i]
        playlistName = currentPlayList['name']
        uri = currentPlayList['uri']
        #name the collection based on the playlist it is retrieving from
        playlistName = playlistName.title()
        playlistName = playlistName.replace(" ", "")
        print(i, playlistName)
        collection = db[playlistName]
        #retrieve songs in playlist up to limit 100
        apiresults = sp.user_playlist_tracks(username, uri, offset=0)
        #form an empty list of spotify URI's
        uriList = []

        # grab the relevant data from each track
        playlistTracks = apiresults['items']
        lengthResults = apiresults['total'] # number of results spotify wants to return
        lengthResults2 = len(playlistTracks) #number of results returned based on limit

        for j in range(lengthResults2): #temp set to shorter of the two, until longer term fix instituted
            uriList.append(playlistTracks[j]['track']['uri'])
        
        
        offset = 0
        #testing to see if we retrieved all songs
        if lengthResults > lengthResults2:
            print('playlist track limit exceeded')
            runs = int(round(lengthResults/100))
            print(runs)
            for m in range (runs):
                #print(m)
                print(offset)
                offset += 100
                apiresults2 = sp.user_playlist_tracks(username, uri, offset=offset)
                playlistTracks2 = apiresults2['items']
                lengthResults2 = len(playlistTracks2)
                for j in range(lengthResults2): #temp set to shorter of the two, until longer term fix instituted
                    uriList.append(playlistTracks[j]['track']['uri'])

        indexK = 0
        playlistAttributes=[]
        for k in uriList:
            attributes = sp.audio_features(uriList[indexK])[0]
            attributes["playlistAssignment"] = playlistName
            playlistAttributes.append(attributes)
            indexK = indexK +1
            #attributeID = collection.insert_one(attributes).inserted_id
        results = collection.insert_many(playlistAttributes)
        print(results.inserted_ids)
     

else:
    print("Can't get token for", username)
