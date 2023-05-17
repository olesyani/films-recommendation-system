import pandas as pd
import pandas.io.sql as psql
import database.db as db
import os
import re
import warnings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from nltk.corpus import stopwords
from dotenv import load_dotenv
import imdb


warnings.filterwarnings("ignore")

load_dotenv()

pd.set_option('display.max_rows', 30)
pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 1000)
pd.set_option('max_colwidth', None)

DATABASE = os.getenv("DATABASE")
PASSWORD = os.getenv("PASSWORD")


def keywords_loader(frsdb: db.FRSDatabase):
    ia = imdb.Cinemagoer()
    films_list = frsdb.get_films_with_no_keywords()

    print(len(films_list))

    for i in films_list:
        print(i)
        film = ia.get_movie(i.replace('t', ''), info='keywords')
        try:
            frsdb.add_keywords(i, film['keywords'])
            frsdb.commit()
        except KeyError:
            frsdb.add_keywords(i, '')
            frsdb.commit()
        except imdb.IMDbDataAccessError:
            print('Error with', i)


def get_recommendations(df_movies, title, n, cosine_sim, weight=1.0):

    movie_index = df_movies[df_movies.film_id == title].id.values[0]

    sim_scores_all = sorted(list(enumerate(cosine_sim[movie_index])), key=lambda x: x[1], reverse=True)

    if n > 0:
        sim_scores_all = sim_scores_all[1:n + 1]

    movie_indices = [i[0] for i in sim_scores_all]
    scores = [i[1]*weight for i in sim_scores_all]

    top_titles_df = pd.DataFrame(df_movies.iloc[movie_indices]['title'])
    top_titles_df['sim_scores'] = scores
    top_titles_df['ranking'] = range(1, len(top_titles_df) + 1)

    result = pd.merge(top_titles_df, df_movies.drop(columns=['imdb_rating', 'keywords', 'id']), on='title', how='inner')
    print(result)

    return result, sim_scores_all


def clear_dataframe(films_dataframe, recs_dataframe, person_id):
    films_dataframe = films_dataframe.drop(columns=['id', 'image_link', 'description']).dropna()
    recs_dataframe = recs_dataframe.drop(columns=['id', 'rate_date'])
    recs_dataframe = recs_dataframe[recs_dataframe['user_id'] == person_id].dropna(subset=['liked', 'saved'], how='all')
    films_dataframe['keywords'] = films_dataframe['keywords'].apply(lambda x: re.sub(r'[^a-zA-Z\d -]+', ' ', x.lower()))
    films_dataframe['year'] = films_dataframe['title'].apply(lambda x: x[-6:].replace('(', '').replace(')', ''))
    films_dataframe['stars'] = films_dataframe['stars'].apply(lambda x: x.replace(' ', '').replace(',', ' '))
    films_dataframe['genres'] = films_dataframe['genres'].apply(lambda x: x.replace(' ', '').replace(',', ' '))
    films_dataframe['keywords'] = films_dataframe['keywords'] + ' ' + films_dataframe['stars'] + ' ' + \
                                  films_dataframe['genres'] + ' ' + films_dataframe['year']
    films_dataframe = films_dataframe.drop(columns=['stars', 'genres', 'year'])
    films_dataframe['id'] = range(0, len(films_dataframe))
    recs_dataframe = recs_dataframe[recs_dataframe['film_id'].isin(films_dataframe['film_id'])]
    print(recs_dataframe)
    print(recs_dataframe)
    return films_dataframe, recs_dataframe


def recommendation_system(frsdb: db.FRSDatabase, person_id, kloader=False):
    if kloader:
        keywords_loader(frsdb)

    films_dataframe = psql.read_sql('select * from filmsinfo', con=frsdb.conn)
    recs_dataframe = psql.read_sql('select * from recommend', con=frsdb.conn)

    films_dataframe, recs_dataframe = clear_dataframe(films_dataframe, recs_dataframe, person_id)

    stop = list(stopwords.words('english'))

    tfidf = TfidfVectorizer(max_features=5000, analyzer='word', stop_words=stop)
    vectorized_data = tfidf.fit_transform(films_dataframe['keywords'])
    count_matrix = pd.DataFrame(vectorized_data.toarray(), index=films_dataframe['keywords'].index.tolist())
    print(count_matrix)

    svd = TruncatedSVD(n_components=3000)
    reduced_data = svd.fit_transform(count_matrix)

    similarity = cosine_similarity(reduced_data)
    print(similarity)

    liked_movie_list = recs_dataframe.loc[recs_dataframe['liked'] == True].film_id.values.tolist()
    saved_movie_list = recs_dataframe.loc[recs_dataframe['saved'] == True].film_id.values.tolist()
    not_liked_movie_list = recs_dataframe.loc[recs_dataframe['liked'] == False].film_id.values.tolist()

    user_scores = pd.DataFrame(films_dataframe['title'])
    user_scores['sim_scores'] = 0.0

    number_of_recommendations = 10000

    for movie_name in liked_movie_list:
        top_titles_df, _ = get_recommendations(films_dataframe, movie_name, number_of_recommendations, similarity)
        user_scores = pd.concat([user_scores,
                                 top_titles_df[['film_id', 'title', 'sim_scores']]]).groupby(['film_id'],
                                                                                as_index=False).sum({'sim_scores'})

    for movie_name in saved_movie_list:
        top_titles_df, _ = get_recommendations(films_dataframe, movie_name, number_of_recommendations, similarity, 0.25)
        user_scores = pd.concat([user_scores,
                                 top_titles_df[['film_id', 'title', 'sim_scores']]]).groupby(['film_id'],
                                                                                as_index=False).sum({'sim_scores'})

    for movie_name in not_liked_movie_list:
        top_titles_df, _ = get_recommendations(films_dataframe, movie_name, number_of_recommendations, similarity, -0.3)
        user_scores = pd.concat([user_scores,
                                 top_titles_df[['film_id', 'title', 'sim_scores']]]).groupby(['film_id'],
                                                                                as_index=False).sum({'sim_scores'})

    top_titles_per_user_df = user_scores.sort_values(by='sim_scores', ascending=False)[1:30]

    print('---- FINAL RECOMMENDATION DATAFRAME: ----')
    result = pd.merge(top_titles_per_user_df,
                      films_dataframe.drop(columns=['imdb_rating', 'keywords', 'id']), on='film_id', how='inner')
    print(result)

    titles_list = top_titles_per_user_df.film_id.values.tolist()
    print(titles_list)

    return titles_list


if __name__ == '__main__':
    FRSDB = db.FRSDatabase(DATABASE, PASSWORD)
    recommendation_system(FRSDB, 91020378)
    FRSDB.close()
