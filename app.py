import json
from flask import Flask, Markup, request, redirect, render_template, jsonify
import requests
from datetime import date
from spotifyClient import data, auth, create
from statisticalAnalysis import stats
import pandas as pd
from flask_wtf import FlaskForm
from wtforms import widgets, SelectMultipleField
import itertools
from collections import Counter
from operator import itemgetter
import time
import os

ENV = os.environ.get('ENV')
SECRET_KEY = ' ' #This doesn't actually get used, but simpleForm needs this to run

#grab date program is being run
td = date.today()
TODAY = td.strftime("%Y%m%d") ##YYYYMMDD
YEAR = td.strftime("%Y") ##YYYY
NICEDATE = td.strftime("%b %d %Y") ##MMM DD YYYY

#creates instance of app
app = Flask(__name__)
app.config.from_object(__name__)

# Server-side Parameters based on where it's running
if ENV == 'dev':
    CLIENT_SIDE_URL = "http://127.0.0.1"
    PORT = 8000
    REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
    START_PAGE_LINK = "{}:{}/start".format(CLIENT_SIDE_URL, PORT)
elif ENV == 'heroku':
    CLIENT_SIDE_URL = "https://musicincontext.herokuapp.com"
    REDIRECT_URI = "{}/callback/q".format(CLIENT_SIDE_URL)
    START_PAGE_LINK = "{}/start".format(CLIENT_SIDE_URL)

@app.route("/")
def home():
    #Serve the landing page
    return render_template("landingpage.html", nextPageLink = START_PAGE_LINK)


@app.route("/start")
#TODO: set / to serve landing page, with link to begin the flow
def index():
    # Auth Step 1: Authorize Spotify User
    authorization = auth()
    return redirect(authorization.auth_url)

@app.route("/callback/q")
def callback():
    # Auth Step 2: Requests refresh and access tokens
    authorization = auth()
    return redirect(authorization.get_accessToken(request.args['code']))

@app.route("/authed", methods=["GET","POST"])
def authed():

    #grab the tokens from the URL + intialize data class
    access_token = request.args.get("access_token")
    refresh_token = request.args.get("refresh_token")
    token_type = "Bearer" #always bearer, don't need to grab this each request
    expires_in = request.args["expires_in"]
    spotifyDataRetrieval = data(access_token)
    authorization = auth()

    profile = spotifyDataRetrieval.profile()
    userName = profile.get("userName")
    image = profile.get("images")

    if len(image) == 0:
        imgurl = 'N/A'
    else:
        imgurl = image[0]['url']
        
    #build the link for each playlist
    allUserPLaylists = spotifyDataRetrieval.currentUserPlaylists()
    checkboxData = []
    for playlist in allUserPLaylists:
        checkboxFormatPlaylist = (playlist['uri'],playlist['playlistName'])
        checkboxData.append(checkboxFormatPlaylist)

    #set up the checkbox classes
    class MultiCheckboxField(SelectMultipleField):
        widget = widgets.ListWidget(prefix_label=False)
        option_widget = widgets.CheckboxInput()

    class SimpleForm(FlaskForm):
        # create a list of value/description tuples
        files = [(x, y) for x,y in checkboxData]
        playlistSelections = MultiCheckboxField('Label', choices=files)

    form = SimpleForm()

    if form.validate_on_submit():
        formData = form.playlistSelections.data
        if not formData:
            return render_template("index.html", title='Home', user=userName, token=access_token, refresh=refresh_token, url=imgurl, form=form)
        else:
            clusterVisPage = "{}?refresh_token={}&access_token={}&data={}".format(authorization.visualizationURL(), refresh_token, access_token, ",".join(formData))
            return redirect(clusterVisPage) 
    else:
        print(form.errors)

    return render_template("index.html", title='Home', user=userName, token=access_token, refresh=refresh_token, url=imgurl, form=form)

