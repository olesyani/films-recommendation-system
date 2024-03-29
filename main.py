import vk_api
import re
import random
import time
import database.db as db
import api.imdb as imdb
import os
from collections import Counter
from deep_translator import GoogleTranslator
from pymorphy2 import MorphAnalyzer
from nltk.corpus import wordnet as wn
from datetime import datetime
from dotenv import load_dotenv
from recommendation import recommendation_system


load_dotenv()

WN_NOUN = 'n'
WN_VERB = 'v'
WN_ADJECTIVE = 'a'
WN_ADJECTIVE_SATELLITE = 's'
WN_ADVERB = 'r'

TOKEN = os.getenv("TOKEN")

DATABASE = os.getenv("DATABASE")
PASSWORD = os.getenv("PASSWORD")


POSTS_N = 100
COMMUNITIES_N = 300
KEYWORDS_N = 10


def word_translate(word):
    translation = GoogleTranslator(source='auto', target='en').translate(word)
    return translation


def translate_to_rus(text):
    translation = GoogleTranslator(source='auto', target='ru').translate(text)
    return translation


def clear_text(text):
    return re.sub(r'[^а-яА-Яa-zA-Z ]+', ' ', text.replace('ё', 'е').lower()).split()


def convert(word):
    to_pos = 'n'
    norm_words = []
    for from_pos in ['v', 'a', 's', 'r']:
        synsets = wn.synsets(word, pos=from_pos)

        if not synsets:
            continue

        lemmas = []
        for s in synsets:
            for l in s.lemmas():
                if s.name().split('.')[1] == from_pos or from_pos in (WN_ADJECTIVE, WN_ADJECTIVE_SATELLITE) \
                        and s.name().split('.')[1] in (WN_ADJECTIVE, WN_ADJECTIVE_SATELLITE):
                    lemmas += [l]

        derivationally_related_forms = [(l, l.derivationally_related_forms()) for l in lemmas]

        related_noun_lemmas = []

        for drf in derivationally_related_forms:
            for l in drf[1]:
                if l.synset().name().split('.')[1] == to_pos or to_pos in (WN_ADJECTIVE, WN_ADJECTIVE_SATELLITE) \
                        and l.synset().name().split('.')[1] in (WN_ADJECTIVE, WN_ADJECTIVE_SATELLITE):
                    related_noun_lemmas += [l]

        words = [l.name() for l in related_noun_lemmas]
        len_words = len(words)

        result = [(w, float(words.count(w)) / len_words) for w in set(words)]
        norm_words.extend(result)

    norm_words.sort(key=lambda w: -w[1])
    norm_words = tuple([w[0] for w in norm_words])
    return norm_words[:5]


def lemmatize(text):
    text = clear_text(text)
    morph = MorphAnalyzer()
    words_lemma = ''
    for word in text:
        p = morph.parse(word)[0]
        words_lemma += p.normal_form + ' '
    return words_lemma


def get_permission(frsdb: db.FRSDatabase, person_id):
    t = frsdb.get_last_request_date(person_id)
    if t:
        days_between = (datetime.now() - t).days
        if days_between > 5:
            return True
        else:
            return False
    return True


def get_user_id(vk_session, screen_name):
    vk = vk_session.get_api()
    person_id = vk.users.get(user_ids=screen_name, fields='screen_name')
    try:
        return person_id[0]['id'], person_id[0]['screen_name']
    except IndexError:
        print('There is no person with that ID')
        return None, None


def calculate_precision(frsdb: db.FRSDatabase):
    liked = frsdb.get_metrics(True)
    not_liked = frsdb.get_metrics(False)
    return liked / (liked + not_liked)


def collecting_data_from_vk(tools, owner_id):
    s = time.time()
    print('VK recommendations in progress..')
    wall = tools.get_all('wall.get', POSTS_N, {'owner_id': owner_id})
    wall_items = wall['items']
    groups = tools.get_all('groups.get', POSTS_N, {'user_id': owner_id, 'extended': 1, 'fields': "name"})
    groups_items = groups['items']

    wall_text = ""
    for i in range(wall['count']):
        wall_text += wall_items[i]['text']
        try:
            wall_text += wall_items[i]['copy_history'][0]['text']
        except KeyError:
            continue
        wall_text += ' '

    for i in range(groups['count']):
        try:
            wall_text += groups_items[i]['name']
        except KeyError:
            continue
        wall_text += ' '

    print('CHECKPOINT INFO COLLECTED')
    s = time.time() - s
    print(s)

    wall_text = lemmatize(wall_text)[:15000]

    translated = ''

    while wall_text:
        translated += word_translate(wall_text[:3000])
        print('--- batch translated ---')
        wall_text = wall_text[3000:]
        time.sleep(1)

    translated = clear_text(translated)

    words = [x for x in translated if len(x) >= 3]

    print('CHECKPOINT TRANSLATED')
    s = time.time() - s
    print(s)

    normalized_words = []

    for w in words:
        normalized_words.extend(convert(w))

    count = list(Counter(normalized_words).most_common())

    print(count)

    print('CHECKPOINT WORDS NORMALIZED')
    s = time.time() - s
    print(s)

    movies_list = []
    for i in count[:KEYWORDS_N]:
        movies_list.extend(imdb.imdb_req(i[0]))

    movies_list = [dict(t) for t in {tuple(d.items()) for d in movies_list}]
    random.shuffle(movies_list)

    print('CHECKPOINT GOT MOVIES LIST')
    s = time.time() - s
    print(s)

    return movies_list


