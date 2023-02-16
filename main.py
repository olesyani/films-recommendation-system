import vk_api
import re
import db
from imdb import imdb_req, imdb_top_250_movies
from collections import Counter
from deep_translator import GoogleTranslator


TOKEN = ''
DATABASE = ''
PASSWORD = ''


POSTS_N = 100
COMMUNITIES_N = 300
KEYWORDS_N = 5


def word_translate(word='сон'):
    translation = GoogleTranslator(source='auto', target='en').translate(word)
    return translation


def clear_text(text):
    return re.sub(r'[^а-яА-Яa-zA-Z ]+', ' ', text.replace('ё', 'е').lower()).split()


def get_user_id(vk_session, screen_name):
    vk = vk_session.get_api()
    person_id = vk.users.get(user_ids=screen_name)
    try:
        return person_id[0]['id']
    except IndexError:
        print('There is no person with that ID')
        return None


def recommendations_from_vk(tools, owner_id):
    print('VK recommendations in progress..')
    wall = tools.get_all('wall.get', POSTS_N, {'owner_id': owner_id})
    wall_items = wall['items']

    wall_text = ""
    for i in range(wall['count']):
        wall_text += wall_items[i]['text']
        try:
            wall_text += wall_items[i]['copy_history'][0]['text']
        except KeyError:
            continue
        wall_text += ' '

    wall_text = clear_text(wall_text)
    words = [x for x in wall_text if len(x) >= 3]
    count = list(Counter(words).most_common())

    movies_list = []
    for i in count[:KEYWORDS_N]:
        w = word_translate(i[0])
        movies_list.extend(imdb_req(w))

    movies_list = [dict(t) for t in {tuple(d.items()) for d in movies_list}]

    return movies_list


def add_250_top_movies_to_db(frsdb: db.FRSDatabase):
    tmp = imdb_top_250_movies()
    for i in range(len(tmp)):
        if frsdb.find_info(tmp[i]['id']) == {}:
            frsdb.insert_film_info(
                film_id=tmp[i]['id'],
                film_desc=tmp[i]['description'],
                film_image=tmp[i]['image'],
                film_title=tmp[i]['title'],
                film_genres=tmp[i]['genre'],
                film_stars=tmp[i]['stars']
            )


def start(frsdb: db.FRSDatabase, person_id):
    if TOKEN != '':
        vk_session = vk_api.VkApi(token=TOKEN)
        tools = vk_api.VkTools(vk_session)
        try:
            person_id = int(person_id)
        except ValueError:
            person_id = get_user_id(vk_session, person_id)
            if person_id is None:
                return 0, 0
        if frsdb.check_if_user_exists(person_id) is None:
            movies = recommendations_from_vk(tools, person_id)
            for i in range(len(movies)):
                if frsdb.find_info(movies[i]['id']) == {}:
                    frsdb.insert_film_info(
                        film_id=movies[i]['id'],
                        film_desc=movies[i]['description'],
                        film_image=movies[i]['image'],
                        film_title=movies[i]['title'],
                        film_genres=movies[i]['genre'],
                        film_stars=movies[i]['stars']
                    )
                frsdb.insert_recommendation(film_id=movies[i]['id'], user_id=person_id)
        films = []
        recs = frsdb.get_undefined_user_recommendations(person_id)
        if recs:
            for i in range(len(recs)):
                films.append(frsdb.find_info(recs[i]['film']))
            return person_id, films
        else:
            return None, None
    else:
        print('Token is empty')
        return


if __name__ == '__main__':
    FRSDB = db.FRSDatabase(DATABASE, PASSWORD)
    start(FRSDB, 'olesyanikolaevaa')
    FRSDB.close()
