import json
from flask import Flask, Markup, request, redirect, render_template, jsonify
import requests
from urllib.parse import quote
from pymongo import MongoClient
from datetime import date
from spotifyClient import data, auth, create
from statisticalAnalysis import stats
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
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

@app.route("/")
def index():
    # Auth Step 1: Authorize Spotify User
    a = auth()
    return redirect(a.auth_url)

@app.route("/callback/q")
def callback():
    # Auth Step 2: Requests refresh and access tokens
    a = auth()
    return redirect(a.get_accessToken(request.args['code']))

@app.route("/authed", methods=["GET","POST"])
def authed():

    #placeholder for discover weekly URI
    #discURI = ""
            #if playlist['playlistName'] == 'DiscoverWeekly':
            # if plalyist['owner'] == 'Spotify':
            #     discURI = plalyist['uri']


    #grab the tokens from the URL
    access_token = request.args.get("access_token")
    refresh_token = request.args.get("refresh_token")
    token_type = "Bearer" #always bearer, don't need to grab this each request
    expires_in = request.args["expires_in"]

    a = auth()
    d = data(access_token)

    prof = d.profile()
    db = prof.get("dbName")
    userName = prof.get("userName")
    image = prof.get("images")

    if len(image) == 0:
        imgurl = 'N/A'
    else:
        imgurl = image[0]['url']
        

    refreshPage = "{}?refresh_token={}&access_token={}".format(a.refreshURL(), refresh_token, access_token)
    analysisPage = "{}?refresh_token={}&access_token={}&expires_in={}".format(a.analysisURL(), refresh_token, access_token, expires_in)

    #build the link for each playlist
    response = d.userPlaylists()
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
        if not formData:
            return render_template("index2.html", title='Home', user=userName, token=access_token, refresh=refresh_token, link=refreshPage, url=imgurl, form=form)
        else:
            dataString = ",".join(formData)
            analysisPageSelections = "{}&data={}".format(analysisPage, dataString)
            return redirect(analysisPageSelections) 
    else:
        print(form.errors)

    return render_template("index2.html", title='Home', user=userName, token=access_token, refresh=refresh_token, link=refreshPage, url=imgurl, form=form)

@app.route("/analysis", methods=["GET"])
def analysis():

    access_token = request.args.get("access_token")
    refresh_token = request.args.get("refresh_token")
    token_type = "Bearer"
    expires_in = request.args["expires_in"]
    pldata = request.args["data"]

    unpackedData = pldata.split(",")

    d = data(access_token)
    prof = d.profile()
    dbName = prof.get("dbName")
    userName = prof.get("userName")

    db = client[dbName]
    collection = 'MASTER'
    mongoCollection = db[collection]

    #retrieve songs and analysis for user selected playlists, store in DB
    masterSongList=[]
    for i in range(len(unpackedData)):
        songs = d.getPlaylistTracks(unpackedData[i])
        masterSongList.extend(songs)

    mongoResult = mongoCollection.insert_many(masterSongList) #includes song id, artist info

    d.playlistTrackFeatures(collection)

    #set up kmeans
    clusters = 5
    featuresList = ['acousticness','danceability','energy','instrumentalness','liveness','speechiness','valence']
    statistics = stats(dbName, collection)
    statistics.kMeans(featuresList, clusters)

    df = statistics.df
    centers = statistics.centers

    #create playlists for each kmeans assignment
    c1 = create(access_token)
    for i in range(clusters):
        descript = ""
        center = centers[i]
        for j in range(len(featuresList)):
            entry = str(" "+str(featuresList[j])+":"+str(round(center[j],3))+" ")
            descript = descript + entry

        response2 = c1.newPlaylist(userName, str(TODAY+'Cluster'+str(i+1)),descript)
        r2 = response2['uri']
        fields = r2.split(":")
        plid = fields[2]

        dfi = df.loc[df['kMeansAssignment'] == i]
        dfi = dfi['trackId']
        idList = dfi.values.tolist()
        uriList=[]
        for item in idList:
            uriList.append("spotify:track:{}".format(item))

        n = 50 #spotify playlist addition limit
        for j in range(0, len(uriList), n):  
            listToSend = uriList[j:j + n]
            stringList = ",".join(listToSend)
            response3 = c1.addSongs(plid, stringList)
            
    return render_template('radar_chart.html', title='Cluster Centers', max = 1.0, labels=featuresList, centers=centers)

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
    
if __name__ == "__main__":
    app.run(debug=True, port=PORT)