def generate_vk_recommendations(frsdb, person_id, loop=False):
    if TOKEN:
        vk_session = vk_api.VkApi(token=TOKEN)
        tools = vk_api.VkTools(vk_session)
        if (frsdb.check_if_user_exists(person_id) is None) or (loop and get_permission(frsdb, person_id)):
            movies = collecting_data_from_vk(tools, person_id)
            frsdb.add_request_date(person_id, datetime.now())
            s = time.time()
            print('Information collected.')
            insert_data(frsdb, movies[:30], person_id)
            if movies[30:]:
                frsdb.add_film_recommendations_list(person_id, movies[30:])
                frsdb.commit()
            print('CHECKPOINT INFO COLLECTED')
            print(time.time() - s)
            print('Data inserted.')
            return True
        return False
    else:
        print('Token is empty')
        return False


def add_250_top_movies_to_db(frsdb: db.FRSDatabase, genre=None, keyword=None):
    if genre:
        tmp = imdb.imdb_top_250_by_genre(genre)
    elif keyword:
        tmp = imdb.imdb_req(keyword)
    else:
        tmp = imdb.imdb_top_250_movies()
    for i in range(len(tmp)):
        if frsdb.find_info(tmp[i]['id']) == {}:
            print('Inserting..')
            if tmp[i]['description']:
                tmp[i]['description'] = translate_to_rus(tmp[i]['description'][:5000])
            frsdb.insert_film_info(
                film_id=tmp[i]['id'],
                film_desc=tmp[i]['description'],
                film_image=tmp[i]['image'],
                film_title=tmp[i]['title'],
                film_genres=tmp[i]['genre'],
                film_stars=tmp[i]['stars'],
                film_rating=tmp[i]['rating']
            )
    frsdb.commit()


def check_vk_id(person_id):
    if TOKEN != '':
        vk_session = vk_api.VkApi(token=TOKEN)
        person_id, screen_name = get_user_id(vk_session, person_id)
        if person_id is None:
            return 0, 0
        return person_id, screen_name


def insert_data(frsdb: db.FRSDatabase, movies, person_id):
    for i in range(len(movies)):
        print('Inserting data into database..')
        try:
            if float(movies[i]['rating']) > 5.5:
                if frsdb.find_info(movies[i]['id']) == {}:
                    if movies[i]['description']:
                        movies[i]['description'] = translate_to_rus(movies[i]['description'][:5000])
                    frsdb.insert_film_info(
                        film_id=movies[i]['id'],
                        film_desc=movies[i]['description'],
                        film_image=movies[i]['image'],
                        film_title=movies[i]['title'],
                        film_genres=movies[i]['genre'],
                        film_stars=movies[i]['stars'],
                        film_rating=movies[i]['rating']
                    )
                frsdb.insert_recommendation(film_id=movies[i]['id'], user_id=person_id)
        except TypeError:
            pass
    frsdb.commit()


def start(frsdb: db.FRSDatabase, person_id):

    generate_vk_recommendations(frsdb, person_id)

    films = []
    recs = frsdb.get_undefined_user_recommendations(person_id)
    recs_n = frsdb.get_number_of_loaded_recs(person_id)

    if recs and recs_n[0] > 10:
        for i in range(len(recs)):
            films.append(frsdb.find_info(recs[i]['film']))
        return films
    else:
        films = frsdb.get_film_recommendations_list(person_id)
        if films:
            films = list(eval(films[0]))
            insert_data(frsdb, films[:20], person_id)
            if films[20:]:
                frsdb.add_film_recommendations_list(person_id, films[20:])
            films = []
            recs = frsdb.get_undefined_user_recommendations(person_id)
            if recs:
                for i in range(len(recs)):
                    films.append(frsdb.find_info(recs[i]['film']))
                return films
        resp = generate_vk_recommendations(frsdb, person_id, True)
        if not resp:
            titles = recommendation_system(frsdb, person_id)
            for i in range(len(titles)):
                frsdb.insert_recommendation(film_id=titles[i], user_id=person_id)
            return films
        for i in range(len(recs)):
            films.append(frsdb.find_info(recs[i]['film']))
        return films


def start_from_main(frsdb: db.FRSDatabase, person_id, loop=False):
    vk_session = vk_api.VkApi(token=TOKEN)

    person_id, screen_name = get_user_id(vk_session, person_id)
    print(person_id, screen_name)
    start(frsdb, person_id)


if __name__ == '__main__':
    FRSDB = db.FRSDatabase(DATABASE, PASSWORD)

    print(calculate_precision(FRSDB))

    # start_from_main(FRSDB, 'olesyanikolaevaa')
    # print('Database connected.')
    # for j in ['action', 'adventure', 'animation', 'biography', 'comedy', 'crime', 'documentary', 'drama', 'family',
    #           'fantasy', 'film_noir', 'game_show', 'history', 'horror', 'music', 'musical', 'mystery', 'news',
    #           'reality_tv', 'romance', 'sci_fi', 'sport', 'talk_show', 'thriller', 'war', 'western']:
    #     print(j)
    #     add_250_top_movies_to_db(FRSDB, j)

    # for j in ['love', 'school', 'inspiration', 'sport', 'work', 'fashion', 'dreamer', 'goal', 'depression',
    #           'teen', 'office', 'treasure', 'murder', 'creatures', 'marvel', 'comics', 'war', 'help', 'destiny']:
    #     print(j)
    #     add_250_top_movies_to_db(FRSDB, keyword=j)

    FRSDB.close()
