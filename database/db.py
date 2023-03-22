import psycopg2
import psycopg2.extras
import requests
import base64


class FRSDatabase:
    def __init__(self, database, password, host='localhost', user='postgres'):
        self.database = database
        self.password = password
        self.host = host
        self.user = user
        self.conn = psycopg2.connect(host=host,
                                     database=database,
                                     user=user,
                                     password=password)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def get_current_user(self, id):
        search = """SELECT * FROM users WHERE id = %s"""
        try:
            self.cur.execute(search, (id,))
            return self.cur.fetchone()
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass

    def reconnect(self):
        self.cur.close()
        self.conn.close()
        self.conn = psycopg2.connect(host=self.host,
                                     database=self.database,
                                     user=self.user,
                                     password=self.password)
        self.cur = self.conn.cursor()

    def check_if_user_exists(self, user_id):
        search = """SELECT * FROM recommend WHERE user_id = %s"""
        try:
            self.cur.execute(search, (user_id,))
            return self.cur.fetchone()
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return None

    def check_if_username_exists(self, username):
        search = """SELECT * FROM users WHERE username = %s"""
        try:
            self.cur.execute(search, (username,))
            return self.cur.fetchone()
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return None

    def check_vk_id_exists(self, vk_id):
        search = """SELECT * FROM users WHERE vk_id = %s"""
        try:
            self.cur.execute(search, (vk_id,))
            return self.cur.fetchone()
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return None

    def rate_film(self, user_id, film_id, rate: True or False):
        upd = """UPDATE recommend SET liked = %s WHERE film_id = %s AND user_id = %s;"""
        try:
            self.cur.execute(upd, (rate, film_id, user_id))
            self.conn.commit()
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass

    def add_film_to_list(self, user_id, film_id):
        upd = """UPDATE recommend SET saved = %s WHERE film_id = %s AND user_id = %s;"""
        try:
            self.cur.execute(upd, (True, film_id, user_id))
            self.conn.commit()
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass

    def get_undefined_user_recommendations(self, user_id):
        search = """SELECT * FROM recommend WHERE user_id = %s AND liked IS NULL AND saved IS NULL LIMIT 5"""
        result = []
        try:
            self.cur.execute(search, (user_id,))
            info = self.cur.fetchone()
            while info is not None:
                r = {}
                r['user'] = info['user_id']
                r['film'] = info['film_id']
                result.append(r)
                info = self.cur.fetchone()
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return result

    def get_defined_user_recommendations(self, user_id):
        search = """SELECT * FROM recommend WHERE user_id = %s AND liked IS NOT NULL LIMIT 25"""
        result = []
        try:
            self.cur.execute(search, (user_id,))
            info = self.cur.fetchone()
            while info is not None:
                r = {}
                r['film'] = self.get_title(info['film_id'])
                r['rating'] = info['liked']
                result.append(r)
                info = self.cur.fetchone()
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return result

    def get_films_list(self, user_id):
        search = """SELECT * FROM recommend WHERE user_id = %s AND saved IS NOT NULL"""
        result = []
        try:
            self.cur.execute(search, (user_id,))
            info = self.cur.fetchone()
            while info is not None:
                r = {}
                r['film'] = self.get_title(info['film_id'])
                result.append(r)
                info = self.cur.fetchone()
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return result

    def get_next_movie(self, user_id):
        search = """SELECT film_id FROM recommend WHERE user_id = %s AND liked IS NULL LIMIT 1 OFFSET 3"""
        result = None
        try:
            self.cur.execute(search, (user_id,))
            info = self.cur.fetchone()
            result = self.find_info(info[0])
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return result

    def get_all_recommendations(self, user_id):
        search = """SELECT * FROM recommend WHERE user_id = %s"""
        result = []
        try:
            self.cur.execute(search, (user_id,))
            info = self.cur.fetchone()
            while info is not None:
                r = {}
                r['user'] = info[1]
                r['film'] = info[2]
                r['like'] = info[3]
                result.append(r)
                info = self.cur.fetchone()
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return result

    def get_title(self, film_id):
        search = """SELECT * FROM filmsInfo WHERE film_id = %s"""
        try:
            self.cur.execute(search, (film_id,))
            info = self.cur.fetchone()
            return info['title']
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return None

    def find_info(self, film_id):
        search = """SELECT * FROM filmsInfo WHERE film_id = %s"""
        result = {}
        try:
            self.cur.execute(search, (film_id,))
            info = self.cur.fetchone()
            result['image'] = info['image_link']
            result['id'] = info['film_id']
            result['title'] = info['title']
            result['description'] = info['description']
            result['genres'] = info['genres']
            result['stars'] = info['stars']
            result['rating'] = info['imdb_rating']
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return result

    def insert_user(self, fullname, username, _hashed_password, pid, sn):
        insertion = """INSERT INTO users (name, username, password, vk_id, screen_name) VALUES (%s,%s,%s,%s,
        %s) RETURNING id; """
        lid = None
        try:
            self.cur.execute(insertion, (fullname, username, _hashed_password, pid, sn))
            lid = self.cur.fetchone()[0]
            self.conn.commit()
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return lid

    def insert_recommendation(self, film_id, user_id):
        insertion = """INSERT INTO recommend(film_id, user_id) VALUES(%s, %s) RETURNING film_id;"""
        lid = None
        try:
            self.cur.execute(insertion, (film_id, user_id))
            lid = self.cur.fetchone()[0]
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return lid

    def insert_film_info(self, film_id, film_title, film_desc, film_image, film_genres, film_stars, film_rating):
        fid = None
        try:
            sql = """INSERT INTO filmsInfo(film_id, title, description, image_link, genres, stars, imdb_rating)
                                 VALUES(%s, %s, %s, %s, %s, %s, %s) RETURNING film_id;"""
            # film_image = convert_image(film_image)
            insertion = self.cur.mogrify(sql, (film_id,
                                               film_title,
                                               film_desc,
                                               film_image,
                                               film_genres,
                                               film_stars,
                                               film_rating))
            self.cur.execute(insertion)
            fid = self.cur.fetchone()[0]
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return fid

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()
        print('Database connection closed.')


def convert_image(link):
    response = requests.get(link)
    return base64.b64encode(response.content)


def decode_image(encoded_image):
    return base64.b64decode(encoded_image)


def create_tables(connection, cursor):
    commands = (
        """
        CREATE TABLE filmsInfo (
            id INTEGER PRIMARY KEY,
            film_id VARCHAR(16) UNIQUE,
            title VARCHAR NOT NULL,
            description VARCHAR,
            image BYTEA,
            genres VARCHAR,
            stars VARCHAR,
            imdb_rating FLOAT,
            image_link VARCHAR
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
            cursor.execute(command)
        connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


if __name__ == '__main__':

    print('Connecting to the PostgreSQL database...')

    conn = psycopg2.connect(
        host="localhost",
        database="",  # Необходимо вставить название БД
        user="postgres",
        password=""  # Необходимо вставить пароль
    )

    cur = conn.cursor()
    create_tables(conn, cur)

    cur.close()
    conn.close()

    print('Database connection closed.')
