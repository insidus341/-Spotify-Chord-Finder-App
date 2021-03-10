from app.core.controllers.database import Database
from app.core.singleton import Singleton
from app.core.controllers.settings import get_env
from app.core.controllers.functions import web_request_get, web_request_post, google_search

from datetime import datetime

import re

@Singleton
class Spotify_songs():

    database = Database.Instance()

    def get_song_chords_url(self, spotify_uri, song_name, artist_name, album_name=''):
        # if we have saved song and chord data for this song already, lets not waste a Google API call
        saved_song = self.get_song_from_database(spotify_uri)
        print("saved_song: {0}".format(saved_song))
        if saved_song:
            # url = saved_song[5]
            # is_valid = saved_song[6]
            # is_failing_search = saved_song[7]
            return saved_song

        # Get the chords url, if it exists
        (status, chords_url) = self.get_chords_url_from_google_search_api(song_name, artist_name)
        print("chords_url: {0}".format(chords_url))
        
        # If we have a good chord URL, let's save this alongside the spotify song data
        # return the chords URL
        if status == 200 and chords_url is not None:
            print("saving song into database")
            self.save_song_into_database(song_name, artist_name, album_name, spotify_uri, chords_url, True, False)
            
            return self.get_song_from_database(spotify_uri)
        
        # We're getting a 429 instead of the chords URL. Lets save this song for now, we can update this later
        elif status == 429 and chords_url is None:
            print("saving partial song info")
            self.save_song_into_database(song_name, artist_name, album_name, spotify_uri, "-", False, True)

            return False
        
        # return no chords URL if we can't find one
        return False

    def get_song_from_database(self, spotify_uri):
        saved_song = self.database.read_song_data(spotify_uri)
        return saved_song

    def save_song_into_database(self, song_name, artist_name, album_name, spotify_uri, chords_url, is_valid, is_failing_search ):
        song_saved = self.database.insert_song_data(song_name, artist_name, album_name, spotify_uri, chords_url, is_valid, is_failing_search)
        return song_saved

    def get_chords_url_from_google_search_api(self, song_name, artist_name):
        google_api_key = get_env('GOOGLE_SEARCH_API_KEY')
        google_engine_id = get_env('GOOGLE_SEARCH_ENGINE_ID')
        num_of_results = 1
        search_string = self.format_google_search_string(song_name, artist_name)
        print(f" log: searching for {search_string}")

        # return google_search(search_string)

        url = f"https://customsearch.googleapis.com/customsearch/v1?key={google_api_key}&cx={google_engine_id}&num={num_of_results}&q={search_string}"
        response = web_request_get(url=url)
        status = response.status_code
        if status == 200:
            response_json = response.json()

            if response_json['searchInformation']['totalResults'] != '0':
                chords_url = response_json['items'][0]['link']

        if response.status_code != 200:
            print("unable to get song from Google, status code {0}".format(response.status_code))
            chords_url = None

        return (status, chords_url)

    def format_google_search_string(self, song_name, artist_name):
        concatinated = f"site:tabs.ultimate-guitar.com {song_name} {artist_name} guitar tab"
        # formated = re.sub("[ ,-]", "+", concatinated)

        return concatinated