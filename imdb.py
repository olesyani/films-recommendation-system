import requests

# в переменной KEY должен лежать ключ для работы с IMDB API
KEY = ""


def get_movie_titles(data):
    titles_list = []
    for i in range(len(data)):
        d = {}
        d['id'] = data[i]['id']
        d['title'] = data[i]['title'] + ' ' + data[i]['description']
        d['description'] = data[i]['plot']
        d['image'] = data[i]['image']
        d['genre'] = data[i]['genres']
        d['stars'] = data[i]['stars']
        titles_list.append(d)
    return titles_list


def imdb_top_250_movies():
    response = requests.get("https://imdb-api.com/API/AdvancedSearch/" + KEY + "?groups=top_250&count=250")
    if response.status_code != 200:
        print('Unsuccessful IMDB request')
        return
    result = response.json()['results']

    return get_movie_titles(result)


def imdb_req(keywords='love'):
    if KEY == '':
        print('IMDB API key is empty')
        return
    response = requests.get("https://imdb-api.com/API/AdvancedSearch/" + KEY + "?keywords=" + keywords + "&count=25")
    if response.status_code != 200:
        print('Unsuccessful IMDB request')
        return
    result = response.json()['results']

    return get_movie_titles(result)


if __name__ == '__main__':
    imdb_req()
