README

Simple web app to get user spotify playlist data and run analysis on it

Goal functionality- scrape DJ sets from mixesdb.com, make playlist, examine set structure

Current version
Step0: User logs into spotify, application gets Auth Token
Step1: Application uses token to retireve all user playlists
Step2: Application retrieves all song URI's in all playlists
Step3: Application Retrieves all song attributes for all URI's
Step4: Analysis- Logistic Regression, Kmeans, Etc.

Code adapted from several Github repositories including:

https://github.com/drshrey/spotify-flask-auth-example