from __future__ import print_function
import sys
import requests
import json
import time
from datetime import date
import os

#import keys from environment
CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
ENV = os.environ.get('ENV')

#URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
if ENV == 'dev':
    CLIENT_SIDE_URL = "http://127.0.0.1"
    PORT = 8000
    REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
    AUTHED_URL = "{}:{}/authed".format(CLIENT_SIDE_URL, PORT)
    REFRESH_URL = "{}:{}/refresh".format(CLIENT_SIDE_URL, PORT)
    ANALYSIS_URL = "{}:{}/analysis".format(CLIENT_SIDE_URL, PORT)
    PLAYLISTS_URL = "{}:{}/playlists".format(CLIENT_SIDE_URL, PORT)
    PLAYLIST_TRACKS_URL = "{}:{}/playlistTracks".format(CLIENT_SIDE_URL, PORT)
    PLAYLIST_TRACK_FEATURES_URL = "{}:{}/playlistTrackFeatures".format(CLIENT_SIDE_URL, PORT)
elif ENV == 'heroku':
    CLIENT_SIDE_URL = "https://musicincontext.herokuapp.com"
    REDIRECT_URI = "{}/callback/q".format(CLIENT_SIDE_URL)
    AUTHED_URL = "{}/authed".format(CLIENT_SIDE_URL)
    REFRESH_URL = "{}/refresh".format(CLIENT_SIDE_URL)
    ANALYSIS_URL = "{}/analysis".format(CLIENT_SIDE_URL)
    PLAYLISTS_URL = "{}/playlists".format(CLIENT_SIDE_URL)
    PLAYLIST_TRACKS_URL = "{}/playlistTracks".format(CLIENT_SIDE_URL)
    PLAYLIST_TRACK_FEATURES_URL = "{}/playlistTrackFeatures".format(CLIENT_SIDE_URL)


SCOPE = "playlist-modify-private,playlist-modify-public,playlist-read-collaborative,playlist-read-private,user-read-recently-played,user-top-read"
STATE = "" #Should create a random string generator here to make a new state for each request

#grab date program is being run
td = date.today()
TODAY = td.strftime("%Y%m%d") ##YYYYMMDD

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
        url_args = "&".join(["{}={}".format(key, val) for key, val in auth_query_parameters.items()])
        auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
        self.auth_url = auth_url

    def refreshURL(self):
        return REFRESH_URL

    def playlistsURL(self):
        return PLAYLISTS_URL

    def analysisURL(self):
        return ANALYSIS_URL

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

    def refreshAccessToken(self, refresh_token):
        
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
        "access_token": refreshed_access_token,
        "refresh_token": refreshed_refresh_token,
        "expires_in": refreshed_expires_in,
        }

        return refreshed_parameters

class create:
    def __init__(self, access_token):
        self.access_token = access_token

    def newPlaylist(self, userid, playlistName, description=None):

        if description is None:
            description = "None"

        user_playlists_endpoint = "{}/users/{}/playlists".format(SPOTIFY_API_URL, userid)
        
        authorization_header = {"Authorization": "Bearer {} Content-Type: application/json".format(self.access_token)}
        request_body = {"name":playlistName,"public":False,"description":description}
        response = requests.post(user_playlists_endpoint, headers=authorization_header, json=request_body)

        response_data = json.loads(response.text)

        return response_data

    def addSongs(self, plid, uriList):
        if type(uriList) == list:
            uriList = ",".join(uriList)

        user_playlist_endpoint = "{}/playlists/{}/tracks?uris={}".format(SPOTIFY_API_URL, plid,uriList)
        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}
        response = requests.post(user_playlist_endpoint, headers=authorization_header)

        return response

