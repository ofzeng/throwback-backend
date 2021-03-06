"""Cloud Foundry test"""

from flask import Flask, request, redirect, jsonify, json
from operator import itemgetter

import sys
import os
import json
import codecs
import parser
import requests
import timeit

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

@app.route("/omg/lol/giffy")
def dank():
	gif = '<iframe src="//giphy.com/embed/3oEdvd2FBjUEDQ4FJS" width="480" height="270" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><p><a href="http://giphy.com/gifs/cat-motivation-motivational-speaker-3oEdvd2FBjUEDQ4FJS">via GIPHY</a></p><iframe src="//giphy.com/embed/14aUO0Mf7dWDXW" width="480" height="480" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><p><a href="http://giphy.com/gifs/embarrassed-facepalm-panda-14aUO0Mf7dWDXW">via GIPHY</a></p>'
	return gif

@app.route("/getCode")
def getCode():
	#return request.args['code']
	return requests.post("https://accounts.spotify.com/api/token", data = {"code": request.args['code'], "grant_type": "authorization_code", "redirect_uri": "https://throwback.mybluemix.net/getCode", "client_id": "b4f179be39ec4098b5b972cdad7f03fb", "client_secret": "c951d664306649d4a29f4411e1a9c56d"}).content

def match_songs_photos(songs, photos, facebook_token, spotify_token):
    #returnString = ""
    elements = [ ]
    for s in songs:
        date_string = s['added_at']
        time = dateutil.parser.parse(date_string)
        uri = s['track']['uri']
        # print time
        element = {'type': 'song', 'time': time, 'id': uri, 'title': s['track']['name']}
        elements.append(element)
    for p in photos:
        date_string = p.get('backdated_time', p['created_time'])
        comment = p.get('comment', '')
        time = dateutil.parser.parse(date_string)
        # print time
        element = {'type': 'photo', 'time': time, 'old_time': date_string, 'id': p['id'], 'comment': comment}
        elements.append(element)
        #returnString += "Adding photo + " + element + "\n"

    elements = sorted(elements,key=itemgetter('time'))
    #print "\n\nCOMBINED SONGS AND PHOTOS: " + str(elements) + "\n\n"

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
        		song_name = last_song.get('title', "NO TITLE FOUND")
        		following_photos.append({'id':element['id'], 'comment':element['comment'], 'date':element['old_time'], 'title': song_name})

    for period in time_periods:
    	if (len(period['photos']) > 7):
    	    period['photos'] = period['photos'][0:6]
    if len(time_periods) > 6:
    	time_periods = time_periods[0:5]


    comments = []
    batchRequest = []
    i = 0
    for time_period in time_periods:
    	song_id = time_period['songs'][0][14:]
    	#print "SONG ID: " + song_id + "\n"
    	song_title = requests.get('https://api.spotify.com/v1/tracks/' + song_id + '?access_token=' + spotify_token).json()
    	for photo in time_period['photos']:
    		#print "JSON OF SONG " + str(song_title) + "\n"
    		photo['song_title'] = song_title['name']
    		batchRequest.append({'method':'GET', 'relative_url':photo['id'] + '/' + 'comments'})
    		i += 1
    		if (i >= 45):
    			#print "Making request\n"
    			comments += requests.post('https://graph.facebook.com', data = {'batch':json.dumps(batchRequest), 'access_token': facebook_token}).json()
    			batchRequest = []
    			i = 0
	#print "REQUEST " + str(json.dumps(batchRequest)) + "\n"
	comments += requests.post('https://graph.facebook.com', data = {'batch':json.dumps(batchRequest), 'access_token': facebook_token}).json()
	print "COMMENTS " + str(json.loads(str(comments[0]['body']))['data'])
	#print "NUMBER COMMENTS " + str(len(comments)) + "\n"
	#counter = -1

	for time_period in time_periods:
		for photo in time_period['photos']:
			#print "i is " + str(counter) + "\n"
			#counter = counter + 1
			try:
				#print "Looking at comment: " + str(comments[0])
				photo['comment'] =  get_top_comment(json.loads(str(comments[0]['body']))['data'])#['from']['name']
				del comments[0]
			except:
				print "bad comment\n"


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

def get_top_comment(comments):
    #r = requests.get("https://graph.facebook.com/" + photo_id + "/comments?access_token=" + access_token)
    #print "MESSAGES: " + r.content + "\n"
    #response = r.json()
    #comments = response['data'] 
    
    max_likes = 0
    top_comment = ''
    for comment in comments:
    	#print "LOOKING AT COMMENT" + str(comment) + "\n"
        if comment.get('like_count', 0) >= max_likes:
            max_likes = comment.get('like_count', 0)
            top_comment = comment['from']['name'] + ': ' + comment['message']
    end = timeit.timeit()
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
	#print "\nPHOTOS: " + str(photos) + "\n"
	"""
	comments = []
	batchRequest = []
	i = 0
	for photo in photos:
		batchRequest.append({'method':'GET', 'relative_url':photo['id'] + '/' + 'comments'})
		i += 1
		if (i >= 45):
			print "Making request\n"
			comments += requests.post('https://graph.facebook.com', data = {'batch':json.dumps(batchRequest), 'access_token': facebook_token}).json()
			batchRequest = []
	#print "REQUEST " + str(json.dumps(batchRequest)) + "\n"
	comments += requests.post('https://graph.facebook.com', data = {'batch':json.dumps(batchRequest), 'access_token': facebook_token}).json()
	#print "NUMBER COMMENTS " + str(len(comments)) + "\n"
	i = 0
	for photo in photos:
		try:
			photo['comment'] =  get_top_comment(json.loads(str(comments[i]['body']))['data'])#['from']['name']
		except:
			break;
		i = i + 1
		if (i >= 45):
			break
	#print "COMMENTS " + str(comments) + "\n"
	for comment in comments:
		print "DATA in comment: " + comment['body'] + '\n'#['data'] + '\n'
		print "JSONIFIED DATA: " + str(json.loads(str(comment['body']))['data']) + "\n"
	"""
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
    time_periods = match_songs_photos(songs,photos,request.args['facebook_token'], request.args['spotify_token'])

    return jsonify({'time_periods': time_periods})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
