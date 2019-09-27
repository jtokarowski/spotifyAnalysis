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
        db = client[dbName] # Creates db instance per user per date

        response = {
        "userName": userName,
        "REFRESH_URL": REFRESH_URL
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
            #name the collection based on the playlist it is retrieving from
            playlistName = playlistName.title()
            playlistName = playlistName.replace(" ", "")

            entry = {"uri":uri, "playlistName": playlistName}
            userPlaylists.append(entry)

            #print(i, playlistName)
            #collection = db[playlistName]

        if playlistCount > playlistCount2:
            #print('playlist limit exceeded')
            runs = int(round(playlistCount/50))
            offset = 0
            for m in range (runs):
                offset += 50
                new_api_endpoint = "{}/me/playlists?limit=50&offset={}".format(SPOTIFY_API_URL, offset)
                response = requests.get(new_api_endpoint, headers=authorization_header)
                response_data = json.loads(response.text)
                playlistCount2 = len(response_data['items'])

                for i in range(playlistCount2): #retrieve up to limit worth of playlist
                    currentPlayList = response_data['items'][i]
                    playlistName = currentPlayList['name']
                    uri = currentPlayList['uri']
                    #name the collection based on the playlist it is retrieving from
                    playlistName = playlistName.title()
                    playlistName = playlistName.replace(" ", "")
                    entry = {"uri":uri, "playlistName": playlistName}
                    userPlaylists.append(entry)

        results = collection.insert_many(userPlaylists)

        return

    def playlistTracks(self):

        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}

    	#retrieve playlist uris
        db = client[dbName]
        collection = db['userPlaylists']
        cursor = collection.find({})

        for document in cursor: #for each playlist in DB

            playlistCollection = db[document['playlistName']]
            print(document['playlistName'])
            plid = document['uri']
            fields = plid.split(':')
            #feed uri to spotify tracks request
            api_endpoint = "{}/users/{}/playlists/{}/tracks?market=US&fields=items(track(id%2C%20name%2C%20artists))&limit=100".format(SPOTIFY_API_URL, userName, fields[2])
            response = requests.get(api_endpoint, headers=authorization_header)
            response_data = json.loads(response.text)
            print(response_data) #need id, artists and respective ids
            input("Press Enter to continue...")

            #unpack response

            #insert into db

            #catch the api limit error
            songCount = response_data['total']
            songCount2 = len(response_data['items']) #this corrects for 100 limit

            offset = 0
            #testing to see if we retrieved all songs
            if songCount > songCount2:
                print('playlist track limit exceeded')
                runs = int(round(songCount/100))
                for m in range (runs):
                    offset += 100
                    api_endpoint = "{}/users/{}/playlists/{}/tracks?market=US&fields=items(track(id%2C%20name%2C%20artists))limit=100&offset={}".format(SPOTIFY_API_URL, userName, fields[2],offset)
                    response = requests.get(api_endpoint, headers=authorization_header)
                    response_data = json.loads(response.text)
                    data = response_data['items']
                    print(data)
                    input("Press Enter to continue...")

                    #unpack response

                    #insert into db
                    
            
            #input("Press Enter to continue...")


    	#mongo insert many
        return
