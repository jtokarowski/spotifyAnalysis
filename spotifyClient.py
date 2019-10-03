from __future__ import print_function
import sys
import requests
import json
import time
from urllib.parse import quote
from pymongo import MongoClient
from datetime import date

#import dev keys
with open('config.json') as json_data_file:
    configData = json.load(json_data_file)

#grab the secret variables
CLIENT_ID = configData["spotify"]["cid"]
CLIENT_SECRET = configData["spotify"]["secret"]

#URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8000
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
AUTHED_URL = "{}:{}/authed".format(CLIENT_SIDE_URL, PORT)
REFRESH_URL = "{}:{}/refresh".format(CLIENT_SIDE_URL, PORT)
PLAYLISTS_URL = "{}:{}/playlists".format(CLIENT_SIDE_URL, PORT)
PLAYLIST_TRACKS_URL = "{}:{}/playlistTracks".format(CLIENT_SIDE_URL, PORT)
PLAYLIST_TRACK_FEATURES_URL = "{}:{}/playlistTrackFeatures".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-read-private"
STATE = "" #Should create a random string generator here to make a new state for each request

#grab date program is being run
td = date.today()
TODAY = td.strftime("%Y%m%d") ##YYYYMMDD

#set up db instance
client = MongoClient('localhost', 27017)

#construct auth request params
auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    "show_dialog": "true",
    "client_id": CLIENT_ID
}

class auth:
    def __init__ (self):
    	#step 1: Spotify User OK's application access
        url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
        auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
        self.auth_url = auth_url

    def refreshURL(self):
        return REFRESH_URL

    def playlistsURL(self):
        return PLAYLISTS_URL

    def playlistTracksURL(self):
        return PLAYLIST_TRACKS_URL

    def playlistTrackFeaturesURL(self):
        return PLAYLIST_TRACK_FEATURES_URL

    def get_accessToken(self, code):
        # Auth Step 2: Requests refresh and access tokens
        auth_payload = {
        "grant_type": "authorization_code",
        "code": str(code),
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        }

        # Auth Step 3: Tokens are Returned to Application
        post_request = requests.post(SPOTIFY_TOKEN_URL, data=auth_payload)
        #unpack token response
        response_data = json.loads(post_request.text)
        access_token = response_data["access_token"]
        refresh_token = response_data["refresh_token"]
        token_type = "Bearer" #always bearer, don't need to grab this each request
        expires_in = response_data["expires_in"]
        newPage = "{}?access_token={}&refresh_token={}&expires_in={}".format(AUTHED_URL, access_token, refresh_token, expires_in)
        return newPage

    def get_refreshToken(self, refresh_token):
        
        #Auth Step 4: get new token with the refresh token
        refresh_payload = {
        "grant_type": "refresh_token",
        "refresh_token": str(refresh_token),
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        }

        post_request_refresh = requests.post(SPOTIFY_TOKEN_URL, data=refresh_payload)
        print(post_request_refresh)
        refreshed_response_data = json.loads(post_request_refresh.text)
        refreshed_access_token = refreshed_response_data["access_token"]
        if refresh_token in refreshed_response_data: #sometimes it doesn't return new refresh token, catch this issue
            refreshed_refresh_token = refreshed_response_data["refresh_token"]
        else: #use old refresh token if that happens
        	refreshed_refresh_token = refresh_token
        refreshed_token_type = refreshed_response_data["token_type"]
        refreshed_expires_in = refreshed_response_data["expires_in"]

        refreshed_parameters = {
        "refreshed_access_token": refreshed_access_token,
        "refreshed_refresh_token": refreshed_refresh_token,
        "expires_in": refreshed_expires_in,
        }

        return refreshed_parameters


