TEST_CONNECTED_CLIENTS_IP = '127.0.0.255'


def test_spotify_init():
    from app.core.controllers.spotify import Spotify
    spotify = Spotify.Instance()

    assert spotify is not None

def test_spotify_single_instance():
    from app.core.controllers.spotify import Spotify
    spotify_instance_1 = Spotify.Instance()
    spotify_instance_2 = Spotify.Instance()

    assert spotify_instance_1 == spotify_instance_2

def test_generate_random_state():
    from app.core.controllers.spotify import Spotify
    spotify = Spotify.Instance()

    state = spotify._generate_random_state()
    assert state

def test_save_generated_random_state():
    from app.core.controllers.spotify import Spotify
    spotify = Spotify.Instance()
    random_state = spotify._generate_random_state()

    saved_state = spotify._save_generated_random_state(random_state, TEST_CONNECTED_CLIENTS_IP)
    assert saved_state == random_state

def test_check_spotify_state_exists():
    from app.core.controllers.spotify import Spotify
    spotify = Spotify.Instance()
    random_state = spotify._generate_random_state()
        
    spotify._save_generated_random_state(random_state, TEST_CONNECTED_CLIENTS_IP)
    saved_state = spotify.check_spotify_state_exists(random_state, TEST_CONNECTED_CLIENTS_IP)
    assert saved_state is True
 
def test_get_callback_url_web_request_to_spotify():
    from app.core.controllers.spotify import Spotify
    spotify = Spotify.Instance()

    url = "https://accounts.spotify.com/authorize"
    params = {}
    headers = {}
    response_url = spotify._get_callback_url_web_request_to_spotify(url, headers, params)
    print(response_url)

def test_get_callback_url():
    from app.core.controllers.spotify import Spotify
    spotify = Spotify.Instance()

    redirect_url = spotify.get_callback_url(TEST_CONNECTED_CLIENTS_IP)
    assert "https://accounts.spotify.com" in redirect_url




# def test_generate_spotify_access_tokens():
#     pass

# def test_get_spotify_user_details():
#     pass