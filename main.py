import vk_api
import re
from imdb import imdb_req, imdb_top_250_movies
from collections import Counter
from deep_translator import GoogleTranslator


TOKEN = ''

POSTS_N = 100
COMMUNITIES_N = 300
KEYWORDS_N = 5


def word_translate(word='сон'):
    translation = GoogleTranslator(source='auto', target='en').translate(word)
    return translation


def clear_text(text):
    return re.sub('[\W_]+', ' ', text.replace('ё', 'е').lower()).split()


def get_user_id(vk_session, screen_name):
    vk = vk_session.get_api()
    person_id = vk.users.get(user_ids=screen_name)
    try:
        return person_id[0]['id']
    except IndexError:
        print('There is no person with that ID')
        return None


def recommendation(tools, owner_id):
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

    # функция imdb_top_250_movies() пока возвращает пустой список, сейчас это в разработке
    movies_list.extend(imdb_top_250_movies())

    return movies_list


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
        titles_list = recommendation(tools, person_id)
        return titles_list
    else:
        print('Token is empty')
        return


if __name__ == '__main__':
    start('')
