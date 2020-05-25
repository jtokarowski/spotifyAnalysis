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
    #['fedde_le_grand',nora_en_pure','armin_van_buuren"]
    # with open("../1001tracklists/trainingDataset.json") as jsonFile:
    #     trainingData = json.load(jsonFile)
    DJ = 'fedde_le_grand'
    #DJSET = trainingData[DJ][2]['tracks_with_features']
    DJSET = [{'trackName': 'TheWeekend', 'trackId': '1rkrZxfScVaKmHdwo92Hr7', 'artistNames': ['David Puentez'], 'artistIds': ['4gSsv9FQDyXx0GUkZYha7v'], 'audioFeatures': {'danceability': 0.805, 'energy': 0.665, 'key': 6, 'loudness': -4.161, 'mode': 1, 'speechiness': 0.0433, 'acousticness': 0.663, 'instrumentalness': 1.3e-06, 'liveness': 0.135, 'valence': 0.77, 'tempo': 125.935, 'type': 'audio_features', 'id': '1rkrZxfScVaKmHdwo92Hr7', 'uri': 'spotify:track:1rkrZxfScVaKmHdwo92Hr7', 'track_href': 'https://api.spotify.com/v1/tracks/1rkrZxfScVaKmHdwo92Hr7', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/1rkrZxfScVaKmHdwo92Hr7', 'duration_ms': 139048, 'time_signature': 4}, 'genres': ['progressive electro house']}, {'trackName': 'StringsOfLife-AtfcRemix', 'trackId': '0RQ2U4kyyRpa4GhaK5WZPg', 'artistNames': ['Kanu', 'Jude & Frank', 'ATFC'], 'artistIds': ['7qGg5f7GRoEEDsjhetcseQ', '7rUJV3QhhZJVRucw5BK09x', '04L4Y7Hkc1fULKhFbTnSSs'], 'audioFeatures': {'danceability': 0.636, 'energy': 0.864, 'key': 1, 'loudness': -6.365, 'mode': 1, 'speechiness': 0.0455, 'acousticness': 0.011, 'instrumentalness': 0.454, 'liveness': 0.0484, 'valence': 0.755, 'tempo': 124.984, 'type': 'audio_features', 'id': '0RQ2U4kyyRpa4GhaK5WZPg', 'uri': 'spotify:track:0RQ2U4kyyRpa4GhaK5WZPg', 'track_href': 'https://api.spotify.com/v1/tracks/0RQ2U4kyyRpa4GhaK5WZPg', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/0RQ2U4kyyRpa4GhaK5WZPg', 'duration_ms': 163322, 'time_signature': 4}, 'genres': ['funky tech house', 'italian tech house', 'chicago house', 'deep house', 'disco house', 'funky tech house', 'house', 'tech house', 'tribal house', 'vocal house']}, {'trackName': 'Dvncefloor', 'trackId': '6lBZpeJ5knvYhsMQArHtOX', 'artistNames': ['Cheyenne Giles', 'Knock2'], 'artistIds': ['2FoyDZAnGzikijRdXrocmj', '6mmSS7itNWKbapgG2eZbIg'], 'audioFeatures': {'danceability': 0.829, 'energy': 0.93, 'key': 10, 'loudness': -3.998, 'mode': 0, 'speechiness': 0.156, 'acousticness': 0.000389, 'instrumentalness': 0.0136, 'liveness': 0.054, 'valence': 0.48, 'tempo': 126.025, 'type': 'audio_features', 'id': '6lBZpeJ5knvYhsMQArHtOX', 'uri': 'spotify:track:6lBZpeJ5knvYhsMQArHtOX', 'track_href': 'https://api.spotify.com/v1/tracks/6lBZpeJ5knvYhsMQArHtOX', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/6lBZpeJ5knvYhsMQArHtOX', 'duration_ms': 152797, 'time_signature': 4}, 'genres': []}, {'trackName': 'HitTheFlow', 'trackId': '7r2VuLH3NqOu0bXF976eFY', 'artistNames': ['Landis'], 'artistIds': ['7bSDGumYzI7Cehekr534Xn'], 'audioFeatures': {'danceability': 0.817, 'energy': 0.987, 'key': 6, 'loudness': -3.344, 'mode': 0, 'speechiness': 0.231, 'acousticness': 0.0038, 'instrumentalness': 0.0432, 'liveness': 0.33, 'valence': 0.643, 'tempo': 128.002, 'type': 'audio_features', 'id': '7r2VuLH3NqOu0bXF976eFY', 'uri': 'spotify:track:7r2VuLH3NqOu0bXF976eFY', 'track_href': 'https://api.spotify.com/v1/tracks/7r2VuLH3NqOu0bXF976eFY', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/7r2VuLH3NqOu0bXF976eFY', 'duration_ms': 151875, 'time_signature': 4}, 'genres': ['pop edm']}, {'trackName': 'BeAlright-JyraClubMix', 'trackId': '0dfrLIPWUuN8b3uCv1GN5L', 'artistNames': ['Kenn Colt', 'Matthew Grant', 'JYRA'], 'artistIds': ['0vSNFAo2h20zd3HOBcM8BX', '1TtBULEnLbpIrXCrpcO4Di', '6reBho1LPAsnLmFCfnDjmh'], 'audioFeatures': {'danceability': 0.808, 'energy': 0.808, 'key': 2, 'loudness': -2.777, 'mode': 1, 'speechiness': 0.139, 'acousticness': 0.106, 'instrumentalness': 0.000746, 'liveness': 0.0862, 'valence': 0.453, 'tempo': 123.996, 'type': 'audio_features', 'id': '0dfrLIPWUuN8b3uCv1GN5L', 'uri': 'spotify:track:0dfrLIPWUuN8b3uCv1GN5L', 'track_href': 'https://api.spotify.com/v1/tracks/0dfrLIPWUuN8b3uCv1GN5L', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/0dfrLIPWUuN8b3uCv1GN5L', 'duration_ms': 210968, 'time_signature': 4}, 'genres': ['belgian edm', 'deep tropical house']}, {'trackName': '2U', 'trackId': '5iEeyPRWPkdtwMQkSkqRrf', 'artistNames': ['ESH', 'Constantin'], 'artistIds': ['6rXMet89uui55tWrcEz7ma', '1bW3e15ewZUHeQkIpgXoxg'], 'audioFeatures': {'danceability': 0.626, 'energy': 0.7, 'key': 0, 'loudness': -7.294, 'mode': 1, 'speechiness': 0.0626, 'acousticness': 0.00395, 'instrumentalness': 0.0999, 'liveness': 0.15, 'valence': 0.304, 'tempo': 124.972, 'type': 'audio_features', 'id': '5iEeyPRWPkdtwMQkSkqRrf', 'uri': 'spotify:track:5iEeyPRWPkdtwMQkSkqRrf', 'track_href': 'https://api.spotify.com/v1/tracks/5iEeyPRWPkdtwMQkSkqRrf', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/5iEeyPRWPkdtwMQkSkqRrf', 'duration_ms': 132480, 'time_signature': 4}, 'genres': []}, {'trackName': 'GetLow', 'trackId': '3ny4Cg0qRMiAvzc55karxs', 'artistNames': ['Shift K3Y'], 'artistIds': ['26OrZl5U3VNGHU9qUj8EcM'], 'audioFeatures': {'danceability': 0.851, 'energy': 0.916, 'key': 10, 'loudness': -3.442, 'mode': 1, 'speechiness': 0.115, 'acousticness': 0.0674, 'instrumentalness': 0.00401, 'liveness': 0.0871, 'valence': 0.779, 'tempo': 127.15, 'type': 'audio_features', 'id': '3ny4Cg0qRMiAvzc55karxs', 'uri': 'spotify:track:3ny4Cg0qRMiAvzc55karxs', 'track_href': 'https://api.spotify.com/v1/tracks/3ny4Cg0qRMiAvzc55karxs', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/3ny4Cg0qRMiAvzc55karxs', 'duration_ms': 202234, 'time_signature': 4}, 'genres': ['bass house', 'deep groove house', 'house', 'tropical house', 'uk dance']}, {'trackName': 'Conmigo', 'trackId': '2ZiLE5lpnkJKHYEvTOhhK6', 'artistNames': ['MNNR'], 'artistIds': ['4yZ4oFs7rKNy4OXlZmcZnd'], 'audioFeatures': {'danceability': 0.805, 'energy': 0.888, 'key': 11, 'loudness': -4.737, 'mode': 0, 'speechiness': 0.0915, 'acousticness': 0.00139, 'instrumentalness': 0.811, 'liveness': 0.0659, 'valence': 0.41, 'tempo': 125.991, 'type': 'audio_features', 'id': '2ZiLE5lpnkJKHYEvTOhhK6', 'uri': 'spotify:track:2ZiLE5lpnkJKHYEvTOhhK6', 'track_href': 'https://api.spotify.com/v1/tracks/2ZiLE5lpnkJKHYEvTOhhK6', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/2ZiLE5lpnkJKHYEvTOhhK6', 'duration_ms': 232381, 'time_signature': 4}, 'genres': ['bass house']}, {'trackName': 'Renegade', 'trackId': '3pXqrcwP59B4gGMAkn66Wg', 'artistNames': ['Steff da Campo', 'SMACK'], 'artistIds': ['7Bo6vpAmmhylCRWoHSBkcZ', '5uJw4WCX5nYj4FHky9r1Ug'], 'audioFeatures': {'danceability': 0.713, 'energy': 0.74, 'key': 9, 'loudness': -5.185, 'mode': 1, 'speechiness': 0.0692, 'acousticness': 0.0691, 'instrumentalness': 0, 'liveness': 0.361, 'valence': 0.419, 'tempo': 126.024, 'type': 'audio_features', 'id': '3pXqrcwP59B4gGMAkn66Wg', 'uri': 'spotify:track:3pXqrcwP59B4gGMAkn66Wg', 'track_href': 'https://api.spotify.com/v1/tracks/3pXqrcwP59B4gGMAkn66Wg', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/3pXqrcwP59B4gGMAkn66Wg', 'duration_ms': 142862, 'time_signature': 4}, 'genres': ['big room', 'deep big room', 'edm', 'electro house', 'house', 'pop edm', 'progressive electro house', 'progressive house']}, {'trackName': 'RollerCoaster', 'trackId': '6xdutwCIBmr6G6vkGoPsQh', 'artistNames': ['Frank Nitty'], 'artistIds': ['4cM46MLXy9kW9okwUOZJXr'], 'audioFeatures': {'danceability': 0.7, 'energy': 0.924, 'key': 4, 'loudness': -6.578, 'mode': 1, 'speechiness': 0.0389, 'acousticness': 0.000658, 'instrumentalness': 0.938, 'liveness': 0.161, 'valence': 0.0765, 'tempo': 125.026, 'type': 'audio_features', 'id': '6xdutwCIBmr6G6vkGoPsQh', 'uri': 'spotify:track:6xdutwCIBmr6G6vkGoPsQh', 'track_href': 'https://api.spotify.com/v1/tracks/6xdutwCIBmr6G6vkGoPsQh', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/6xdutwCIBmr6G6vkGoPsQh', 'duration_ms': 187844, 'time_signature': 4}, 'genres': []}, {'trackName': 'Fast', 'trackId': '0NQMRA9kAo4KEDRW78vNUz', 'artistNames': ['Main Circus'], 'artistIds': ['2S7Rdg81ijGBww89t47xCL'], 'audioFeatures': {'danceability': 0.776, 'energy': 0.89, 'key': 0, 'loudness': -2.331, 'mode': 1, 'speechiness': 0.0473, 'acousticness': 0.0095, 'instrumentalness': 0.821, 'liveness': 0.342, 'valence': 0.596, 'tempo': 125.009, 'type': 'audio_features', 'id': '0NQMRA9kAo4KEDRW78vNUz', 'uri': 'spotify:track:0NQMRA9kAo4KEDRW78vNUz', 'track_href': 'https://api.spotify.com/v1/tracks/0NQMRA9kAo4KEDRW78vNUz', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/0NQMRA9kAo4KEDRW78vNUz', 'duration_ms': 187200, 'time_signature': 4}, 'genres': []}, {'trackName': 'SummerAir(Feat.TrevorGuthrie)-SunneryJames&RyanMarcianoRemix', 'trackId': '2TAVfXcfCsqeZ6LzATWZrl', 'artistNames': ['Hardwell', 'Trevor Guthrie', 'Sunnery James & Ryan Marciano'], 'artistIds': ['6BrvowZBreEkXzJQMpL174', '6NXk2pLFocS2OkNdT7ncBt', '7kABWMhjA5GIl9PBEasBPt'], 'audioFeatures': {'danceability': 0.666, 'energy': 0.846, 'key': 1, 'loudness': -7.405, 'mode': 0, 'speechiness': 0.0386, 'acousticness': 0.000921, 'instrumentalness': 0.0013, 'liveness': 0.468, 'valence': 0.313, 'tempo': 125.983, 'type': 'audio_features', 'id': '2TAVfXcfCsqeZ6LzATWZrl', 'uri': 'spotify:track:2TAVfXcfCsqeZ6LzATWZrl', 'track_href': 'https://api.spotify.com/v1/tracks/2TAVfXcfCsqeZ6LzATWZrl', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/2TAVfXcfCsqeZ6LzATWZrl', 'duration_ms': 215238, 'time_signature': 4}, 'genres': ['big room', 'dance pop', 'deep big room', 'dutch house', 'edm', 'electro house', 'progressive electro house', 'progressive house', 'tropical house', 'canadian pop', 'big room', 'circuit', 'dutch house', 'edm', 'electro house', 'progressive electro house']}, {'trackName': 'AllOverTheWorld', 'trackId': '0XS2z0E0ox7F4JHYKKR4wK', 'artistNames': ['Fedde Le Grand'], 'artistIds': ['7dc6hUwyuIhrZdh80eaCEE'], 'audioFeatures': {'danceability': 0.657, 'energy': 0.976, 'key': 6, 'loudness': -3.842, 'mode': 0, 'speechiness': 0.0437, 'acousticness': 0.171, 'instrumentalness': 0.0315, 'liveness': 0.318, 'valence': 0.794, 'tempo': 125.983, 'type': 'audio_features', 'id': '0XS2z0E0ox7F4JHYKKR4wK', 'uri': 'spotify:track:0XS2z0E0ox7F4JHYKKR4wK', 'track_href': 'https://api.spotify.com/v1/tracks/0XS2z0E0ox7F4JHYKKR4wK', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/0XS2z0E0ox7F4JHYKKR4wK', 'duration_ms': 145728, 'time_signature': 4}, 'genres': ['big room', 'dance pop', 'deep big room', 'deep house', 'disco house', 'dutch house', 'edm', 'electro house', 'house', 'progressive electro house', 'progressive house', 'tech house', 'tropical house']}, {'trackName': 'You&I', 'trackId': '1LGZ1och1qvsxlzJr1zViK', 'artistNames': ['Bluckther', 'Jaime Deraz'], 'artistIds': ['6iPD95GXysz0X96JtbGej6', '4J7ascv32yT6yE75KRCktv'], 'audioFeatures': {'danceability': 0.585, 'energy': 0.957, 'key': 7, 'loudness': -3.1, 'mode': 0, 'speechiness': 0.0445, 'acousticness': 0.192, 'instrumentalness': 0.201, 'liveness': 0.227, 'valence': 0.494, 'tempo': 126.021, 'type': 'audio_features', 'id': '1LGZ1och1qvsxlzJr1zViK', 'uri': 'spotify:track:1LGZ1och1qvsxlzJr1zViK', 'track_href': 'https://api.spotify.com/v1/tracks/1LGZ1och1qvsxlzJr1zViK', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/1LGZ1och1qvsxlzJr1zViK', 'duration_ms': 158537, 'time_signature': 4}, 'genres': []}, {'trackName': 'Pyro', 'trackId': '3aDhgouoRk6awklXL4QBGQ', 'artistNames': ['Chester Young', 'Castion'], 'artistIds': ['3u45rXhQ0o9pUL24xlnf6e', '4xt0qH1NubQexyAzDa9UlR'], 'audioFeatures': {'danceability': 0.718, 'energy': 0.977, 'key': 1, 'loudness': -1.824, 'mode': 1, 'speechiness': 0.0668, 'acousticness': 0.143, 'instrumentalness': 0.0318, 'liveness': 0.374, 'valence': 0.259, 'tempo': 125.983, 'type': 'audio_features', 'id': '3aDhgouoRk6awklXL4QBGQ', 'uri': 'spotify:track:3aDhgouoRk6awklXL4QBGQ', 'track_href': 'https://api.spotify.com/v1/tracks/3aDhgouoRk6awklXL4QBGQ', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/3aDhgouoRk6awklXL4QBGQ', 'duration_ms': 148364, 'time_signature': 4}, 'genres': ['future house', 'pop edm', 'future house']}, {'trackName': 'Boss', 'trackId': '4VQQKNYsaFbcZAbsSnTDov', 'artistNames': ['Rave Radio', 'RageMode'], 'artistIds': ['7JrHNXd3zMD7xTFFhvnoyN', '3lTaAVDzKmGsmvFafGe5W6'], 'audioFeatures': {'danceability': 0.64, 'energy': 0.969, 'key': 2, 'loudness': -4.47, 'mode': 1, 'speechiness': 0.078, 'acousticness': 0.000257, 'instrumentalness': 0.696, 'liveness': 0.116, 'valence': 0.497, 'tempo': 126.01, 'type': 'audio_features', 'id': '4VQQKNYsaFbcZAbsSnTDov', 'uri': 'spotify:track:4VQQKNYsaFbcZAbsSnTDov', 'track_href': 'https://api.spotify.com/v1/tracks/4VQQKNYsaFbcZAbsSnTDov', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/4VQQKNYsaFbcZAbsSnTDov', 'duration_ms': 184762, 'time_signature': 4}, 'genres': []}, {'trackName': 'WhateverIWant', 'trackId': '5sWlaaDY0T6keHDTpbkQqY', 'artistNames': ['Carta'], 'artistIds': ['3MTk6MUbUmV5X0N04N56JF'], 'audioFeatures': {'danceability': 0.715, 'energy': 0.962, 'key': 0, 'loudness': -4.716, 'mode': 1, 'speechiness': 0.163, 'acousticness': 0.00792, 'instrumentalness': 0.669, 'liveness': 0.251, 'valence': 0.315, 'tempo': 125.964, 'type': 'audio_features', 'id': '5sWlaaDY0T6keHDTpbkQqY', 'uri': 'spotify:track:5sWlaaDY0T6keHDTpbkQqY', 'track_href': 'https://api.spotify.com/v1/tracks/5sWlaaDY0T6keHDTpbkQqY', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/5sWlaaDY0T6keHDTpbkQqY', 'duration_ms': 156667, 'time_signature': 4}, 'genres': ['deep big room', 'electro house', 'sky room']}, {'trackName': 'Obscure', 'trackId': '6hmD4PR6RvE863vhmAQXBZ', 'artistNames': ['Domastic'], 'artistIds': ['6IaUmXLyN20djYxvBlTk4c'], 'audioFeatures': {'danceability': 0.727, 'energy': 0.934, 'key': 1, 'loudness': -5.563, 'mode': 1, 'speechiness': 0.0405, 'acousticness': 0.00517, 'instrumentalness': 0.827, 'liveness': 0.258, 'valence': 0.0939, 'tempo': 128.024, 'type': 'audio_features', 'id': '6hmD4PR6RvE863vhmAQXBZ', 'uri': 'spotify:track:6hmD4PR6RvE863vhmAQXBZ', 'track_href': 'https://api.spotify.com/v1/tracks/6hmD4PR6RvE863vhmAQXBZ', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/6hmD4PR6RvE863vhmAQXBZ', 'duration_ms': 186562, 'time_signature': 3}, 'genres': ['gaming edm']}, {'trackName': 'SwitchBack', 'trackId': '2uyQG1q7OJEsj3VlNbWTY6', 'artistNames': ['SWACQ'], 'artistIds': ['45UHclgIcRavRoRa2MET5i'], 'audioFeatures': {'danceability': 0.729, 'energy': 0.954, 'key': 2, 'loudness': -4.156, 'mode': 1, 'speechiness': 0.0616, 'acousticness': 0.0167, 'instrumentalness': 0.382, 'liveness': 0.0441, 'valence': 0.391, 'tempo': 128.034, 'type': 'audio_features', 'id': '2uyQG1q7OJEsj3VlNbWTY6', 'uri': 'spotify:track:2uyQG1q7OJEsj3VlNbWTY6', 'track_href': 'https://api.spotify.com/v1/tracks/2uyQG1q7OJEsj3VlNbWTY6', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/2uyQG1q7OJEsj3VlNbWTY6', 'duration_ms': 180000, 'time_signature': 4}, 'genres': ['deep big room', 'sky room']}, {'trackName': 'HadEnough', 'trackId': '67HGEuWBJOmCJfgeoELIZe', 'artistNames': ['Mantrastic', 'Rechler'], 'artistIds': ['6vqoE66ibpvmRwM9157Z39', '0WXKLUSXMD4c4A00vXyQpl'], 'audioFeatures': {'danceability': 0.567, 'energy': 0.989, 'key': 4, 'loudness': -4.063, 'mode': 0, 'speechiness': 0.0879, 'acousticness': 0.00118, 'instrumentalness': 0.32, 'liveness': 0.4, 'valence': 0.28, 'tempo': 126.001, 'type': 'audio_features', 'id': '67HGEuWBJOmCJfgeoELIZe', 'uri': 'spotify:track:67HGEuWBJOmCJfgeoELIZe', 'track_href': 'https://api.spotify.com/v1/tracks/67HGEuWBJOmCJfgeoELIZe', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/67HGEuWBJOmCJfgeoELIZe', 'duration_ms': 204375, 'time_signature': 4}, 'genres': []}, {'trackName': 'LostInSpace-TimoRommeRemix', 'trackId': '1DVf9QsN4a5pCa2TVw2qnn', 'artistNames': ['MOTi', 'AERO5', 'Timo Romme'], 'artistIds': ['1vo8zHmO1KzkuU9Xxh6J7W', '6KkDl8hG9xuLpLyrk1oFP6', '7GbhdrDJkFO9fMhsRY0LRm'], 'audioFeatures': {'danceability': 0.641, 'energy': 0.886, 'key': 11, 'loudness': -4.913, 'mode': 0, 'speechiness': 0.037, 'acousticness': 0.0146, 'instrumentalness': 0.874, 'liveness': 0.265, 'valence': 0.199, 'tempo': 124.006, 'type': 'audio_features', 'id': '1DVf9QsN4a5pCa2TVw2qnn', 'uri': 'spotify:track:1DVf9QsN4a5pCa2TVw2qnn', 'track_href': 'https://api.spotify.com/v1/tracks/1DVf9QsN4a5pCa2TVw2qnn', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/1DVf9QsN4a5pCa2TVw2qnn', 'duration_ms': 240000, 'time_signature': 4}, 'genres': ['big room', 'deep big room', 'edm', 'electro house', 'house', 'pop', 'pop edm', 'progressive electro house', 'progressive house', 'tropical house']}]
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
    for artist in userTopArtists:  
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
    createPlaylistResponse = spotifyCreate.newPlaylist(userName, "+| MiC Tailored Set |+","Inspired by {}. Created via Music in Context ++2020 Jtokarowski++".format(DJ))
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