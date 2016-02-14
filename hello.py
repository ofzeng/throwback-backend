"""Cloud Foundry test"""

from flask import Flask, request, redirect, jsonify, json
from operator import itemgetter

import sys
import os
import json
import codecs
import parser
import requests

import dateutil.parser

app = Flask(__name__)


app.config['PROPAGATE_EXCEPTIONS'] = True

# On Bluemix, get the port number from the environment variable VCAP_APP_PORT
# When running this app on the local machine, default the port to 8080
port = int(os.getenv('VCAP_APP_PORT', 8080))

@app.route("/")
def hello():
    return request.args['facebook_token']

@app.route("/home", methods = ["GET", "POST"])
def home():
    return "Home Page"

@app.route("/getToken")
def getToken():
	return redirect("https://accounts.spotify.com/authorize/?client_id=b4f179be39ec4098b5b972cdad7f03fb&response_type=code&redirect_uri=https://throwback.mybluemix.net/getCode&scope=playlist-read-private%20user-library-read", code=302)

@app.route("/getCode")
def getCode():
	#return request.args['code']
	return requests.post("https://accounts.spotify.com/api/token", data = {"code": request.args['code'], "grant_type": "authorization_code", "redirect_uri": "https://throwback.mybluemix.net/getCode", "client_id": "b4f179be39ec4098b5b972cdad7f03fb", "client_secret": "c951d664306649d4a29f4411e1a9c56d"}).content

def match_songs_photos(songs, photos, facebook_token):
    #returnString = ""
    elements = [ ]
    for s in songs:
        date_string = s['added_at']
        time = dateutil.parser.parse(date_string)
        uri = s['track']['uri']
        # print time
        element = {'type': 'song', 'time': time, 'id': uri}
        elements.append(element)
    for p in photos:
        date_string = p.get('backdated_time', p['created_time'])
        time = dateutil.parser.parse(date_string)
        # print time
        element = {'type': 'photo', 'time': time, 'old_time': date_string, 'id': p['id']}
        elements.append(element)
        #returnString += "Adding photo + " + element + "\n"

    elements = sorted(elements,key=itemgetter('time'))
    print "\n\nCOMBINED SONGS AND PHOTOS: " + str(elements) + "\n\n"

    #return str(elements)
    #return returnString + str(elements)

    time_periods = [ ];
    last_song = None;
    following_photos = [ ];
    for element in elements:
        if (element['type'] == 'song'):
            if (last_song != '' and len(following_photos) >= 7):
                time_period = {'songs': [last_song['id']], 'photos': following_photos}
                time_periods.append(time_period)
            	following_photos = [ ]
            last_song = element
        if (element['type'] == 'photo'):
        	if last_song is not None:
        		following_photos.append({'id':element['id'], 'comment':get_top_comment(element['id'], facebook_token), 'date':element['old_time']})

    for period in time_periods:
    	if (len(period['photos']) > 7):
    	    period['photos'] = period['photos'][0:6]
    if len(time_periods) > 6:
    	time_periods = time_periods[0:5]
    return time_periods

def get_all_songs(spotify_token):
	songs = []
	next = 'https://api.spotify.com/v1/me/tracks?limit=50&offset=0'
	while (not (next is None)):
		#print "NEXT IS " + next + "\n\n"
		r = requests.get(next + '&access_token=' + spotify_token)
		response = r.json()
		#print "JSON CONTENT: " + r.content + "\n\n"
		songs.extend(response['items'])
		#return songs
		next = response['next']
	return songs

def get_top_comment(photo_id,access_token):
    comments = []

    r = requests.get("https://graph.facebook.com/"+photo_id+"/comments?access_token="+access_token)
    response = r.json()
    comments = response['data'] 
    
    max_likes = 0
    top_comment = ''
    for comment in comments:
        if comment['like_count'] > max_likes:
            max_likes = comment['like_count']
            top_comment = comment['message']

    return top_comment

def get_all_photos_tagged(facebook_token):
	photos = []
	next = 'https://graph.facebook.com/me/photos/?fields=id,created_time,backdated_time'
	while (not (next is None)):
		#print "NEXT IS " + next + "\n\n"
		r = requests.get(next + '&access_token=' + facebook_token)
		response = r.json()
		#print "JSON CONTENT: " + r.content + "\n\n"
		try:
			photos.extend(response['data'])
			next = response['paging']['next']
		except:
			break
		#return photos
	return photos

def get_all_photos_uploaded(facebook_token):
	photos = []
	next = 'https://graph.facebook.com/me/photos/uploaded/?fields=id,created_time,backdated_time'
	while (not (next is None)):
		#print "NEXT IS " + next + "\n\n"
		r = requests.get(next + '&access_token=' + facebook_token)
		response = r.json()
		#print "JSON CONTENT: " + r.content + "\n\n"
		try:
			photos.extend(response['data'])
			next = response['paging']['next']
		except:
			break
		#return photos
	return photos

def get_all_photos(facebook_token):
	photos = get_all_photos_uploaded(facebook_token)
	photos.extend(get_all_photos_tagged(facebook_token))
	print "\nPHOTOS: " + str(photos) + "\n"
	return photos

@app.route("/request", methods = ["GET"])
def process_request():
    #r = requests.get('https://graph.facebook.com/me/photos/?fields=id,created_time&access_token=' + request.args['facebook_token'])
    photos = get_all_photos(request.args['facebook_token'])
    #r.json()['data']
    # print photos
    #return str(get_all_songs(request.args['spotify_token']))
    songs = get_all_songs(request.args['spotify_token'])
    #r = requests.get('https://api.spotify.com/v1/me/tracks?limit=50&offset=100&access_token=' + request.args['spotify_token'])
    #songs = r.json()['items']
    #photos = [{'id': 'p1', 'time': '2'}, {'id': 'p2', 'time': '3'},{'id': 'p3', 'time': '5'}]
    #songs =  [{'id': 's1', 'time': 1},{'id': 's2', 'time': 4}]
    time_periods = match_songs_photos(songs,photos,request.args['facebook_token'])

    return jsonify({'time_periods': time_periods})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
