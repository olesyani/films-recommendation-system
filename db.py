import psycopg2
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
        self.cur = self.conn.cursor()

    def query(self, query):
        self.cur.execute(query)

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
        result = None
        try:
            self.cur.execute(search, (user_id,))
            info = self.cur.fetchone()
            result = info[1]
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return result

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

    def get_undefined_user_recommendations(self, user_id):
        search = """SELECT * FROM recommend WHERE user_id = %s AND liked IS NULL LIMIT 4"""
        result = []
        try:
            self.cur.execute(search, (user_id,))
            info = self.cur.fetchone()
            while info is not None:
                r = {}
                r['user'] = info[1]
                r['film'] = info[2]
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

    def find_info(self, film_id):
        search = """SELECT * FROM filmsInfo WHERE film_id = %s"""
        result = {}
        try:
            self.cur.execute(search, (film_id,))
            info = self.cur.fetchone()
            result['id'] = info[1]
            result['title'] = info[2]
            result['description'] = info[3]
            result['image'] = decode_image(info[4])
            result['genres'] = info[5]
            result['stars'] = info[6]
            result['rating'] = info[7]
        except psycopg2.DatabaseError as error:
            print(error)
            self.reconnect()
        except TypeError:
            pass
        return result

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
            sql = """INSERT INTO filmsInfo(film_id, title, description, image, genres, stars, imdb_rating)
                                 VALUES(%s, %s, %s, %s, %s, %s, %s) RETURNING film_id;"""
            film_image = convert_image(film_image)
            insertion = self.cur.mogrify(sql, (film_id, film_title, film_desc, film_image, film_genres, film_stars, film_rating))
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
            imdb_rating FLOAT
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
