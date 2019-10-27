import json
from flask import Flask, request, redirect, render_template, jsonify
import requests
from urllib.parse import quote
from pymongo import MongoClient
from datetime import date
from spotifyClient import data, auth, create
from statisticalAnalysis import stats
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
from plots import plotting
from flask_wtf import FlaskForm
from wtforms import widgets, SelectMultipleField

SECRET_KEY = 'development'

#grab date program is being run
td = date.today()
TODAY = td.strftime("%Y%m%d") ##YYYYMMDD

#set up db instance 
client = MongoClient('localhost', 27017)

#creates instance of app
app = Flask(__name__)
app.config.from_object(__name__)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8000

@app.route("/",methods=["GET","POST"])
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

@app.route("/authed", methods=["GET","POST"])
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
    image = p2.get("images")
    if len(image) == 0:
        imgurl = 'N/A'
    else:
        imgurl = image[0]['url']
        
    followers = p2.get("followers")
    followCount = followers['total']
    db = p2.get("dbName")

    refreshPage = "{}?refresh_token={}&access_token={}".format(r1.refreshURL(), refresh_token, access_token)
    playlistsPage = "{}?refresh_token={}&access_token={}&expires_in={}".format(r1.playlistsURL(), refresh_token, access_token, expires_in)
    analysisPage = "{}?refresh_token={}&access_token={}&expires_in={}".format(r1.analysisURL(), refresh_token, access_token, expires_in)

    response = p1.userPlaylists()

    #build the link for each playlist
    playlists = []
    for playlist in response:
        pl = (playlist['uri'],playlist['playlistName'])
        playlists.append(pl)

    #set up the checkbox classes
    class MultiCheckboxField(SelectMultipleField):
        widget = widgets.ListWidget(prefix_label=False)
        option_widget = widgets.CheckboxInput()

    class SimpleForm(FlaskForm):
        # create a list of value/description tuples
        files = [(x, y) for x,y in playlists]
        playlistSelections = MultiCheckboxField('Label', choices=files)

    form = SimpleForm()
    if form.validate_on_submit():
        formData = form.playlistSelections.data
        dataString = ",".join(formData)
        analysisPageSelections = "{}&data={}".format(analysisPage, dataString)
        return redirect(analysisPageSelections) # need to redirect to analysis, including necessary keys
    else:
        print(form.errors)

    return render_template("index2.html", title='Home', user=userName, token=access_token, refresh=refresh_token, followCount=followCount, link=refreshPage, url=imgurl, form=form)

@app.route("/analysis", methods=["GET"])
def analysis():

    access_token = request.args.get("access_token")
    refresh_token = request.args.get("refresh_token")
    token_type = "Bearer" #always bearer, don't need to grab this each request
    expires_in = request.args["expires_in"]
    pldata = request.args["data"]

    unpackedData = pldata.split(",")

    p1 = data(access_token)
    p2 = p1.profile()
    dbName = p2.get("dbName")
    userName = p2.get("userName")

    db = client[dbName]
    collection='MASTER'
    mongoCollection = db[collection]

    #retrieve songs and analysis for user selected playlists, store in DB
    masterSongList=[]
    for i in range(len(unpackedData)):
        result = p1.getPlaylistTracks(unpackedData[i])
        for i in range(len(result)):
            masterSongList.append(result[i])

    results = mongoCollection.insert_many(masterSongList) #includes song id, artist info

    p1.playlistTrackFeatures(collection)

    #offer user choice of how many clusters
    clusters = 10
    # take in user selection of playlists
    result = stats(dbName, collection)
    featuresList = ['acousticness','danceability','energy','instrumentalness','liveness','speechiness','valence']
    result.kMeans(featuresList, clusters)

    # add option for user to decide if they want to create spotify playlists
    # offer user cluster analysis (bar chart with each avg attribute)

    #print(result.X.head())

    #plotting section goes here
    #p1 = plotting()
    #p1.plot()


    # #create playlists for each kmeans assignment
    c1 = create(access_token)
    df = result.X
    centers = result.centers
    for i in range(clusters):
        descript = ""
        center = centers[i]
        for j in range(len(featuresList)):
            entry = str(" "+str(featuresList[j])+":"+str(center[j])+" ")
            descript = descript + entry

        response2 = c1.newPlaylist(userName, str(TODAY+'kmeans'+str(i)),descript)
        print(response2)
        r2 = response2['uri']
        fields = r2.split(":")
        plid = fields[2]

        dfi = df.loc[df['kMeansAssignment'] == i]
        dfi = dfi['trackId']
        idList = dfi.values.tolist()
        uriList=[]
        for item in idList:
            uriList.append("spotify:track:{}".format(item))

        n = 50
        for j in range(0, len(uriList), n):  
            listToSend = uriList[j:j + n]
            stringList = ",".join(listToSend)
            response3 = c1.addSongs(plid, stringList)
            #print(response3)

    return("Completed K-Means Analysis for selected playlists, created playlists in Spotify")
    #LATER - make this where the results will be displayed as a bar chart

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

    #show the averages, ranges here to examine what the characteristics of a playlist are

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
