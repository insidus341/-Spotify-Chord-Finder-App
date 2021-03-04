import pytest

TEST_CONNECTED_CLIENTS_IP = '127.0.0.255'
TEST_RANDOM_STATE = 'database_test'

def test_spotify_init():
    from core.controllers.database import Database
    database = Database.Instance()

    assert database is not None

def test_spotify_single_instance():
    from core.controllers.database import Database
    database_instance_1 = Database.Instance()
    database_instance_2 = Database.Instance()

    assert database_instance_1 == database_instance_2

def test_insert_spotify_authorization_challenge():
    from core.controllers.database import Database
    database = Database.Instance()

    saved_state = database.insert_spotify_authorization_challenge(TEST_RANDOM_STATE, TEST_CONNECTED_CLIENTS_IP)
    assert saved_state == TEST_RANDOM_STATE

def test_insert_spotify_authorization_challenge_incorrect_state():
    from core.controllers.database import Database
    database = Database.Instance()

    with pytest.raises(ValueError):
        database.insert_spotify_authorization_challenge(1234556678, TEST_CONNECTED_CLIENTS_IP)

def test_insert_spotify_authorization_challenge_incorrect_client_ip():
    from core.controllers.database import Database
    database = Database.Instance()

    with pytest.raises(ValueError):
        database.insert_spotify_authorization_challenge(TEST_RANDOM_STATE, 1231245213)

def test_read_spotify_authorization_challenge():
    from core.controllers.database import Database
    database = Database.Instance()

    saved_state = database.read_spotify_authorization_challenge(TEST_RANDOM_STATE, TEST_CONNECTED_CLIENTS_IP)
    assert saved_state == TEST_RANDOM_STATE

def test_read_spotify_authorization_challenge_state_does_not_exist():
    from core.controllers.database import Database
    database = Database.Instance()

    with pytest.raises(Exception):
        database.read_spotify_authorization_challenge('random_state_that_wont_work', TEST_CONNECTED_CLIENTS_IP)

def test_read_spotify_authorization_challenge_client_ip_does_not_exist():
    from core.controllers.database import Database
    database = Database.Instance()

    with pytest.raises(Exception):
        database.read_spotify_authorization_challenge(TEST_RANDOM_STATE, '127.0.432.1')



# insert_spotify_authentication_and_userdata
# pre_insert_spotify_user
# read_spotify_user_data
# insert_spotify_user
# insert_spotify_user_access_tokens