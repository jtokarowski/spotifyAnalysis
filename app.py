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

    r1=auth()

    p1 = data(access_token)
    p2 = p1.profile()
    userName = p2.get("userName")
    refreshPage = "{}?refresh_token={}&access_token={}".format(r1.refreshURL(), refresh_token, access_token)
    playlistsPage = "{}?refresh_token={}&access_token={}&expires_in={}".format(r1.playlistsURL(), refresh_token, access_token, expires_in)

    #p1.userPlaylists()
    #resp = p1.allPlaylistTracks()
    #resp = p1.allTrackFeatures()
    #print(resp)

    return render_template("index.html", title='Authenticated', token=access_token, refresh=refresh_token, link=refreshPage, link2=playlistsPage, user=userName)

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
    refreshPage = "{}?refresh_token={}&access_token={}".format(r1.refreshURL(), refresh_token, access_token)
    playlistsPage = "{}?refresh_token={}&access_token={}&expires_in={}".format(r1.playlistsURL(), refresh_token, access_token, expires_in)

    return render_template("refresh.html", title='Refreshed', token=access_token, refresh=refresh_token, link=refreshPage, link2=playlistsPage, user=userName)
    

@app.route("/playlists")
def playlists():

    #grab the tokens from the URL
    access_token = request.args.get("access_token")
    refresh_token = request.args.get("refresh_token")
    token_type = "Bearer" #always bearer, don't need to grab this each request
    expires_in = request.args["expires_in"]


    r1 = auth()
    refreshPage = "{}?refresh_token={}&access_token={}".format(r1.refreshURL(), refresh_token, access_token)
    playlistsPage = "{}?refresh_token={}&access_token={}&expires_in={}".format(r1.playlistsURL(), refresh_token, access_token, expires_in)

    p1 = data(access_token)
    p1.profile #create class instance that grabs userName
    response = p1.userPlaylists()

    #build the link for each playlist
    array = []
    for playlist in response:
        item = {}
        item['playlistName'] = playlist['playlistName']
        item['link'] = "{}?refresh_token={}&access_token={}&expires_in={}&uri={}&title={}".format(r1.playlistTracksURL(), refresh_token, access_token, expires_in, playlist['uri'], playlist['playlistName'])
        array.append(item)
    

    return render_template("playlists.html", title='Playlists', token=access_token, refresh=refresh_token, link=refreshPage, sorted_array=array)

@app.route("/playlistTracks")
def playlistTracks():

    #grab the tokens from the URL
    access_token = request.args.get("access_token")
    refresh_token = request.args.get("refresh_token")
    token_type = "Bearer" #always bearer, don't need to grab this each request
    expires_in = request.args["expires_in"]
    uri = request.args.get("uri")
    name = request.args.get('title')

    r1 = auth()
    refreshPage = "{}?refresh_token={}&access_token={}".format(r1.refreshURL(), refresh_token, access_token)
    playlistsPage = "{}?refresh_token={}&access_token={}&expires_in={}".format(r1.playlistsURL(), refresh_token, access_token, expires_in)
    p1 = data(access_token)

    response = p1.getPlaylistTracks(uri)

    #build the link for each song
    array = []
    for song in response:
        item = {}
        item['trackName'] = song['trackName']
        item['link'] = "{}?refresh_token={}&access_token={}&expires_in={}&uri={}&trackName={}".format(r1.playlistTrackFeaturesURL(), refresh_token, access_token, expires_in, song['trackId'], song['trackName'])
        array.append(item)

    return render_template("playlistTracks.html", title='PlaylistTracks', pname=name, token=access_token, refresh=refresh_token, link=refreshPage, sorted_array=array)

@app.route("/playlistTrackFeatures")
def playlistTrackFeatures():

    access_token = request.args.get("access_token")
    refresh_token = request.args.get("refresh_token")
    token_type = "Bearer" #always bearer, don't need to grab this each request
    expires_in = request.args["expires_in"]

    trackName = request.args.get("trackName")
    
    uri = []
    uri.append(request.args.get("uri"))
    
    r1 = auth()
    refreshPage = "{}?refresh_token={}&access_token={}".format(r1.refreshURL(), refresh_token, access_token)
    playlistsPage = "{}?refresh_token={}&access_token={}&expires_in={}".format(r1.playlistsURL(), refresh_token, access_token, expires_in)
    
    p1 = data(access_token)
    array = []
    trackAudioFeatures = p1.getTrackFeatures(uri)

    unpacked = trackAudioFeatures['audio_features'] #remove outer layer of dict
    for item in unpacked:
        array.append(item)


    #convert this to plot a graph of the audio features

    return render_template("playlistTrackFeatures.html", title='PlaylistTrackFeatures', token=access_token, refresh=refresh_token, link=refreshPage, link2=playlistsPage, sorted_array=array, tname=trackName)

    
if __name__ == "__main__":
    app.run(debug=True, port=PORT)
