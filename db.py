import psycopg2
import requests
import base64


PASSWORD = ''


def convert_image(link):
    response = requests.get(link)
    return base64.b64encode(response.content)


def decode_image(encoded_image):
    return base64.b64decode(encoded_image)


def rate_film(conn, cur, user_id, film_id, rate: True or False):
    print("Updating user's preference..")
    upd = """UPDATE recommend
                SET liked = %s
                WHERE film_id = %s AND user_id = %s;"""
    try:
        cur.execute(upd, (rate, film_id, user_id))
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


def check_if_user_exists(cur, user_id):
    print('Checking if user exists..')
    search = """SELECT * FROM recommend WHERE user_id = %s"""
    result = None
    try:
        cur.execute(search, (user_id,))
        info = cur.fetchone()
        result = info[1]
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return result


def find_undefined_user_recommendations(cur, user_id):
    print('Finding recommendations..')
    search = """SELECT * FROM recommend WHERE user_id = %s AND liked IS NULL"""
    result = None
    try:
        result = []
        cur.execute(search, (user_id,))
        info = cur.fetchone()
        while info is not None:
            r = {}
            r['user'] = info[1]
            r['film'] = info[2]
            result.append(r)
            info = cur.fetchone()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return result


def get_all_users_recommendations(cur, user_id):
    print('Get all recommendations..')
    search = """SELECT * FROM recommend WHERE user_id = %s"""
    result = None
    try:
        result = []
        cur.execute(search, (user_id,))
        info = cur.fetchone()
        while info is not None:
            r = {}
            r['user'] = info[1]
            r['film'] = info[2]
            r['like'] = info[3]
            result.append(r)
            info = cur.fetchone()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return result


def find_info(cur, film_id):
    print('Finding info..')
    search = """SELECT * FROM filmsInfo WHERE film_id = %s"""
    result = None
    try:
        r = {}
        cur.execute(search, (film_id,))
        info = cur.fetchone()
        r['id'] = info[1]
        r['title'] = info[2]
        r['description'] = info[3]
        r['image'] = decode_image(info[4])
        r['genres'] = info[5]
        r['stars'] = info[6]
        result = r
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return result


def insert_recommendation(conn, cur, film_id, user_id):
    print('Inserting recommendation..')
    insertion = """INSERT INTO recommend(film_id, user_id)
                     VALUES(%s, %s) RETURNING film_id;"""
    lid = None
    try:
        cur.execute(insertion, (film_id, user_id))
        lid = cur.fetchone()[0]
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return lid


def insert_film_info(conn, cur, film_id, film_title, film_desc, film_image, film_genres, film_stars):
    maxchar = 312
    print('Inserting film information..')
    insertion = """INSERT INTO filmsInfo(film_id, title, description, image, genres, stars)
                 VALUES(%s, %s, %s, %s, %s, %s) RETURNING film_id;"""
    fid = None
    if len(film_desc) > maxchar:
        film_desc = film_desc[:maxchar-3] + '...'
    try:
        film_image = convert_image(film_image)
        cur.execute(insertion, (film_id, film_title, film_desc, film_image, film_genres, film_stars))
        fid = cur.fetchone()[0]
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return fid


def create_tables(conn, cur):
    commands = (
        """
        CREATE TABLE filmsInfo (
            id INTEGER PRIMARY KEY,
            film_id VARCHAR(16) UNIQUE,
            title VARCHAR NOT NULL,
            description VARCHAR(312) NOT NULL,
            image BYTEA NOT NULL,
            genres VARCHAR NOT NULL,
            stars VARCHAR NOT NULL
        )
        """,
        """ CREATE TABLE recommend (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                film_id VARCHAR(16) NOT NULL,
                liked BOOLEAN,
                UNIQUE (user_id, film_id)
            )
        """,
        """ ALTER TABLE filmsInfo 
            ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY
        """,
        """ ALTER TABLE recommend 
            ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY
        """
    )
    try:
        for command in commands:
            cur.execute(command)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


if __name__ == '__main__':

    print('Connecting to the PostgreSQL database...')

    conn = psycopg2.connect(
        host="localhost",
        database="frsystem",
        user="postgres",
        password=PASSWORD
    )

    cur = conn.cursor()
    create_tables(conn, cur)

    cur.close()
    conn.close()
    print('Database connection closed.')
