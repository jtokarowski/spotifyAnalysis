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
from tqdm import tqdm

with open("../1001tracklists/trainingDataset.json") as jsonFile:
    trainingData = json.load(jsonFile)

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

    #TODO checkbox form list the sets we can model the tunnel off of

    #list of audio features used to fit curve
    spotifyAudioFeatures = ['acousticness','danceability','energy','instrumentalness','liveness','speechiness','valence']
    
    #grab the tokens from the URL + intialize data class
    access_token = request.args.get("access_token")
    refresh_token = request.args.get("refresh_token")
    token_type = "Bearer" #always bearer, don't need to grab this each request
    expires_in = request.args["expires_in"]
    spotifyDataRetrieval = data(access_token)
    authorization = auth()

    profile = spotifyDataRetrieval.profile()
    userName = profile.get("userName")

    ################################################################
    ###               TUNNEL  BETA                               ###
    ################################################################

    ################################################################
    ##          STEP ZERO - SET TARGETS                           ##
    ################################################################
    #set target is a list of dicts
    DJSET = trainingData['fedde_le_grand'][2]['tracks_with_features']

    #initialize mapreduce lists - aligned with target tracks
    minimumDistances = [999999] * len(DJSET)
    minimumDistanceTracks = ["None"] * len(DJSET)
    
    newSetTargets = []

    skipFeatures = ['liveness']

    #set max distance per attribute we are willing to use
    bound = 0.2
    
    trackIndex = 0
    for track in DJSET:
        trackTargets = {}
        for audioFeature in spotifyAudioFeatures:
            #store the features in same format for easy ED calc later
            trackTargets['audioFeatures'] =  track['audioFeatures']

            #set targets + min/max
            key = "target_{}".format(audioFeature)
            trackTargets[key] = track['audioFeatures'][audioFeature]
                
            minKey = "min_{}".format(audioFeature)
            maxKey = "max_{}".format(audioFeature)
            trackTargets[minKey] = max(track['audioFeatures'][audioFeature] - bound,0)
            trackTargets[maxKey] = min(track['audioFeatures'][audioFeature] + bound,1)

        trackTargets['trackIndex'] = trackIndex
        newSetTargets.append(trackTargets)
        trackIndex +=1

    print("Completed target setup")

    ################################################################
    ##    STEP ONE - BUILD POOL OF SUGGESTED TRACKS + MAP         ##
    ################################################################

    #build up list of user top artists
    topListenType = 'artists'
    userTopArtists = []
    userTopArtists.extend(spotifyDataRetrieval.getMyTop(topType=topListenType, term='short_term', limit=10))
    userTopArtists.extend(spotifyDataRetrieval.getMyTop(topType=topListenType, term='medium_term', limit=10))
    userTopArtists.extend(spotifyDataRetrieval.getMyTop(topType=topListenType, term='long_term', limit=10))
    #remove dupes
    userTopArtists = list(set(userTopArtists))
    print("Loaded {} user top artists".format(len(userTopArtists)))

    # Build up a large pool of options by grabbing suggestions for each
    # of top artists, target 0 and target 1 to get almost all of pool
    cleanMasterTrackPool = []
    cleanMasterTrackPoolIDs = []
    for artist in tqdm(userTopArtists):  
        recommendedTracks = spotifyDataRetrieval.getRecommendations(limit = 100, seed_artists = artist)
        #break if we don't get anything back
        if len(recommendedTracks) == 0 or recommendedTracks == None:
            continue

        cleanRecommendations = spotifyDataRetrieval.cleanTrackData(recommendedTracks)
        cleanRecommendationsWithFeatures = spotifyDataRetrieval.getAudioFeatures(cleanRecommendations)
        
        trackPoolAdditions = 0
        for cleanTrack in cleanRecommendationsWithFeatures:
            #check if it will dupe
            if cleanTrack['trackID'] not in cleanMasterTrackPoolIDs:
                #calculate distance to each target
                cleanTrack['euclideanDistances'] = []
                arrayIndex = 0
                for target in newSetTargets:
                    euclideanDistance = spotifyDataRetrieval.calculateEuclideanDistance(cleanTrack, target, spotifyAudioFeatures, "absValue")
                    #build a list for each suggested track to each target
                    cleanTrack['euclideanDistances'].append(euclideanDistance)
                    #check vs the current closest match
                    if euclideanDistance < minimumDistances[arrayIndex]:
                        minimumDistances[arrayIndex] = euclideanDistance
                        minimumDistanceTracks[arrayIndex] = cleanTrack
                    arrayIndex += 1


                trackPoolAdditions += 1
                cleanMasterTrackPool.append(cleanTrack)
                cleanMasterTrackPoolIDs.append(cleanTrack['trackID'])
        print("Added {} tracks to recommendations pool".format(trackPoolAdditions))

    print("Loaded {} unique track recommendations".format(len(cleanMasterTrackPoolIDs)))

    ################################################################
    ##           STEP TWO SEND SET TO SPOTIFY                     ##
    ################################################################

    #create the playlist to populate
    spotifyCreate = create(access_token)
    createPlaylistResponse = spotifyCreate.newPlaylist(userName, "+| MiC Tailored Set |+","Created via Music in Context ++2020 Jtokarowski++")
    playlistID = spotifyDataRetrieval.URItoID(createPlaylistResponse['uri'])
    
    #convert to URI
    recommendationURIs = []
    for track in minimumDistanceTracks:
        recommendationURIs.append(spotifyDataRetrieval.idToURI("track", track['trackID']))
    
    
    playlistAdditionsResponse = spotifyCreate.addTracks(playlistID, recommendationURIs)
    print(playlistAdditionsResponse)

    print('DONE')
    quit()

    #return render_template("index.html", title='Home', user=userName, token=access_token, refresh=refresh_token, url=imgurl, form=form)

#instantiate app
if __name__ == "__main__":
    if ENV == 'heroku':
        app.run(debug=False)
    else:
        app.run(debug=True, port=PORT)