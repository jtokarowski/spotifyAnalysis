import json
from flask import Flask, request, redirect, render_template, jsonify
import requests
from urllib.parse import quote
from pymongo import MongoClient
from datetime import date
from spotifyClient import data, auth

#grab date program is being run
td = date.today()
TODAY = td.strftime("%Y%m%d") ##YYYYMMDD

#set up db instance 
client = MongoClient('localhost', 27017)

#creates instance of app
app = Flask(__name__)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8000

@app.route("/")
def index():
    # Auth Step 1: Authorize Spotify User
    u1 = auth()
    url = u1.auth_url
    return redirect(url)


@app.route("/callback/q")
def callback():
    # Auth Step 2: Requests refresh and access tokens
    t1 = auth()
    newPage = t1.get_accessToken(request.args['code'])
    return redirect(newPage)

@app.route("/authed")
def authed():

    #grab the tokens from the URL
    access_token = request.args.get("access_token")
    refresh_token = request.args.get("refresh_token")
    token_type = "Bearer" #always bearer, don't need to grab this each request
    expires_in = request.args["expires_in"]

    p1 = data(access_token)
    p2 = p1.profile()
    userName = p2.get("userName")
    refreshPage = "{}?refresh_token={}&access_token={}".format(p2.get("REFRESH_URL"), refresh_token, access_token)

    p1.userPlaylists()
    p1.playlistTracks()

    return render_template("index.html", title='Authenticated', token=access_token, refresh=refresh_token, link=refreshPage, user=userName)

@app.route("/refresh")
def refresh():

    r1 = auth()
    r2 = r1.get_refreshToken(request.args.get("refresh_token"))
    access_token = r2.get('refreshed_access_token')
    refresh_token = r2.get('refreshed_refresh_token')
    expires_in = r2.get('refreshed_expires_in')

    p1 = data(access_token)
    p2 = p1.profile()
    userName = p2.get("userName")
    refreshPage = "{}?refresh_token={}&access_token={}".format(p2.get("REFRESH_URL"), refresh_token, access_token)

    return render_template("index.html", title='Refreshed', token=access_token, refresh=refresh_token, link=refreshPage, user=userName)
    

@app.route("/playlists")
def playlists():

    return "ok"
    # Use the access token to access Spotify API
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
