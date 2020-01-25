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


SECRET_KEY = 'development'

#grab date program is being run
td = date.today()
TODAY = td.strftime("%Y%m%d") ##YYYYMMDD
YEAR = td.strftime("%Y") ##YYYY
NICEDATE = td.strftime("%b %d %Y") ##MMM DD YYYY

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
            return render_template("index.html", title='Home', user=userName, token=access_token, refresh=refresh_token, link=refreshPage, url=imgurl, form=form)
        else:
            dataString = ",".join(formData)
            analysisPageSelections = "{}&data={}".format(analysisPage, dataString)
            return redirect(analysisPageSelections) 
    else:
        print(form.errors)

    return render_template("index.html", title='Home', user=userName, token=access_token, refresh=refresh_token, link=refreshPage, url=imgurl, form=form)

@app.route("/analysis", methods=["GET"])
def analysis():

    featuresList = ['acousticness','danceability','energy','instrumentalness','liveness','speechiness','valence']

    access_token = request.args.get("access_token")
    refresh_token = request.args.get("refresh_token")
    token_type = "Bearer"
    expires_in = request.args["expires_in"]

    #raw data from the checklist (a list of playlist URIs specifically)
    pldata = request.args["data"]

    unpackedData = pldata.split(",")

    d = data(access_token)
    prof = d.profile()
    userName = prof.get("userName")

    #retrieve songs and analysis for user selected playlistsDB
    masterSongList=[]
    for i in range(len(unpackedData)):
        songs = d.getPlaylistTracks(unpackedData[i])
        masterSongList.extend(songs)

    playlistsongs = d.trackFeatures(masterSongList)

    #testing the audio analysis method
    #response = d.getAudioAnalysis("3YwyAnL9NlqAK9V833qiGz")
    #print(response)
    #input()

    #top = d.getTop50()
    #rec = d.getRecentSongs()

    ################################################################################################
    ## EXPERIMENTAL REC FUNCTION ###

    # test_target_1 = { 
    # "target_danceability": 0.808,
    # "target_energy": 0.626,
    # "target_speechiness": 0.168,
    # "target_acousticness": 0.00187,
    # "target_instrumentalness": 0.159,
    # "target_liveness": 0.376,
    # "target_valence": 0.369,
    # "target_key":0,
    # "min_tempo": 120,
    # "max_tempo": 130
    # }
    
    # test_target_3 = { 
    # "target_danceability": 0.5,
    # "target_energy": 0.5,
    # "target_speechiness": 0.5,
    # "target_acousticness": 0.5,
    # "target_instrumentalness": 0.5,
    # "target_liveness": 0.5,
    # "target_valence": 0.5,
    # "target_key":0
    # }

    # recommendations = d.getRecommendations(limit=100, seed_artists='10gzBoINW3cLJfZUka8Zoe')
    # song_ids = []
    # song_ids2 = []
    # song_ids3 = []
    # song_ids4 = []
    # for reco in recommendations:
    #     song_ids.append(reco["trackId"])
    # recommendations2 = d.getRecommendations(limit=100, seed_artists='10gzBoINW3cLJfZUka8Zoe',targets=test_target_1)
    # for reco2 in recommendations2:
    #     song_ids2.append(reco2["trackId"])
    # recommendations3 = d.getRecommendations(limit=100, seed_artists='10gzBoINW3cLJfZUka8Zoe',targets=test_target_2)
    # for reco3 in recommendations3:
    #     song_ids3.append(reco3["trackId"])
    # recommendations4 = d.getRecommendations(limit=100, seed_artists='10gzBoINW3cLJfZUka8Zoe',targets=test_target_3)
    # for reco4 in recommendations4:
    #     song_ids4.append(reco3["trackId"])

    # allrecs = []
    # allrecs.extend(song_ids)
    # allrecs.extend(song_ids2)
    # allrecs.extend(song_ids3)
    # allrecs.extend(song_ids4)
    # # insert the list to the set 
    # list_set = set(allrecs) 
    # # convert the set to the list 
    # unique_list = (list(list_set))
    # print(unique_list) 
    # print(len(unique_list))

    # print(song_ids)
    # print(song_ids2)
    # print(song_ids3)

    # new_ids = []
    # for sid in song_ids2:
    #   if not sid in song_ids:
    #     new_ids.append(sid)
    # print(len(new_ids))

    # input()

    stTop = d.getMyTop(topType='artists', term='short_term', limit=10)
    mtTop = d.getMyTop(topType='artists', term='medium_term', limit=10)
    ltTop = d.getMyTop(topType='artists', term='long_term', limit=10)

    artists = []
    artists.extend(stTop)
    artists.extend(mtTop)
    artists.extend(ltTop)

    topArtistIds = []
    for artist in artists:
        topArtistIds.append(artist['artist_id'])

    #remove dupes
    topArtistIds = list(set(topArtistIds))

    test_target_1 = { 
    "target_danceability": 1,
    "target_energy": 1,
    "target_speechiness": 1,
    "target_acousticness": 1,
    "target_instrumentalness": 1,
    "target_liveness": 1,
    "target_valence": 1,
    "target_key":0
    }
    test_target_2 = { 
    "target_danceability": 0,
    "target_energy": 0,
    "target_speechiness": 0,
    "target_acousticness": 0,
    "target_instrumentalness": 0,
    "target_liveness": 0,
    "target_valence": 0,
    "target_key":0
    }


    ## Build up a large pool of options by grabbing suggestions for each
    ## of top artists, target 0 and target 1 to get almost all of pool
    masterpool = []
    for i in range(len(topArtistIds)):  
        #listToSend = topArtistIds[i:i + m]
        #stringList = ",".join(listToSend)
        recommendations = d.getRecommendations(limit=100, seed_artists=topArtistIds[i],targets=test_target_1)
        recommendations2 = d.getRecommendations(limit=100, seed_artists=topArtistIds[i],targets=test_target_2)
        masterpool.extend(recommendations)
        masterpool.extend(recommendations2)


    master_ids = []
    for j in masterpool:
        master_ids.append(j['trackId'])

    #remove dupes
    master_ids = list(set(master_ids))

    finalrecs = d.trackFeatures(masterpool)

    #targets = []
    recs = []
    recids = []
    for song in playlistsongs:
        #target = {}
        #for j in range(len(featuresList)):
        #    key = "target_{}".format(featuresList[j])
        #    target[key] = song['audioFeatures'][featuresList[j]]
 
        #################################################################
        ###MAP REDUCE WOULD BE FASTER HERE##
        
        #euclideanDistance
        TEDS=[]
        for rec in finalrecs:
            TED = 0
            for feature in featuresList:
                diff = (rec['audioFeatures'][feature]*100)-(song['audioFeatures'][feature]*100)
                TED += diff * diff
            rec["TED"] = TED
            TEDS.append(TED)

        index_min_TED = TEDS.index(min(TEDS))
        recs.append(finalrecs[index_min_TED])
        ##ENSURE SONG NOT DUPED
        #choice = finalrecs[index_min_TED]['trackId']
        recids.append(finalrecs[index_min_TED]['trackId'])
        recids = list(set(recids))
        #targets.append(target)

        

    c1 = create(access_token)
    response2 = c1.newPlaylist(userName, "+| TEST SET |+","N/A")
    r2 = response2['uri']
    fields = r2.split(":")
    plid = fields[2]
    uriList=[]
    for item in recids:
        uriList.append("spotify:track:{}".format(item))
    if len(uriList)>0:
        n = 50 #spotify playlist addition limit
        for j in range(0, len(uriList), n):  
            listToSend = uriList[j:j + n]
            stringList = ",".join(listToSend)
            response3 = c1.addSongs(plid, stringList)

    print('DONE')
    input()

   ################################################################ 
    #sort by minimum euclidean distance from coordinates of curve
    #get recomendations from first chosen song
    #as we move forward in the set, trailing 5 songs as seeds


   #  #print(d.getMyTop(topType='tracks', term='long_term'))    

    
    ################################################################
    # WORKING CLUSTER SECTION

    #set up kmeans, check how many songs
    if len(masterSongList)<5:
        clusters = len(masterSongList)
    else:
        clusters = 5

    
    statistics = stats(playlistsongs)
    statistics.kMeans(featuresList, clusters)
    df = statistics.df
    centers = statistics.centers

    #create playlists for each kmeans assignment
    c1 = create(access_token)
    repeatgenres = {}
    for i in range(clusters):
        descript = ""
        center = centers[i]
        targets = {}
        for j in range(len(featuresList)):
            entry = str(" "+str(featuresList[j])+":"+str(round(center[j],3))+" ")
            key = "target_{}".format(featuresList[j])
            #key2 = "min_{}".format(featuresList[j])
            #key3 = "max_{}".format(featuresList[j])
            targets[key] = center[j]
            #targets[key2] = center[j]-0.2
            #targets[key3] = center[j]+0.2
            descript += entry

            #we can return less detail here, maybe 'highly danceable' is sufficient

        descript +=" created on {}".format(NICEDATE)
        descript+=" by JTokarowski "

        dfi = df.loc[df['kMeansAssignment'] == i]

        genres = dfi['genres'].values.tolist()
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

        response2 = c1.newPlaylist(userName, "+| "+str(maxGenre)+" |+",descript)
        r2 = response2['uri']
        fields = r2.split(":")
        plid = fields[2]


        dfi = dfi['trackId']
        idList = dfi.values.tolist()

        uriList=[]
        for item in idList:
            uriList.append("spotify:track:{}".format(item))

        if len(uriList)>0:
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
