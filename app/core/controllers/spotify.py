from app.core.controllers.database import Database
from app.core.singleton import Singleton
from app.core.controllers.settings import get_env
from app.core.controllers.functions import web_request_get, web_request_post

from datetime import datetime

import secrets

@Singleton
class Spotify():

    database = Database.Instance()
    
    # Retrieves a login URL from spotify using our client ID and redirect uri
    # Returns the login URL
    def get_callback_url(self, connected_clients_ip):
        if connected_clients_ip is None or not isinstance(connected_clients_ip, str):
            return False    

        url = "https://accounts.spotify.com/authorize"

        # Get a random state to use
        random_state = self._generate_random_state()
        if not random_state:
            return False
        
        # Saved the state in the database to use for later
        state_saved = self._save_generated_random_state(random_state, connected_clients_ip)
        if not state_saved:
            return False

        # Fill out our HTTP parameters
        params = {
            "client_id": get_env("SPOTIFY_CLIENT_ID"),
            "response_type": "code",
            "redirect_uri": get_env("APP_URL") + get_env("SPOTIFY_REDIRECT_URI"),
            "scope": "user-read-email user-read-private user-read-currently-playing user-modify-playback-state user-read-playback-state",
            "state": random_state
        }

        headers = {'content-type': 'application/json'}
        
        # Generate the redirect URL
        redirect_url = self._get_callback_url_web_request_to_spotify(url, params, headers)
        if not redirect_url:
            return False

        return redirect_url

    # Reach out to spotify with out client_id, redirect_uri, scope and random state
    # We expect an HTTP 200 back and a response URL
    def _get_callback_url_web_request_to_spotify(self, url, params, headers):
        try: 
            response = web_request_get(headers, params, url)
            status_code = response.status_code
            
            # TODO 200 is always returned. Must confirm client_id, scope, state is correct
            if status_code != 200:
                raise ValueError("Spotify did not return an HTTP 200 for our Authorization request")

            # Return the login url. We will redirect the user to this 
            return response.url         
        
        except Exception as e:
            print(e)
            return False

    # Generates a random token from the Secrets library
    def _generate_random_state(self):
        try:
            random_state = secrets.token_urlsafe(16)
            return random_state
        except:
            raise Exception("Unable to generate random secret state")
            

    # Saves the state in the database
    def _save_generated_random_state(self, random_state, connected_clients_ip):
        state = self.database.insert_spotify_authorization_challenge(random_state, connected_clients_ip)
        return state

    # Check that the state exists in our database and that the clients public IP matches
    # If either the state or clients IP do not match, we return an error
    def check_spotify_state_exists(self, spotify_state, connected_clients_ip):
        # TODO confirm state code is less than a minute old
        state_check_record = self.database.read_spotify_authorization_challenge(spotify_state, connected_clients_ip)
        
        if state_check_record == spotify_state:
            return True
        
        return False
    
    def delete_spotify_state(self, spotify_state):
        self.database.delete_spotify_authorization_challenge(spotify_state)
        return True


    # Send our authorization code to Spotify to generate access and refresh tokens
    def generate_spotify_access_tokens(self, spotify_code, connected_clients_ip):
        if connected_clients_ip is None or not isinstance(connected_clients_ip, str):
            raise ValueError(f"connected_clients_ip ({connected_clients_ip}) is not a good string")
        if spotify_code is None or not isinstance(spotify_code, str):
            raise ValueError(f"spotify_code ({spotify_code}) is not a good string")

        url = "https://accounts.spotify.com/api/token"

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
            'Authorization': get_env("SPOTIFY_CLIENT_BASIC")
        }

        params = {
            "code": spotify_code,
            "grant_type": "authorization_code",
            "redirect_uri": get_env("APP_URL") + get_env("SPOTIFY_REDIRECT_URI"),
        }

        # Make the request against Spotify
        token_data = self.generate_spotify_access_tokens_web_request(url, headers, params)
        return token_data
    
    # Makes the web request against Spotify and returns Access and Refresh Token
    # We throw an error if the returned status_code is not an HTTP 200
    def generate_spotify_access_tokens_web_request(self, url, headers, params):
        print("generating spotify access tokens")
        response = web_request_post(headers, params, url)
        status_code = response.status_code
        
        if status_code != 200:
            print("Spotify did not return an HTTP 200 for our access tokens request")
            raise ValueError("Spotify did not return an HTTP 200 for our access tokens request")

        # Return the response data
        return response.json()

    # Makes a request against Spotify to get user data
    # This requres an Access Token
    # We throw an error if the returned status_code is not an HTTP 200
    def get_spotify_user_details(self, access_token):
        print("getting spotify user details")

        url = "https://api.spotify.com/v1/me"

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
            'Authorization': f"Bearer {access_token}"
        }

        spotify_user_details = self.get_spotify_user_details_web_request(url, headers)
        print(spotify_user_details)

        return spotify_user_details

    def get_spotify_user_details_web_request(self, url, headers):
        response = web_request_get(headers, url=url)
        status_code = response.status_code

        if status_code != 200:
            raise ValueError("Spotify did not return an HTTP 200 for our user details request")
        
        # jsonify the response and return the user data
        spotify_user_details = response.json()
        print(spotify_user_details)

        return spotify_user_details

    def update_user_access_token_if_invalid(self, authentication_data):
        user_id = authentication_data[0][1]
        # access_token = authentication_data[0][2]
        refresh_token = authentication_data[0][3]
        token_generated = datetime.timestamp(authentication_data[0][4])
        token_expires_in = authentication_data[0][5]

        user_access_token_expired = self.check_if_user_access_token_is_expired(token_expires_in, token_generated)

        # If the access token has expired, refresh it
        if user_access_token_expired:
            new_access_tokens = self.refresh_user_access_tokens(refresh_token)
            self.save_new_access_token_for_user(user_id, new_access_tokens)
            
            return new_access_tokens['access_token']
        
        return None
    
    def check_if_user_access_token_is_expired(self, expires_in, generated):
        # Get the timestamp of NOW
        now = datetime.timestamp(datetime.now())
        
        expires_at = generated + expires_in
        time_difference = expires_at - now
        print(time_difference)

        if time_difference < 600:
            return True
        else:
            return False

    def refresh_user_access_tokens(self, refresh_token):
        if refresh_token is None or not isinstance(refresh_token, str):
            raise ValueError(f"refresh_token ({refresh_token}) is not a good string")

        print("Refreshing user access tokens")

        url = "https://accounts.spotify.com/api/token"

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
            'Authorization': get_env("SPOTIFY_CLIENT_BASIC")
        }

        params = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        new_user_access_token = self.refresh_user_access_tokens_web_request(url, headers, params)
        return new_user_access_token

    def refresh_user_access_tokens_web_request(self, url, headers, params):
        response = web_request_post(headers, params, url)
        status_code = response.status_code
        
        if status_code != 200:
            raise ValueError("Spotify did not return an HTTP 200 for our access tokens request")

        # Return the response data
        return response.json()

    def save_new_access_token_for_user(self, user_id, new_access_tokens):
        self.database.update_user_access_token(user_id, new_access_tokens)

    def retrieve_user_access_token(self, user_id):
        current_user_spotify_authentication = self.database.read_user_access_tokens(user_id)
        if current_user_spotify_authentication is None:
            return None

        new_access_token = self.update_user_access_token_if_invalid(current_user_spotify_authentication)

        if new_access_token is not None:
            user_access_token = new_access_token
        else:
            user_access_token = current_user_spotify_authentication[0][2]

        return user_access_token 

    
    def get_current_playing_song(self, user_id):
        user_access_token = self.retrieve_user_access_token(user_id)
        
        if user_access_token is not None:
            url = "https://api.spotify.com/v1/me/player"

            headers = {
                'Authorization': f"Bearer {user_access_token}"
            }

            users_current_playing_song = self.get_current_playing_song_web_request(url, headers)
            print("current song: {0}".format(users_current_playing_song))
            return users_current_playing_song

    def get_current_playing_song_web_request(self, url, headers=None, params=None):
        response = web_request_get(headers, params, url)
        status_code = response.status_code
        
        if status_code != 200:
            raise ValueError("Spotify did not return an HTTP 200 when getting the current playing song")

        return response.json()

        


        

        