@app.route("/analysis", methods=["GET"])
def analysis():

    #list of spotify attributes used in the model
    spotifyAudioFeatures = ['acousticness','danceability','energy','instrumentalness','liveness','speechiness','valence']

    #intialize data retrieval class
    access_token = request.args.get("access_token")
    refresh_token = request.args.get("refresh_token")
    token_type = "Bearer"
    spotifyDataRetrieval = data(access_token)


    ################################################################
    ###               CLUSTER SECTION                            ###
    ################################################################

    #raw data from the checklist (a list of playlist URIs specifically)
    pldata = request.args["data"]
    unpackedData = pldata.split(",")
    
    profile = spotifyDataRetrieval.profile()
    userName = profile.get("userName")

    #retrieve songs and audio features for user selected playlists
    masterTrackList=[]
    for i in range(len(unpackedData)):
        tracks = spotifyDataRetrieval.getPlaylistTracks(unpackedData[i])
        masterTrackList.extend(tracks)

    cleanedMasterTrackList = spotifyDataRetrieval.cleanTrackData(masterTrackList)
    masterTrackListWithFeatures = spotifyDataRetrieval.getAudioFeatures(cleanedMasterTrackList)

    #set up kmeans, check how many songs
    if len(masterTrackListWithFeatures)<5:
        clusters = len(masterTrackListWithFeatures)
    else:
        clusters = 5

    statistics = stats(masterTrackListWithFeatures)
    statistics.kMeans(spotifyAudioFeatures, clusters)
    dataframeWithClusters = statistics.df
    clusterCenterCoordinates = statistics.centers

    #create playlists for each kmeans assignment
    spotifyCreate = create(access_token)
    repeatgenres = {}
    for i in range(clusters):
        descript = ""
        selectedClusterCenter = clusterCenterCoordinates[i]
        for j in range(len(spotifyAudioFeatures)):
            entry = str(" "+str(spotifyAudioFeatures[j])+":"+str(round(selectedClusterCenter[j],3))+" ")
            descript += entry
            #we can return less detail here, maybe 'highly danceable' is sufficient

        descript +=" created on {}".format(NICEDATE)
        descript+=" by JTokarowski "

        dataframeFilteredToSingleCluster = dataframeWithClusters.loc[dataframeWithClusters['kMeansAssignment'] == i]

        genres = dataframeFilteredToSingleCluster['genres'].values.tolist()
        genreslist = genres[0]

        genreDict = {}
        for genre in genreslist:
            g =  genre.replace(" ", "_")
            if g in genreDict:
                genreDict[g]+=1
            else:
                genreDict[g]=1

        v=list(genreDict.values())
        k=list(genreDict.keys())

        try:
            maxGenre = k[v.index(max(v))]
        except:
            maxGenre = "¯\_(ツ)_/¯"

        if maxGenre in repeatgenres.keys():
            repeatgenres[maxGenre]+=1
            maxGenre += "_"+str(repeatgenres[maxGenre])
        else:
            repeatgenres[maxGenre]=1

        maxGenre = maxGenre.replace("_", " ")

        newPlaylistInfo = spotifyCreate.newPlaylist(userName, "+| "+str(maxGenre)+" |+",descript)
        newPlaylistID = spotifyDataRetrieval.URItoID(newPlaylistInfo['uri'])


        dataframeFilteredToSingleCluster = dataframeFilteredToSingleCluster['trackID']
        newPlaylistTracksIDList = dataframeFilteredToSingleCluster.values.tolist()

        outputPlaylistTracks=[]
        for spotifyID in newPlaylistTracksIDList:
            outputPlaylistTracks.append(spotifyDataRetrieval.idToURI("track",spotifyID))

        if len(outputPlaylistTracks)>0:
            n = 50 #spotify playlist addition limit
            for j in range(0, len(outputPlaylistTracks), n):  
                playlistTracksSegment = outputPlaylistTracks[j:j + n]
                spotifyCreate.addTracks(newPlaylistID, playlistTracksSegment)
                
            
    return render_template('radar_chart.html', title='Cluster Centers', max = 1.0, labels=spotifyAudioFeatures, centers=clusterCenterCoordinates)

#instantiate app
if __name__ == "__main__":
    if ENV == 'heroku':
        app.run(debug=False)
    else:
        app.run(debug=True, port=PORT)