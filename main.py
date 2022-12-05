import vk_api
import re
from imdb import imdb_req
from collections import Counter
from deep_translator import GoogleTranslator



# в переменных LOGIN, PASSWORD должны лежать логин и пароль от странцы в ВК
LOGIN, PASSWORD = '', ''
FRIENDS_N = 150
POSTS_N = 100
COMMUNITIES_N = 300
KEYWORDS_N = 15


def word_translate(word='сон'):
    translation = GoogleTranslator(source='auto', target='en').translate(word)
    return translation


def get_movie_titles(data):
    for i in range(len(data)):
        print(data[i]['title'], data[i]['description'])


def auth_handler():
    """ При двухфакторной аутентификации вызывается эта функция.
    """

    key = input("Enter authentication code: ")
    remember_device = True

    return key, remember_device


def main():

    login, password = LOGIN, PASSWORD

    vk_session = vk_api.VkApi(
        login, password,
        # функция для обработки двухфакторной аутентификации
        auth_handler=auth_handler
    )

    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return

    tools = vk_api.VkTools(vk_session)

    # friends = tools.get_all('friends.get', FRIENDS_N)
    # friends_ids = friends['items']

    wall = tools.get_all('wall.get', POSTS_N)
    wall_items = wall['items']

    wall_text = ""
    for i in range(wall['count']):
        wall_text += wall_items[i]['text']
        try:
            wall_text += wall_items[i]['copy_history'][0]['text']
        except KeyError:
            continue
        wall_text += ' '

    wall_text = re.sub("[*/,.@':;!?&]", "", wall_text)
    wall_text = wall_text.replace("-", " ")
    words = [x for x in wall_text.split(" ") if len(x) >= 2]
    count = list(Counter(words).most_common())

    movies_list = []
    for i in count[:KEYWORDS_N]:
        w = word_translate(i[0])
        movies_list.extend(imdb_req(w))

    get_movie_titles(movies_list)


if __name__ == '__main__':
    main()
