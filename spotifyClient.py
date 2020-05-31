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

    def visualizationURL(self):
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

    def checkAPIStatus(self):
        #TODO set up a helper that checks response code and acts accoridngly 
        #ex. if it's a timeout problem, resend request

        return "OK"

    def idToURI(self, type, id):
        if type not in ["playlist", "track", "artist"]:
            return "Invalid type"
        # set up the correct format
        return "spotify:{}:{}".format(type, id)

    def URItoID(self, URI):
        #strip format to just the ID
        splitURI = URI.split(":")
        return splitURI[2]


    def profile(self):
        #https://developer.spotify.com/documentation/web-api/reference/users-profile/
        
        global userName

        user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}
        profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
        profileData = json.loads(profile_response.text)

        userName = self.URItoID(profileData["uri"])
        followers = profileData["followers"]
        images = profileData["images"]

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

        userInfoClean = {
        "userName": userName,
        "images": images,
        "followers": followers
        }

        return userInfoClean

    def currentUserPlaylists(self):
        #https://developer.spotify.com/documentation/web-api/reference/playlists/get-a-list-of-current-users-playlists/

        currentUserPlaylists = []
        
        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}
        apiEndpoint = "{}/me/playlists?limit=50".format(SPOTIFY_API_URL)
        
        currentUserPlaylistsResponse = requests.get(apiEndpoint, headers=authorization_header)
        responseData = json.loads(currentUserPlaylistsResponse.text)
        currentUserPlaylists.extend(self.reformatPlaylists(responseData))

        if responseData['total'] > len(responseData['items']):
            runs = int(round(responseData['total']/50)-1)
            offset = 0

            for i in range(runs):
                offset += 50
                newApiEndpoint = "{}/me/playlists?limit=50&offset={}".format(SPOTIFY_API_URL, offset)
                currentUserPlaylistsResponse = requests.get(newApiEndpoint, headers=authorization_header)
                responseData = json.loads(currentUserPlaylistsResponse.text)
                currentUserPlaylists.extend(self.reformatPlaylists(responseData))

        return currentUserPlaylists

    def reformatPlaylists(self, rawPlaylists):
        #cleans up playlists retrieved by currentUserPlaylists method
        cleanPlaylists = []

        for rawPlaylist in rawPlaylists['items']:
            cleanPlaylists.append({"uri":rawPlaylist['uri'], "playlistName": rawPlaylist['name']})

        return cleanPlaylists

    def getTracks(self, trackIds):
        #https://developer.spotify.com/documentation/web-api/reference/tracks/get-several-tracks/
        apiLimit = 50
        authorizationHeader = {"Authorization": "Bearer {}".format(self.access_token)}

        if not isinstance(trackIds, list):
            trackIds = [trackIds]

        #define output
        outputTrackData = []
        
        for i in range(0, len(trackIds), apiLimit):  
            selectedTrackIds = trackIds[i:i + apiLimit]
            selectedTrackIdsString = ",".join(selectedTrackIds)

            apiEndpoint = "{}/tracks?ids={}".format(SPOTIFY_API_URL,selectedTrackIdsString)
            tracksResponse = requests.get(apiEndpoint, headers=authorizationHeader) 
            
            if tracksResponse.status_code != 200:
                return "API Error {}".format(tracksResponse.status_code)
            else:
                responseData = json.loads(tracksResponse.text)
                outputTrackData.extend(responseData['tracks'])

        return outputTrackData

    
    def getAudioAnalysis(self, trackURI):
        #https://developer.spotify.com/documentation/web-api/reference/tracks/get-audio-analysis/
        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}
        if ":" in trackURI:
            trackID = self.URItoID(trackURI)
        else:
            trackID = trackURI

        api_endpoint = "{}/audio-analysis/{}".format(SPOTIFY_API_URL,trackID)
        audioAnalysisResponse = requests.get(api_endpoint, headers=authorization_header)
        response_data = json.loads(audioAnalysisResponse.text)
            
        return response_data

    def getPlaylistTracks(self, playlistURI):
        #https://developer.spotify.com/documentation/web-api/reference/playlists/get-playlists-tracks/
        #get tracks for 1 playlist
        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}

        if ":" in playlistURI:
            playlistID = self.URItoID(playlistURI)
        else:
            playlistID = playlistURI

        #set blank list for all songs in playlist
        playlistTracks = []

        #get songs in playlist from API
        api_endpoint = "{}/users/{}/playlists/{}/tracks?market=US&fields=items(track(id%2C%20name%2C%20artists))%2Ctotal&limit=100".format(SPOTIFY_API_URL, userName, playlistID)
        playlistTracksResponse = requests.get(api_endpoint, headers=authorization_header)

        #unpack response
        playlistTracksResponseData = json.loads(playlistTracksResponse.text)
        playlistTracks = playlistTracksResponseData['items'] #this is a list of dicts  

        #catch the api limit error
        offset = 0
        if playlistTracksResponseData['total'] > len(playlistTracksResponseData['items']):
            runs = int(round(playlistTracksResponseData['total']/100)-1)
            for j in range (runs):
                offset += 100
                api_endpoint = "{}/users/{}/playlists/{}/tracks?market=US&fields=items(track(id%2C%20name%2C%20artists))%2Ctotallimit=100&offset={}".format(SPOTIFY_API_URL, userName, playlistID, offset)
                playlistTracksResponse = requests.get(api_endpoint, headers=authorization_header)
                playlistTracksResponseData = json.loads(playlistTracksResponse.text)
                playlistTracks.extend(playlistTracksResponseData['items'])

        return playlistTracks

    def cleanTrackData(self, rawTracks):
    #reformats track information to drop unecessary data
        if rawTracks == None or len(rawTracks) == 0:
            return "Error: no track provided"
    
        elif not isinstance(rawTracks, list):
            rawTracks = [rawTracks]

        cleanTracks= []

        for track in rawTracks:
            cleanTrackData = {} 
            cleanTrackData['trackName'] = track['track']['name'].title()
            cleanTrackData['trackID'] = track['track']['id']
            
            artistNameList = []
            artistIdList = []
            for artist in track['track']['artists']:
                artistNameList.append(artist['name'])
                artistIdList.append(artist['id'])
                
            cleanTrackData['artistNames'] = artistNameList
            cleanTrackData['artistIDs'] = artistIdList
            cleanTrackData['isClean'] = True

            cleanTracks.append(cleanTrackData)
        
        return cleanTracks

    def getGenreSeeds(self):

        authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}

        api_endpoint = "{}/recommendations/available-genre-seeds".format(SPOTIFY_API_URL)
        response = requests.get(api_endpoint, headers=authorization_header)
        response_data = json.loads(response.text)     

        return response_data['genres']


    def getRecentTracks(self):
        #https://developer.spotify.com/documentation/web-api/reference/player/get-recently-played/
        apiLimit = 50

        authorizationHeader = {"Authorization": "Bearer {}".format(self.access_token)}
        apiEndpoint = "{}/me/player/recently-played?limit=50".format(SPOTIFY_API_URL)
        
        response = requests.get(apiEndpoint, headers=authorizationHeader)
        responseData = json.loads(response.text) 

        idlist = []
        for i in range(len(responseData['items'])):
            idlist.append(responseData['items'][i]['track']['id'])

        return idlist
        #the response_data['next'] field provides the endpoint to hit for next 50 tracks
        #TODO: add option to continue grabbing older tracks
        
    def getMyTop(self, topType, term, limit):
        #https://developer.spotify.com/documentation/web-api/reference/personalization/get-users-top-artists-and-tracks/

        authorizationHeader = {"Authorization": "Bearer {}".format(self.access_token)}
        apiEndpoint = "{}/me/top/{}?time_range={}&limit={}".format(SPOTIFY_API_URL,topType,term, limit)
        response = requests.get(apiEndpoint, headers=authorizationHeader)
        responseData = json.loads(response.text) 

        cleanedData = []
        if topType == 'tracks':
            for track in responseData['items']:
                cleanTrack = {}
                cleanTrack['trackID'] = track['id']
                cleanedData.append(cleanTrack)
        else:
            for artist in responseData['items']:
                cleanArtist = {}
                cleanArtist['artistID'] = artist['id']
                cleanArtist['genres'] = artist['genres']
                cleanedData.append(cleanArtist)

        return cleanedData
   
    def getTop50(self):
        #static link for global top50
        return getPlaylistTracks(self, "spotify:playlist:37i9dQZEVXbMDoHDwVN2tF"):

    def getRecommendations(self, targets=None, market=None, apiLimit=None, seedArtists=None, seedGenres=None, seedTracks=None):
        #https://developer.spotify.com/documentation/web-api/reference/browse/get-recommendations/

        #TODO: add funcitonality to examine pool size before and after filters

        authorizationHeader = {"Authorization": "Bearer {}".format(self.access_token)}
        apiEndpoint = "{}/recommendations?".format(SPOTIFY_API_URL)

        if market:
            apiEndpoint+="market={}".format(market)
        else:
            apiEndpoint+="market=US"

        if not apiLimit:
            apiLimit = 20

        apiEndpoint+="&limit={}".format(apiLimit)

        #SEEDS
        if seedArtists:
            apiEndpoint+="&seed_artists={}".format(seedArtists)
        if seedGenres:
            apiEndpoint+="&seed_genres={}".format(seedGenres)
        if seedTracks:
            apiEndpoint+="&seed_tracks={}".format(seedTracks)

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
        responseData = json.loads(response.text)

        #clean response data
        output = []
        for song in responseData['tracks']:
            output.append(self.cleanTrackData(song))

        return output

    def search(self, name, artist, searchType, limit=None):
        #https://developer.spotify.com/documentation/web-api/reference/search/search/

        #could overlay simple ML here to find best match to our track
        #eventually want to feed in artists separate from track name
        #for now, list of keywords (artist, songname) shoudl be ok

        #could add flexibility to search for differen things, for now just track

        #q=album:gold%20artist:abba&type=album
        #track_str = 'Henry Dark - Beirut'
        #need to encode the keywords

        if not limit:
            limit = 1

        authorizationHeader = {"Authorization": "Bearer {}".format(self.access_token)}

        apiEndpoint = "{}/search?q={}+artist:{}&type={}&limit={}&market=US".format(SPOTIFY_API_URL,name,artist,searchType,limit)
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
    
    def getArtistData(self, artistIDs):
        #https://developer.spotify.com/documentation/web-api/reference/artists/get-artist/
        apiLimit = 50

        if not isinstance(artistIDs, list):
            artistIDs = [artistIDs]
    
        authorizationHeader = {"Authorization": "Bearer {}".format(self.access_token)}
        
        artistData = []

        for i in range(0, len(artistIDs), apiLimit):
            artistIDString = ",".join(artistIDs[i:i+apiLimit])
            apiEndpoint = "{}/artists?ids={}".format(SPOTIFY_API_URL, artistIDString)
            artistsResponse = requests.get(apiEndpoint, headers=authorizationHeader)  
        
            if artistsResponse.status_code != 200:
                return "API Error {}".format(artistsResponse.status_code)
            else:
                responseData = json.loads(artistsResponse.text)
                artistData.extend(responseData['artists'])

        return artistData  

    def extractGenres(self, artistData):
        #extract genres from single artist retrieved or list of artists
        genresByArtist = {}
        for artist in artistData:
            genresByArtist[artist['id']] = artist['genres']

        return genresByArtist #dict by ID
    
    def getAudioFeatures(self, incomingTracks):
        #Must send this method clean track/s
        #https://developer.spotify.com/documentation/web-api/reference/tracks/get-several-audio-features/
        apiLimit = 100

        authorizationHeader = {"Authorization": "Bearer {}".format(self.access_token)}
        
        artistIDs = []
        trackIDs = []
        
        #convert to list
        if not isinstance(incomingTracks, list):
            incomingTracks = [incomingTracks]

        #pull out relevant identifiers
        for track in incomingTracks:
            artistIDs.extend(track['artistIDs'])
            trackIDs.append(track['trackID'])

        #create dict of IDs and and genres
        artistData = self.getArtistData(artistIDs)
        genresByArtistID = self.extractGenres(artistData)

        #define output + retrieve in blocks of 50 at a time
        audioFeaturesData = []
        for i in range(0, len(trackIDs), apiLimit):
            selectedTrackIDs = trackIDs[i:i+apiLimit]
            trackIDString = ",".join(selectedTrackIDs)
            apiEndpoint = "{}/audio-features/?ids={}".format(SPOTIFY_API_URL, trackIDString)
            audioFeaturesResponse = requests.get(apiEndpoint, headers=authorizationHeader)  
        
            if audioFeaturesResponse.status_code != 200:
                return "API Error {}".format(audioFeaturesResponse.status_code)
            else:
                responseData = json.loads(audioFeaturesResponse.text)
                
                audioFeaturesData.extend(responseData['audio_features'])
        
        #reformat data for export
        trackDataComplete = []
        for j in range(len(incomingTracks)):
            completeTrack = incomingTracks[j]
            completeTrack['audioFeatures'] = audioFeaturesData[j]
            completeTrack['genres'] = []
            for artistID in completeTrack['artistIDs']:
                completeTrack['genres'].extend(genresByArtistID[artistID]) 
            trackDataComplete.append(completeTrack)

        return trackDataComplete 

        