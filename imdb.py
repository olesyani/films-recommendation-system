import requests

# в переменной KEY должен лежать ключ для работы с IMDB API
KEY = ""


def imdb_req(keywords='love'):
    response = requests.get("https://imdb-api.com/API/AdvancedSearch/" + KEY + "?keywords=" + keywords + "&count=20")
    if response.status_code != 200:
        return 0
    result = response.json()['results']
    return result
