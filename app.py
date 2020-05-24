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
    DJSET = [{"trackName": "WallOfStrings", "trackId": "1YH044L7flGyNT7lUT1KV5", "artistNames": ["Ben B\u00f6hmer"], "artistIds": ["5tDjiBYUsTqzd0RkTZxK7u"], "audioFeatures": {"danceability": 0.677, "energy": 0.605, "key": 7, "loudness": -9.813, "mode": 1, "speechiness": 0.0368, "acousticness": 0.00857, "instrumentalness": 0.911, "liveness": 0.16, "valence": 0.147, "tempo": 125.018, "type": "audio_features", "id": "1YH044L7flGyNT7lUT1KV5", "uri": "spotify:track:1YH044L7flGyNT7lUT1KV5", "track_href": "https://api.spotify.com/v1/tracks/1YH044L7flGyNT7lUT1KV5", "analysis_url": "https://api.spotify.com/v1/audio-analysis/1YH044L7flGyNT7lUT1KV5", "duration_ms": 254306, "time_signature": 4}, "genres": ["progressive house", "tropical house"]}, {"trackName": "NothingToLose-OliverKoletzkiRemix", "trackId": "2BnHNJ2JUbuZmcHX3Z3jjj", "artistNames": ["Giorgia Angiuli", "Oliver Koletzki"], "artistIds": ["4iHnLagnnmgiIwMSm1wuTq", "1WjBIvYAnZTkTh5UiZNwlR"], "audioFeatures": {"danceability": 0.677, "energy": 0.969, "key": 10, "loudness": -8.154, "mode": 0, "speechiness": 0.0422, "acousticness": 2.63e-05, "instrumentalness": 0.888, "liveness": 0.108, "valence": 0.0375, "tempo": 123.013, "type": "audio_features", "id": "2BnHNJ2JUbuZmcHX3Z3jjj", "uri": "spotify:track:2BnHNJ2JUbuZmcHX3Z3jjj", "track_href": "https://api.spotify.com/v1/tracks/2BnHNJ2JUbuZmcHX3Z3jjj", "analysis_url": "https://api.spotify.com/v1/audio-analysis/2BnHNJ2JUbuZmcHX3Z3jjj", "duration_ms": 411255, "time_signature": 4}, "genres": ["italian techno", "puglia indie", "deep melodic euro house", "electronica", "german techno", "minimal techno", "organic electronic", "tech house", "tropical house"]}, {"trackName": "MyBoy-MeduzaRemix", "trackId": "6npSsIYSqN7ia7rdGme1Ic", "artistNames": ["R Plus", "Dido", "MEDUZA"], "artistIds": ["0lnAZ68xKGysVy084bTQmh", "2mpeljBig2IXLXRAFO9AAs", "0xRXCcSX89eobfrshSVdyu"], "audioFeatures": {"danceability": 0.676, "energy": 0.717, "key": 1, "loudness": -9.519, "mode": 1, "speechiness": 0.0439, "acousticness": 0.0105, "instrumentalness": 0.783, "liveness": 0.0891, "valence": 0.114, "tempo": 123.997, "type": "audio_features", "id": "6npSsIYSqN7ia7rdGme1Ic", "uri": "spotify:track:6npSsIYSqN7ia7rdGme1Ic", "track_href": "https://api.spotify.com/v1/tracks/6npSsIYSqN7ia7rdGme1Ic", "analysis_url": "https://api.spotify.com/v1/audio-analysis/6npSsIYSqN7ia7rdGme1Ic", "duration_ms": 406452, "time_signature": 4}, "genres": ["dance pop", "new wave pop", "pop rock", "pop house"]}, {"trackName": "Birthright-MariusDrescherRemixEdit", "trackId": "7fOmMqzKyjApRDwBSj9PfN", "artistNames": ["Nora En Pure", "Marius Drescher"], "artistIds": ["24DO0PijjITGIEWsO8XaPs", "4oU99ab1DTNIF3a9RHmnhf"], "audioFeatures": {"danceability": 0.637, "energy": 0.905, "key": 8, "loudness": -5.582, "mode": 0, "speechiness": 0.0404, "acousticness": 0.00046, "instrumentalness": 0.0984, "liveness": 0.159, "valence": 0.306, "tempo": 122.997, "type": "audio_features", "id": "7fOmMqzKyjApRDwBSj9PfN", "uri": "spotify:track:7fOmMqzKyjApRDwBSj9PfN", "track_href": "https://api.spotify.com/v1/tracks/7fOmMqzKyjApRDwBSj9PfN", "analysis_url": "https://api.spotify.com/v1/audio-analysis/7fOmMqzKyjApRDwBSj9PfN", "duration_ms": 219878, "time_signature": 3}, "genres": ["deep house", "deep tropical house", "edm", "electra", "house", "new french touch", "progressive house", "swiss pop", "tropical house", "deep euro house"]}, {"trackName": "Comet", "trackId": "0wkwd3BYi2oPUGkl3DaZse", "artistNames": ["Danito & Athina"], "artistIds": ["4Sa0Izacj6A61uSlU6jp4o"], "audioFeatures": {"danceability": 0.757, "energy": 0.897, "key": 8, "loudness": -7.067, "mode": 1, "speechiness": 0.0534, "acousticness": 0.012, "instrumentalness": 0.89, "liveness": 0.05, "valence": 0.719, "tempo": 120.008, "type": "audio_features", "id": "0wkwd3BYi2oPUGkl3DaZse", "uri": "spotify:track:0wkwd3BYi2oPUGkl3DaZse", "track_href": "https://api.spotify.com/v1/tracks/0wkwd3BYi2oPUGkl3DaZse", "analysis_url": "https://api.spotify.com/v1/audio-analysis/0wkwd3BYi2oPUGkl3DaZse", "duration_ms": 478723, "time_signature": 4}, "genres": ["cologne electronic", "deep melodic euro house", "ethnotronica", "focus trance", "german tech house"]}, {"trackName": "TreatYouBetter-CassianRemix", "trackId": "3haIVEYCzkPb5pwTzbEFDE", "artistNames": ["R\u00dcF\u00dcS DU SOL", "Cassian"], "artistIds": ["5Pb27ujIyYb33zBqVysBkj", "1ChtRJ3f4rbv4vtz87i6CD"], "audioFeatures": {"danceability": 0.597, "energy": 0.919, "key": 5, "loudness": -5.298, "mode": 0, "speechiness": 0.0345, "acousticness": 0.00244, "instrumentalness": 0.114, "liveness": 0.33, "valence": 0.236, "tempo": 124.017, "type": "audio_features", "id": "3haIVEYCzkPb5pwTzbEFDE", "uri": "spotify:track:3haIVEYCzkPb5pwTzbEFDE", "track_href": "https://api.spotify.com/v1/tracks/3haIVEYCzkPb5pwTzbEFDE", "analysis_url": "https://api.spotify.com/v1/audio-analysis/3haIVEYCzkPb5pwTzbEFDE", "duration_ms": 290934, "time_signature": 4}, "genres": ["australian electropop", "indietronica", "nu disco"]}, {"trackName": "Visions-OriginalShortEdit", "trackId": "2BC40dE6wyg6JDU37hb5yz", "artistNames": ["Anturage", "Alexey Union"], "artistIds": ["60hGAZqZ60I2EhUi0f4j2N", "4bzppvW4geKqxLC5VYJn2G"], "audioFeatures": {"danceability": 0.787, "energy": 0.699, "key": 6, "loudness": -8.789, "mode": 1, "speechiness": 0.0479, "acousticness": 0.000343, "instrumentalness": 0.85, "liveness": 0.0897, "valence": 0.25, "tempo": 120.999, "type": "audio_features", "id": "2BC40dE6wyg6JDU37hb5yz", "uri": "spotify:track:2BC40dE6wyg6JDU37hb5yz", "track_href": "https://api.spotify.com/v1/tracks/2BC40dE6wyg6JDU37hb5yz", "analysis_url": "https://api.spotify.com/v1/audio-analysis/2BC40dE6wyg6JDU37hb5yz", "duration_ms": 198417, "time_signature": 4}, "genres": ["groove room"]}, {"trackName": "Hi-CidInc.Remix", "trackId": "0EMNWjTgRRCgY6KnHH9Ws6", "artistNames": ["Kasper Koman", "Cid Inc."], "artistIds": ["2fjKKBOOCTqkDTRC7wH6dO", "6pWibdpstk7c1dp0NVi9xJ"], "audioFeatures": {"danceability": 0.804, "energy": 0.921, "key": 7, "loudness": -7.976, "mode": 1, "speechiness": 0.0686, "acousticness": 0.0017, "instrumentalness": 0.861, "liveness": 0.0375, "valence": 0.177, "tempo": 121.996, "type": "audio_features", "id": "0EMNWjTgRRCgY6KnHH9Ws6", "uri": "spotify:track:0EMNWjTgRRCgY6KnHH9Ws6", "track_href": "https://api.spotify.com/v1/tracks/0EMNWjTgRRCgY6KnHH9Ws6", "analysis_url": "https://api.spotify.com/v1/audio-analysis/0EMNWjTgRRCgY6KnHH9Ws6", "duration_ms": 487869, "time_signature": 4}, "genres": ["focus trance", "focus trance", "tech house"]}, {"trackName": "KeepControl-ArtbatRemix", "trackId": "6n8wkmgsU4wCJdM2rky0yb", "artistNames": ["Sono", "ARTBAT"], "artistIds": ["7vBGVjjUKLWS8zLNSYwVVC", "3BkRu2TGd2I1uBxZKddfg1"], "audioFeatures": {"danceability": 0.769, "energy": 0.762, "key": 7, "loudness": -9.669, "mode": 1, "speechiness": 0.0757, "acousticness": 0.0151, "instrumentalness": 0.783, "liveness": 0.0748, "valence": 0.119, "tempo": 123.002, "type": "audio_features", "id": "6n8wkmgsU4wCJdM2rky0yb", "uri": "spotify:track:6n8wkmgsU4wCJdM2rky0yb", "track_href": "https://api.spotify.com/v1/tracks/6n8wkmgsU4wCJdM2rky0yb", "analysis_url": "https://api.spotify.com/v1/audio-analysis/6n8wkmgsU4wCJdM2rky0yb", "duration_ms": 483902, "time_signature": 4}, "genres": ["pop house", "minimal techno", "tech house", "ukrainian electronic"]}, {"trackName": "Nameless", "trackId": "1QRuPx8r7RlfyyWazPLPfr", "artistNames": ["Mees Salom\u00e9"], "artistIds": ["3vcY5vaGqSQF6UA9N2iC4L"], "audioFeatures": {"danceability": 0.677, "energy": 0.758, "key": 10, "loudness": -10.189, "mode": 1, "speechiness": 0.0446, "acousticness": 0.048, "instrumentalness": 0.776, "liveness": 0.123, "valence": 0.0394, "tempo": 122.983, "type": "audio_features", "id": "1QRuPx8r7RlfyyWazPLPfr", "uri": "spotify:track:1QRuPx8r7RlfyyWazPLPfr", "track_href": "https://api.spotify.com/v1/tracks/1QRuPx8r7RlfyyWazPLPfr", "analysis_url": "https://api.spotify.com/v1/audio-analysis/1QRuPx8r7RlfyyWazPLPfr", "duration_ms": 284717, "time_signature": 4}, "genres": ["deep techno"]}, {"trackName": "DarkSlide", "trackId": "2XPafM7lYPYBwy9nVlHkjP", "artistNames": ["J.P. Velardi"], "artistIds": ["2hWGvUMh3CyIxKvJp7mlFp"], "audioFeatures": {"danceability": 0.759, "energy": 0.969, "key": 10, "loudness": -4.658, "mode": 0, "speechiness": 0.0417, "acousticness": 0.00131, "instrumentalness": 0.917, "liveness": 0.0653, "valence": 0.52, "tempo": 118.009, "type": "audio_features", "id": "2XPafM7lYPYBwy9nVlHkjP", "uri": "spotify:track:2XPafM7lYPYBwy9nVlHkjP", "track_href": "https://api.spotify.com/v1/tracks/2XPafM7lYPYBwy9nVlHkjP", "analysis_url": "https://api.spotify.com/v1/audio-analysis/2XPafM7lYPYBwy9nVlHkjP", "duration_ms": 240000, "time_signature": 4}, "genres": []}]

    
    newSetTargets = []

    #TODO set audio features to skip here

    #set max distance per attribute we are willing to use
    bound = 0.2
    

    trackIndex = 0
    for track in DJSET:
        trackTargets = {}
        for audioFeature in spotifyAudioFeatures:
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
    print(newSetTargets)

            

    ################################################################
    ##          STEP ONE - BUILD POOL OF SUGGESTED TRACKS         ##
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
        cleanRecommendations = spotifyDataRetrieval.cleanTrackData(recommendedTracks)
        cleanRecommendationsWithFeatures = spotifyDataRetrieval.getAudioFeatures(cleanRecommendations)
        poolAdditions = 0
        for cleanTrack in tqdm(cleanRecommendationsWithFeatures):
            if cleanTrack['trackID'] not in cleanMasterTrackPoolIDs:
                poolAdditions += 1
                cleanMasterTrackPool.append(cleanTrack)
                cleanMasterTrackPoolIDs.append(cleanTrack['trackID'])
        print("Added {} tracks to recommendations pool".format(poolAdditions))

    print("Loaded {} unique track recommendations".format(len(cleanMasterTrackPoolIDs)))

    ################################################################
    ##           STEP TWO - FIT RECOMMENDATIONS TO CURVE          ##
    ################################################################

    #TODO- MAPREDUCE FOR EFFICIENCY
    outgoingRecommendations = []

    #for each target we're trying to match songs to
    for targetTrack in newSetTargets:
        totalEuclideanDistances = []
        #check each possible song in our pool
        for recommendedTrack in cleanMasterTrackPool:
            totalEuclideanDistance = 0
            #compare the features to target and record the distance
            for audiofeature in spotifyAudioFeatures:
                skipFeatures = []#'liveness']
                if audiofeature not in skipFeatures:
                    diff = (recommendedTrack['audioFeatures'][audiofeature]*100) - (targetTrack["target_{}".format(audioFeature)]*100)
                    totalEuclideanDistance += diff * diff
           
            #append the distance to a list that aligns with the pool
            totalEuclideanDistances.append(totalEuclideanDistance)

        # sort the recommendations by min ED
        bestFitTrack = cleanMasterTrackPool[totalEuclideanDistances.index(min(totalEuclideanDistances))]
        outgoingRecommendations.append(bestFitTrack)
        
        print("TARGET")
        print(targetTrack)
        print("################################################################")
        print("SUGGESTION")
        print(bestFitTrack)
        print("################################################################")


    # c1 = create(access_token)
    # response2 = c1.newPlaylist(userName, "+| TEST SET |+","N/A")
    # r2 = response2['uri']
    # fields = r2.split(":")
    # plid = fields[2]
    # uriList=[]
    # for item in recids:
    #     uriList.append("spotify:track:{}".format(item))
    # if len(uriList)>0:
    #     n = 50 #spotify playlist addition limit
    #     for j in range(0, len(uriList), n):  
    #         listToSend = uriList[j:j + n]
    #         stringList = ",".join(listToSend)
    #         response3 = c1.addSongs(plid, stringList)

    print('DONE')
    input()


    #return render_template("index.html", title='Home', user=userName, token=access_token, refresh=refresh_token, url=imgurl, form=form)

#instantiate app
if __name__ == "__main__":
    if ENV == 'heroku':
        app.run(debug=False)
    else:
        app.run(debug=True, port=PORT)