class data:
    def __init__(self, access_token):
        self.access_token = access_token

    def profile(self):
        
        global userName
        global dbName

        user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}
        profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
        profile_data = json.loads(profile_response.text)
        userName = profile_data["display_name"]

        #set up db for user
        dbName = str(TODAY) + str(userName)
        db = client[dbName] # Creates db instance per user per date, or reconnects

        #remove old collections to start fresh if used before
        oldCollections = db.list_collection_names()
        iterator = 0
        for h in oldCollections:
            db.drop_collection(oldCollections[iterator])
            iterator += 1


        response = {
        "userName": userName
        }

        return response

    def userPlaylists(self):
        #connect to db
        db = client[dbName]
        collection = db['userPlaylists']

        userPlaylists = []
        
        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}
        api_endpoint = "{}/me/playlists?limit=50".format(SPOTIFY_API_URL)
        
        response = requests.get(api_endpoint, headers=authorization_header)
        response_data = json.loads(response.text)

        playlistCount = response_data['total']
        playlistCount2 = len(response_data['items'])

        for i in range(playlistCount2): #retrieve up to limit worth of playlists
            currentPlayList = response_data['items'][i]
            playlistName = currentPlayList['name']
            uri = currentPlayList['uri']
            playlistName = playlistName.title()
            playlistName = playlistName.replace(" ", "")
            entry = {"uri":uri, "playlistName": playlistName}
            userPlaylists.append(entry)

        if playlistCount > playlistCount2:
            #print('playlist limit exceeded')
            runs = int(round(playlistCount/50)-1)
            offset = 0
            for m in range (runs):
                offset += 50
                new_api_endpoint = "{}/me/playlists?limit=50&offset={}".format(SPOTIFY_API_URL, offset)
                response = requests.get(new_api_endpoint, headers=authorization_header)
                response_data = json.loads(response.text)
                playlistCount3 = len(response_data['items'])

                for i in range(playlistCount3): #retrieve up to limit worth of playlists
                    currentPlayList = response_data['items'][i]
                    playlistName = currentPlayList['name']
                    uri = currentPlayList['uri']
                    playlistName = playlistName.title()
                    playlistName = playlistName.replace(" ", "")
                    entry = {"uri":uri, "playlistName": playlistName}
                    userPlaylists.append(entry)

        results = collection.insert_many(userPlaylists)

        return userPlaylists

    def allPlaylistTracks(self):

    	#retrieve playlist uris
        db = client[dbName]
        collection = db['userPlaylists']
        cursor = collection.find({})

        for document in cursor: #for each playlist in DB
            playlistCollection = db[document['playlistName']]
            currentPlaylistTracks = playlistTracks(document['uri'])
            results = playlistCollection.insert_many(songDataClean) #includes song id, artist info
            print('done with',document['playlistName'], results)
                    
            
        return "OK- Got all Playlist Songs and entered into DB"

    def getTrackFeatures(self, uri):

        #get tracks for 1 playlist
        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}

        #uri = uri
        #print(uri)
        #fields = uri.split(':')
        #songid = fields[2]

        api_endpoint = "{}/audio-features?ids={}".format(SPOTIFY_API_URL,uri)
        response = requests.get(api_endpoint, headers=authorization_header)
        response_data = json.loads(response.text)
            
        return response_data




    def playlistTracks(self, uri):
        #get tracks for 1 playlist
        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}

        #set blank list for all songs in playlist
        songDataClean = []

        uri = uri
        fields = uri.split(':')
        plid = fields[2]

        #get songs in playlist from API
        api_endpoint = "{}/users/{}/playlists/{}/tracks?market=US&fields=items(track(id%2C%20name%2C%20artists))%2Ctotal&limit=100".format(SPOTIFY_API_URL, userName, plid)
        response = requests.get(api_endpoint, headers=authorization_header)

        #unpack response
        response_data = json.loads(response.text)
        data = response_data['items'] #this is a list of dicts        
    
        for i in range(len(data)):
            songInfo = {} 

            trackId = data[i]['track']['id']
            name = data[i]['track']['name']
            name = name.title()
            trackName = name.replace(" ", "")

            songInfo['trackName'] = trackName
            songInfo['trackId'] = trackId

            artistList = data[i]['track']['artists']
            artistNameList = []
            artistIdList = []
            for i in range(len(artistList)):
                artistName = artistList[i]['name']
                artistNameList.append(artistName)
                artistId = artistList[i]['id']
                artistIdList.append(artistId)

            songInfo['artistNames'] = artistNameList
            songInfo['artistIds'] = artistIdList

            songDataClean.append(songInfo)

        #catch the api limit error
        songCount = response_data['total']
        songCount2 = len(response_data['items'])

        offset = 0
        #testing to see if we retrieved all songs
        if songCount > songCount2:
            #print('track limit exceeded')
            runs = int(round(songCount/100)-1)
            for m in range (runs):
                offset += 100
                api_endpoint = "{}/users/{}/playlists/{}/tracks?market=US&fields=items(track(id%2C%20name%2C%20artists))%2Ctotallimit=100&offset={}".format(SPOTIFY_API_URL, userName, plid, offset)
                response = requests.get(api_endpoint, headers=authorization_header)
                response_data = json.loads(response.text)
                data = response_data['items']       

                for i in range(len(data)):
                    songInfo = {} 

                    trackId = data[i]['track']['id']
                    name = data[i]['track']['name']
                    name = name.title()
                    trackName = name.replace(" ", "")

                    songInfo['trackName'] = trackName
                    songInfo['trackId'] = trackId

                    artistList = data[i]['track']['artists']
                    artistNameList = []
                    artistIdList = []
                    for i in range(len(artistList)):
                        artistName = artistList[i]['name']
                        artistNameList.append(artistName)
                        artistId = artistList[i]['id']
                        artistIdList.append(artistId)

                    songInfo['artistNames'] = artistNameList
                    songInfo['artistIds'] = artistIdList

                    songDataClean.append(songInfo)
            
        return songDataClean

