import json
from flask import Flask, request, redirect, g, render_template, jsonify
import requests
from urllib.parse import quote
from pymongo import MongoClient
from datetime import date
from spotifyClient import Spotify

#grab date program is being run
td = date.today()
TODAY = td.strftime("%Y%m%d") ##YYYYMMDD

#set up db instance 
client = MongoClient('localhost', 27017)

with open('config.json') as json_data_file:
    configData = json.load(json_data_file)

#grab the secret variables
CLIENT_ID = configData["spotify"]["cid"]
CLIENT_SECRET = configData["spotify"]["secret"]

#creates instance of app
app = Flask(__name__)

# Spotify URLS
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

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    "show_dialog": "true",
    "client_id": CLIENT_ID
}


@app.route("/")
def index():
    # Auth Step 1: Authorize Spotify User
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


@app.route("/callback/q")
def callback():
    # Auth Step 2: Requests refresh and access tokens
    auth_code = request.args['code']
    auth_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_code),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
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

    return redirect(newPage)

@app.route("/authed")
def authed():

    #grab the tokens from the URL
    access_token = request.args.get("access_token")
    refresh_token = request.args.get("refresh_token")
    token_type = "Bearer" #always bearer, don't need to grab this each request
    expires_in = request.args["expires_in"]

    #Auth Step 4: Refresh Token is used to get refreshed access token
    refreshPage = "{}?refresh_token={}&access_token={}".format(REFRESH_URL, refresh_token, access_token)

    p1 = Spotify(access_token)
    userName = p1.profile()

    #set up db for user
    dbName = str(TODAY) + str(userName)
    db = client[dbName] # Creates db instance per user per date
    #collection=db.test
    #result = collection.insert_one({'name':'test'})

    return render_template("index.html", title='Authenticated', token=access_token, refresh=refresh_token, link=refreshPage, user=userName)

@app.route("/refresh")
def refresh():

    refresh_token = request.args.get("refresh_token")
    #old_access_token = request.args.get("access_token")

    #Auth Step 4: get new token with the refresh token
    refresh_payload = {
        "grant_type": "refresh_token",
        "refresh_token": str(refresh_token),
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

    post_request_refresh = requests.post(SPOTIFY_TOKEN_URL, data=refresh_payload)
    refreshed_response_data = json.loads(post_request_refresh.text)
    #unpack response
    refreshed_response_data = json.loads(post_request_refresh.text)
    refreshed_access_token = refreshed_response_data["access_token"]
    if refresh_token in refreshed_response_data: #sometimes it doesn't return new refresh token, catch this issue
        refreshed_refresh_token = refreshed_response_data["refresh_token"]
    refreshed_token_type = refreshed_response_data["token_type"]
    refreshed_expires_in = refreshed_response_data["expires_in"]

    ret = str(refreshed_access_token)

    return(ret) 


    # # Use the access token to access Spotify API
    # #authorization_header = {"Authorization": "Bearer {}".format(access_token)}
    
    #return jsonify(access_token) #authorization_header

    # # Get user playlist data
    # playlist_api_endpoint = "{}/me/playlists".format(SPOTIFY_API_URL)
    # playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    # playlist_data = json.loads(playlists_response.text)

    # # Combine profile and playlist data to display
    # display_arr = playlist_data["items"]
    # return render_template("index.html", sorted_array=display_arr)

if __name__ == "__main__":
    app.run(debug=True, port=PORT)
