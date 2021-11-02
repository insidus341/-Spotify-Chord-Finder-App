import requests

url = "https://tabs.ultimate-guitar.com/tab/ed-sheeran/photograph-tabs-1499208"

response = requests.get(url)
status_code = response.status_code
content = response.content.decode("utf-8")

print(content)