class data:
    def __init__(self, access_token):
        self.access_token = access_token

    def profile(self):
        
        global userName

        user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}
        profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
        profile_data = json.loads(profile_response.text)

        uri = profile_data["uri"]
        fields = uri.split(':')
        userName = fields[2]
        followers = profile_data["followers"]
        images = profile_data["images"]

        #strips username to avoid error if user is from FB and name has a space, or other weird char
        userName = str(userName)
        newstr = ""
        for char in userName:
            if char == ' ':
                continue
            elif char == '.':
                continue
            elif char == ',':
                continue
            else:
                newstr += char

        response = {
        "userName": userName,
        "images": images,
        "followers": followers
        }

        return response

    def userPlaylists(self):

        userPlaylists = []
        
        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}
        api_endpoint = "{}/me/playlists?limit=50".format(SPOTIFY_API_URL)
        
        response = requests.get(api_endpoint, headers=authorization_header)
        response_data = json.loads(response.text)

        userPlaylists.extend(self.reformat_playlists(response_data))

        playlistCount = response_data['total']
        playlistCount2 = len(response_data['items'])

        if playlistCount > playlistCount2:
            #print('playlist limit exceeded')
            runs = int(round(playlistCount/50)-1)
            offset = 0
            for m in range (runs):
                offset += 50
                new_api_endpoint = "{}/me/playlists?limit=50&offset={}".format(SPOTIFY_API_URL, offset)
                response = requests.get(new_api_endpoint, headers=authorization_header)
                response_data2 = json.loads(response.text)
                userPlaylists.extend(self.reformat_playlists(response_data2))


        #results = collection.insert_many(userPlaylists)

        return userPlaylists

    def reformat_playlists(self, data):

        playlists = []
        playlistCount = data['total']
        playlistCount2 = len(data['items'])

        for i in range(playlistCount2): #retrieve up to limit worth of playlists
            currentPlayList = data['items'][i]
            playlistName = currentPlayList['name']
            uri = currentPlayList['uri']
            playlistName = playlistName.title()
            playlistName = playlistName.replace(" ", "")
            entry = {"uri":uri, "playlistName": playlistName}
            playlists.append(entry)

        return playlists

    def getTracks(self, songs):

        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}

        output = []

        #API limit is 50 ids per call
        n = 25
        for i in range(0, len(songs), n):  
            listToSend = songs[i:i + n]
            ids = ",".join(listToSend)
            print(len(listToSend))

            api_endpoint = "{}/tracks?ids={}".format(SPOTIFY_API_URL,ids)
            response = requests.get(api_endpoint, headers=authorization_header)
            response_data = json.loads(response.text) 
            try:
                output.extend(response_data['tracks'])
            except:
                print(response_data)
                input()

        return output

    def trackFeatures(self, songs):

        d1 = data(self.access_token)
        songList = [] #new tracklist for each playlist
        uriList = [] #list for URIs to send to retrieval
        artistIdList = [] #list of artist ids to send for genre
        
        for song in songs: #within playlist

            songList.append(song)
            if song == None:
                uriList.append('None')
            elif song['trackId'] == None:
                uriList.append('None')
            else:
                uriList.append(song['trackId'])
                artistIdList.extend(song['artistIds'])

        set_artistids = set(artistIdList)
        unique_artistids = list(set_artistids)

        #break up by spotify artist id limita
        allGenresList = []
        m = 50
        for j in range(0, len(unique_artistids), m):  
            listToSend = unique_artistids[j:j + m]
            response = d1.getArtistGenres(listToSend)
            allGenresList.extend(response)

        #form dict from resulting lists
        genremap = {}

        for l in range(len(unique_artistids)):
            genremap[unique_artistids[l]] = allGenresList[l]

        # breaking up song ids by spotify limit
        allFeaturesList = []
        n = 100
        for i in range(0, len(uriList), n):  
            listToSend = uriList[i:i + n]
            response = d1.getTrackFeatures(listToSend)
            allFeaturesList.extend(response['audio_features'])    

        for k in range(len(songList)):
            currentSong = songList[k]
            if currentSong ==None:
                continue
            currentSong['audioFeatures'] = allFeaturesList[k]
            if len(currentSong['artistIds'])>1:
                currentSong['genres'] = []
                for z in range(len(currentSong['artistIds'])):
                    g = genremap[currentSong['artistIds'][z]]
                    currentSong['genres'].extend(g)
            else:
                currentSong['genres'] = genremap[currentSong['artistIds'][0]]

        return songList
        #return "done getting features for songs in " + str(collection)

    def getTrackFeatures(self, uri):
    #get audio features for 1 or more tracks (max of 100)

        if uri == None:
            return
        
        elif len(uri) ==0:
            return

        elif len(uri) == 1:
            uri = uri[0]
        else:
            uri = ",".join(uri)

        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}

        api_endpoint = "{}/audio-features?ids={}".format(SPOTIFY_API_URL,uri)
        response = requests.get(api_endpoint, headers=authorization_header)
        response_data = json.loads(response.text)
            
        return response_data

    def getAudioAnalysis(self, uri):

        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}

        api_endpoint = "{}/audio-analysis/{}".format(SPOTIFY_API_URL,uri)
        response = requests.get(api_endpoint, headers=authorization_header)
        response_data = json.loads(response.text)
            
        return response_data

    def getPlaylistTracks(self, uri):
        #get tracks for 1 playlist
        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}

        if ":" in uri:
            fields = uri.split(':')
            plid = fields[2]
        else:
            plid = uri

        #set blank list for all songs in playlist
        songDataClean = []

        #get songs in playlist from API
        api_endpoint = "{}/users/{}/playlists/{}/tracks?market=US&fields=items(track(id%2C%20name%2C%20artists))%2Ctotal&limit=100".format(SPOTIFY_API_URL, userName, plid)
        response = requests.get(api_endpoint, headers=authorization_header)

        #unpack response
        response_data = json.loads(response.text)
        data = response_data['items'] #this is a list of dicts  

        ###improve efficiency here      
        for i in range(len(data)):
            songDataClean.append(self.cleanSongData(data[i]))

        #catch the api limit error
        songCount = response_data['total']
        songCount2 = len(response_data['items'])
        offset = 0

        if songCount > songCount2:
            runs = int(round(songCount/100)-1)
            for j in range (runs):
                offset += 100
                api_endpoint = "{}/users/{}/playlists/{}/tracks?market=US&fields=items(track(id%2C%20name%2C%20artists))%2Ctotallimit=100&offset={}".format(SPOTIFY_API_URL, userName, plid, offset)
                response = requests.get(api_endpoint, headers=authorization_header)
                response_data = json.loads(response.text)
                data = response_data['items']     

                for k in range(len(data)):
                    songDataClean.append(self.cleanSongData(data[k]))  
            
        return songDataClean

    def cleanSongData(self, song):
    #reformats song information to drop unecessary data
        
        if song == None:
            return None

        songInfo = {} 
        try:
            trackId = song['track']['id']
            name = song['track']['name']
            artistList = song['track']['artists']
        except:
            trackId = song['id']
            name = song['name']
            artistList = song['artists']
        
        name = name.title()
        trackName = name.replace(" ", "")

        songInfo['trackName'] = trackName
        songInfo['trackId'] = trackId

        
        artistNameList = []
        artistIdList = []
        for i in range(len(artistList)):
            artistName = artistList[i]['name']
            artistNameList.append(artistName)
            artistId = artistList[i]['id']
            artistIdList.append(artistId)
        songInfo['artistNames'] = artistNameList
        songInfo['artistIds'] = artistIdList
        
        return songInfo

    def getGenreSeeds(self):

        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}

        api_endpoint = "{}/recommendations/available-genre-seeds".format(SPOTIFY_API_URL)
        response = requests.get(api_endpoint, headers=authorization_header)
        response_data = json.loads(response.text)     

        return response_data['genres']

    def getArtistGenres(self, artistids):

        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}

        if isinstance(artistids, list):
            if len(artistids)>1:
                genres = []
                #turn the list into comma separated string
                commaSep_artistids = ",".join(artistids)
                api_endpoint = "{}/artists?ids={}".format(SPOTIFY_API_URL, commaSep_artistids)
                response = requests.get(api_endpoint, headers=authorization_header)
                response_data = json.loads(response.text) 
                for i in range(len(artistids)):
                    genres.append(response_data['artists'][i]['genres'])
            
                return genres

        api_endpoint = "{}/artists?ids={}".format(SPOTIFY_API_URL, artistids[0])
        response = requests.get(api_endpoint, headers=authorization_header)
        response_data = json.loads(response.text) 

        genres = response_data['artists'][0]['genres'] 
        
        return genres

    def getRecentSongs(self):

        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}
        api_endpoint = "{}/me/player/recently-played?limit=50".format(SPOTIFY_API_URL)
        response = requests.get(api_endpoint, headers=authorization_header)
        response_data = json.loads(response.text) 

        idlist = []
        for i in range(len(response_data['items'])):
            idlist.append(response_data['items'][i]['track']['id'])

        return idlist
        #the response_data['next'] field provides the endpoint to hit for next 50 songs
        
    def getMyTop(self, topType, term, limit):

        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}
        api_endpoint = "{}/me/top/{}?time_range={}&limit={}".format(SPOTIFY_API_URL,topType,term, limit)
        response = requests.get(api_endpoint, headers=authorization_header)
        response_data = json.loads(response.text) 

        cleaned_data = []
        if topType == 'tracks':
            for track in response_data['items']:
                clean = {}
                clean['track_id'] = track['id']
                cleaned_data.append(clean)
        else:
            for artist in response_data['items']:
                clean = {}
                clean['artist_id'] = artist['id']
                clean['genres'] = artist['genres']
                cleaned_data.append(clean)

        return cleaned_data
   
    def getTop50(self):

        #static link for global top50
        results = self.getPlaylistTracks("spotify:playlist:37i9dQZEVXbMDoHDwVN2tF")
        
        return results

    def getRecommendations(self, targets=None, market=None, limit=None, seed_artists=None, seed_genres=None, seed_tracks=None):

        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}
        api_endpoint = "{}/recommendations?".format(SPOTIFY_API_URL)

        if market:
            api_endpoint+="market={}".format(market)
        else:
            api_endpoint+="market=US"

        if not limit:
            limit = 20

        api_endpoint+="&limit={}".format(limit)

        #SEEDS
        if seed_artists:
            api_endpoint+="&seed_artists={}".format(seed_artists)
        if seed_genres:
            api_endpoint+="&seed_genres={}".format(seed_genres)
        if seed_tracks:
            api_endpoint+="&seed_tracks={}".format(seed_tracks)

        #TARGETS, MINS, MAXS
        if targets:
            for attribute in ["acousticness", "danceability", "duration_ms",
                           "energy", "instrumentalness", "key", "liveness",
                           "loudness", "mode", "popularity", "speechiness",
                           "tempo", "time_signature", "valence"]:
                for prefix in ["min_", "max_", "target_"]:
                    param = prefix + attribute
                    if param in targets:
                        api_endpoint+="&{}={}".format(param,targets[param])
        

        response = requests.get(api_endpoint, headers=authorization_header)
        response_data = json.loads(response.text)

        output = []
        for song in response_data['tracks']:
            output.append(self.cleanSongData(song))

        print(response_data['seeds'])

        return output

    def search(self,name, artist,searchType, limit=None):

        #could overlay simple ML here to find best match to our track
        #eventually want to feed in artists separate from track name
        #for now, list of keywords (artist, songname) shoudl be ok

        #could add flexibility to search for differen things, for now just track

        #q=album:gold%20artist:abba&type=album
        #track_str = 'Henry Dark - Beirut'
        #need to encode the keywords

        if not limit:
            limit = 1

        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}

        api_endpoint = "{}/search?q={}+artist:{}&type={}&limit={}&market=US".format(SPOTIFY_API_URL,name,artist,searchType,limit)
        response = requests.get(api_endpoint, headers=authorization_header)
        if response.status_code ==429:
            try:
                time.sleep(response.headers['Retry-After'])
            except:
                time.sleep(10)
            
            response = requests.get(api_endpoint, headers=authorization_header)

        try:
            response_data = json.loads(response.text) 
        except:
            response_data = None

        return response_data







