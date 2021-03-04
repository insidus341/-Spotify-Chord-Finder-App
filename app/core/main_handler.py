from app.core.controllers.spotify import Spotify
from app.core.controllers.database import Database
from app.core.controllers.settings import get_env
from app.core.controllers.sessions import Session
from app.core.controllers.spotify_songs import Spotify_songs

from app.core.singleton import Singleton

import requests

@Singleton
class Core():
 
    def __init__(self):
        self.database = Database.Instance()
        self.spotify = Spotify.Instance()
        self.session = Session.Instance()
        self.spotify_songs = Spotify_songs.Instance()

    def check_user_logged_in(self):
        pass

    def user_login(self, connected_clients_ip):
        if connected_clients_ip is None or not isinstance(connected_clients_ip, str):
            return False

        redirect_url = self.spotify.get_callback_url(connected_clients_ip)
        return redirect_url
    
    def user_logout(self):
        self.session.delete_user_session_token()

    def spotify_callback(self, connected_clients_ip, spotify_code, spotify_state):
        print("main_handler.callback")
        try:
            if self.returning_user():
                print("Is a returning user")
                return

            if not self.check_user_callback_is_valid(connected_clients_ip, spotify_code, spotify_state):
                print("Is not a valid callback")
                return
            
            self.process_spotify_authentication_code(spotify_code, connected_clients_ip)
        
        except Exception as e:
            print(e)
            return

    def check_user_callback_is_valid(self, connected_clients_ip, spotify_code, spotify_state):
        if connected_clients_ip is None or not isinstance(connected_clients_ip, str):
            return False
        if spotify_code is None or not isinstance(spotify_code, str):
            return False
        if spotify_state is None or not isinstance(spotify_state, str):
            return False
        
        state_check = self.spotify.check_spotify_state_exists(spotify_state, connected_clients_ip)
        if state_check:
            self.spotify.delete_spotify_authorization_challenge(spotify_state)
        
        return state_check

    def process_spotify_authentication_code(self, spotify_code, connected_clients_ip):
        print("processing authentication code")
        
        # Generate access and refresh tokens from the authentication code
        spotify_access_and_refresh_tokens = self.spotify.generate_spotify_access_tokens(spotify_code, connected_clients_ip)

        # user the access token to get their spotify user details, such as their username, id and email address
        spotify_access_token = spotify_access_and_refresh_tokens['access_token']
        spotify_user_details = self.spotify.get_spotify_user_details(spotify_access_token)

        spotify_user_id = spotify_user_details['id']
        # existing_user_id = self.database.read_spotify_user_data(spotify_user_id)
        existing_user_id = self.database.read_spotify_user_id_from_spotify_id(spotify_user_id)

        # Existing user
        if existing_user_id:
            print("is an existing user")

            user_access_tokens_exist = self.database.read_user_access_tokens(existing_user_id)
            
            # user exists and they have existing access/refresh tokens
            # we must override the existing tokens 
            if user_access_tokens_exist:
                self.database.update_user_access_token(existing_user_id, spotify_access_and_refresh_tokens, True)
                
            # user exists but they don't have any access tokens
            elif user_access_tokens_exist is None:
                self.database.insert_spotify_user_access_tokens(existing_user_id, spotify_access_and_refresh_tokens)
            
        # New user
        # Save their user details and save their access tokens
        elif existing_user_id is None:
            print("is not an existing user, inserting")
            print(spotify_user_details)
            print(connected_clients_ip)
            print("")
            print(spotify_access_and_refresh_tokens)

            user_id = self.database.insert_spotify_user(spotify_user_details, connected_clients_ip)
            print(user_id)
            
            self.database.insert_spotify_user_access_tokens(user_id, spotify_access_and_refresh_tokens)
            existing_user_id = user_id
        
        # create user login tokens
        self.session.create_user_login_token(existing_user_id)       

    def returning_user(self):
        user_session_exists = self.session.check_if_user_session_token_is_valid()

        if user_session_exists:
            self.session.update_user_session_token()
            return True
        
        return False 

    def get_current_playing_song(self):
        if not self.returning_user():
            return False

        try: 
            user_id = self.session.get_user_id_from_session()
            if not user_id:
                return False
            
            current_song = self.spotify.get_current_playing_song(user_id)
            song_name = current_song['item']['name']
            artist_name = current_song['item']['artists'][0]['name']
            album_name = current_song['item']['album']['name']
            spotify_uri = current_song['item']['uri']

            current_song_tab_url = self.spotify_songs.get_song_chords_url(spotify_uri, song_name, artist_name, album_name)

            output = {
                "ok": True,
                "song": {
                    "song_name": song_name,
                    "artist_name": artist_name,
                    "album_name": album_name,
                    "chords_url": current_song_tab_url
                }
            }

            return output
        
        except Exception as e:
            print(e)
            return False 

    def get_user_details(self):
        if not self.returning_user():
            return False

        user_id = self.session.get_user_id_from_session()
        user_data = self.database.read_spotify_user_data(user_id)
        return user_data
