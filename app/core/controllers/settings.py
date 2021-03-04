from dotenv import load_dotenv
import os

load_dotenv('.env') # for local dev

def get_env(environmental):
    try:
        env = os.getenv(environmental)
        return env
    except Exception as e:
        print(e)
        return False
