from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import requests, sys, os
import sqlite3


# ----------------------- GET JP SONGS SCAPRED ON JLYRIC -----------------------
def scrapeFromJLyric(artist_name, song_name, lyric_site_url):
	print("Scraping song : '{}' by '{}'".format(song_name, artist_name))
	browser.get(lyric_site_url)
	browser.implicitly_wait(1)
	song_name_input   =  browser.find_element_by_name('kt')
	artist_name_input =  browser.find_element_by_name('ka')
	song_name_input.send_keys(song_name)
	artist_name_input.send_keys(artist_name)
	artist_name_input.submit()
	browser.implicitly_wait(1)
	try:
		browser.find_element_by_xpath(".//*[@id='lyricList']/div[2]/div[2]/a").send_keys(Keys.ENTER)
		browser.implicitly_wait(1)
		lyric_text = browser.find_element_by_xpath(".//*[@id='lyricBody']").text
		print ('Song found. Processing...\n')
		print(lyric_text)
	except:
		print ("---------- Song not found. ----------\n")

	return lyric_text


def addLyricToDBByArtistName(db_name, artist_name, api_key):
	api_method_name  = "track.search"
	api_url          = "http://api.musixmatch.com/ws/1.1/" + api_method_name + "?apikey=" + api_key
	conn = sqlite3.connect(db_name)
	c = conn.cursor()
	payload = { 
				'format'      : 'json',
				'page'        : 1,
				'page_size'   : 100,
				'q_artist'    : artist_name,
	}
	res = requests.get(api_url, params=payload)
	for i in range(100):
		try:
			track_info = res.json()['message']['body']['track_list'][i]['track']
			if track_info['has_lyrics'] == 0:
				title    = track_info['track_name']
				artist   = track_info['artist_name']
				album    = track_info['album_name']
				track_id = track_info['track_id']
				lyric    = scrapeFromJLyric(artist_name, title, j_lyrics_url)

				c.execute("INSERT INTO songs (title, artist, album, track_id, lyric) VALUES (?, ?, ?, ?, ?)", (title, artist, album, track_id, lyric))
				conn.commit()
		except:
			pass

	conn.close()



def getChartArtist(country, api_key):
	chart_artist_list = []
	api_method_name   = 'chart.artists.get'
	api_url           = "http://api.musixmatch.com/ws/1.1/" + api_method_name + "?apikey=" + api_key
	payload = { 
				'country'     : country,
				'page'        : 1,
				'page_size'   : 100,
				'format'      : 'json',
	}
	res = requests.get(api_url, params=payload)
	chart_artists_info = res.json()['message']['body']['artist_list']

	for i in range(100):
		chart_artist_list.append(chart_artists_info[i]['artist']['artist_name'])

	return chart_artist_list




# ----------------------- GET US SONGS LYRIC FROM MUSIXMATCH -----------------------
def getChartTrack(country, api_key):
	chart_track_list = []
	api_method_name  = 'chart.tracks.get'
	api_url          = "http://api.musixmatch.com/ws/1.1/" + api_method_name + "?apikey=" + api_key
	payload = { 
				'country'     : country,
				'page'        : 1,
				'page_size'   : 100,
				'format'      : 'json',
				'f_has_lyrics': 1,
	}
	res = requests.get(api_url, params=payload)
	chart_tracks_info = res.json()['message']['body']['track_list']
	for i in range(100):
		track_name  = chart_tracks_info[i]['track']['track_name']
		artist_name = chart_tracks_info[i]['track']['artist_name']
		album_name  = chart_tracks_info[i]['track']['album_name']
		track_id    = chart_tracks_info[i]['track']['track_id']

		chart_track_list.append((track_name, artist_name, album_name, track_id))

	return chart_track_list


def getLyric(track_id, api_key):
	api_method_name   = 'track.lyrics.get'
	api_url           = "http://api.musixmatch.com/ws/1.1/" + api_method_name + "?apikey=" + api_key
	payload = { 
				'track_id' : track_id,
				'format'   : 'json',
	}
	res = requests.get(api_url, params=payload)
	lyric = res.json()['message']['body']['lyrics']['lyrics_body']

	return lyric


def addLyricToDB(db_name, chart_track_list, api_key):
	conn = sqlite3.connect(db_name)
	c = conn.cursor()
	for (title, artist, album, track_id) in chart_track_list:
		lyric = getLyric(track_id, api_key)
		print ("Adding song : '{}' by '{}'".format(title, artist))
		c.execute("INSERT INTO songs (title, artist, album, track_id, lyric) VALUES (?, ?, ?, ?, ?)", (title, artist, album, track_id, lyric))
		conn.commit()
	conn.close()





if __name__ == '__main__':
	browser      = webdriver.PhantomJS(r"C:\Program Files\phantomjs-2.1.1-windows\bin\phantomjs.exe")
	api_key      = "YOUR_API_KEY"
	j_lyrics_url = 'http://j-lyric.net/'
	db_name      = 'songsUS.db'

	# ==== Add scraped songs without lyrics for Japanese chart Artists ==== 
	# chart_artist_list =  getChartArtist('jp', api_key)
	# for chart_artist in chart_artist_list:
		# addLyricToDBByArtistName(db_name, chart_artist, api_key)

	# ==== Add US chart songs with lyrics from Musixmatch ==== 
	chart_track_list  = getChartTrack('us', api_key)
	addLyricToDB(db_name, chart_track_list, api_key)