import requests
import os
from dotenv import load_dotenv


load_dotenv()

KEY = os.getenv("KEY")


def get_information_from_response(data):
    d = {}
    sep = '...'
    d['id'] = data['id']
    try:
        d['title'] = data['title'] + ' ' + data['description']
    except KeyError:
        d['title'] = data['fullTitle']
    try:
        d['description'] = data['plot'].split(sep, 1)[0]
    except AttributeError:
        d['description'] = data['plot']
    d['image'] = data['image']
    d['genre'] = data['genres']
    d['stars'] = data['stars']
    d['rating'] = data['imDbRating']
    return d


def request_movie_information(fid):
    if KEY == '':
        print('IMDB API key is empty')
        return
    response = requests.get("https://imdb-api.com/en/API/Title/" + KEY + "/" + fid)
    if response.status_code != 200:
        print('Unsuccessful IMDB request')
        return
    result = response.json()

    return get_information_from_response(result)


def imdb_top_250_movies():
    response = requests.get("https://imdb-api.com/API/AdvancedSearch/" + KEY + "?groups=top_1000&count=250")
    if response.status_code != 200:
        print('Unsuccessful IMDB request')
        return
    result = response.json()['results']
    titles_list = []
    for i in range(len(result)):
        titles_list.append(get_information_from_response(result[i]))
    return titles_list


def imdb_top_250_by_genre(genre):
    response = requests.get("https://imdb-api.com/API/AdvancedSearch/" + KEY + "?genres=" + genre + "&count=250")
    if response.status_code != 200:
        print('Unsuccessful IMDB request')
        return
    result = response.json()['results']
    titles_list = []
    for i in range(len(result)):
        titles_list.append(get_information_from_response(result[i]))
    return titles_list


def imdb_req(keywords='love'):
    if KEY == '':
        print('IMDB API key is empty')
        return
    response = requests.get("https://imdb-api.com/API/AdvancedSearch/" + KEY + "?keywords=" + keywords + "&count=50")
    if response.status_code != 200:
        print('Unsuccessful IMDB request')
        return
    result = response.json()['results']
    titles_list = []
    for i in range(len(result)):
        titles_list.append(get_information_from_response(result[i]))
    return titles_list


if __name__ == '__main__':
    request_movie_information('tt1375666')
