from googlesearch import search
import requests

def web_request_get(headers={}, params={}, url=None):
    if url is None:
        return False

    request = requests.session()
    request.headers = headers
    request.params = params

    response = request.get(url)
    return response

def web_request_post(headers, params, url):
    request = requests.session()
    request.headers = headers
    request.params = params

    response = request.post(url)
    return response

def google_search(search_string):
    out = search(search_string, num_results=0)
    print(out)

    if len(out) == 1:
        return out[0]
    else:
        return None
