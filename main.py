import vk_api
import re
import psycopg2
import db
from imdb import imdb_req, imdb_top_250_movies
from collections import Counter
from deep_translator import GoogleTranslator


TOKEN = ''
PASSWORD = ''


POSTS_N = 100
COMMUNITIES_N = 300
KEYWORDS_N = 5


def word_translate(word='сон'):
    translation = GoogleTranslator(source='auto', target='en').translate(word)
    return translation


def clear_text(text):
    return re.sub('[\W_]+', ' ', text.replace('ё', 'е').lower()).split()


def rate(film_id, uid, rate:True or False):
    db.rate_film(conn, cur, uid, film_id, rate)


def next_movie(uid):
    mv = db.find_next_undefined_movie(cur, uid)
    if mv is not None:
        return db.find_info(cur, mv)
    return None


def get_user_id(vk_session, screen_name):
    vk = vk_session.get_api()
    person_id = vk.users.get(user_ids=screen_name)
    try:
        return person_id[0]['id']
    except IndexError:
        print('There is no person with that ID')
        return None


def recommendations_from_vk(tools, owner_id):
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

    for i in range(len(movies_list)):
        if db.find_info(cur, movies_list[i]['id']) is None:
            db.insert_film_info(
                conn,
                cur,
                film_id=movies_list[i]['id'],
                film_desc=movies_list[i]['description'],
                film_image=movies_list[i]['image'],
                film_title=movies_list[i]['title'],
                film_genres=movies_list[i]['genre'],
                film_stars=movies_list[i]['stars']
            )
        db.insert_recommendation(
            conn,
            cur,
            film_id=movies_list[i]['id'],
            user_id=owner_id
        )


def add_250_top_movies_to_db():
    tmp = imdb_top_250_movies()
    for i in range(len(tmp)):
        if db.find_info(cur, tmp[i]['id']) is None:
            db.insert_film_info(
                conn,
                cur,
                film_id=tmp[i]['id'],
                film_desc=tmp[i]['description'],
                film_image=tmp[i]['image'],
                film_title=tmp[i]['title'],
                film_genres=tmp[i]['genre'],
                film_stars=tmp[i]['stars']
            )


def start(person_id):
    if TOKEN != '':
        vk_session = vk_api.VkApi(token=TOKEN)
        tools = vk_api.VkTools(vk_session)
        try:
            person_id = int(person_id)
        except ValueError:
            person_id = get_user_id(vk_session, person_id)
            if person_id is None:
                return 0
        if db.check_if_user_exists(cur, person_id) is None:
            recommendations_from_vk(tools, person_id)
        films = []
        recs = db.find_undefined_user_recommendations(cur, person_id)
        for i in range(len(recs)):
            films.append(db.find_info(cur, recs[i]['film']))
        return person_id, films
    else:
        print('Token is empty')
        return


def connect():
    print('Connecting to the PostgreSQL database...')

    global conn
    conn = psycopg2.connect(
        host="localhost",
        database="frsystem",
        user="postgres",
        password=PASSWORD
    )

    global cur
    cur = conn.cursor()


def close():
    cur.close()
    conn.close()
    print('Database connection closed.')


if __name__ == '__main__':
    connect()
    # add_250_top_movies_to_db()
    # start('olesyanikolaevaa')
    close()
