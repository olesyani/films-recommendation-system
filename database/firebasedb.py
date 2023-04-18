import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


class FRSFirebaseDatabase:
    def __init__(self, directory: str):
        self.cred = credentials.Certificate(directory)
        self.app = firebase_admin.initialize_app(self.cred)
        self.client = firestore.client()

    def get_current_user(self, uid):
        coll_ref = self.client.collection("users")
        query_ref = coll_ref.where("vk_id", "==", uid)
        for doc in query_ref.stream():
            print(doc.id, doc.to_dict())
            return doc.to_dict()
        return None

    def get_films_list(self, user_id):
        coll_ref = self.client.collection("recommendations").document(str(user_id)).collection('recs')
        query_ref = coll_ref.where("saved", "==", True).limit(5)
        d = []
        for doc in query_ref.stream():
            tmp = doc.to_dict()
            tmp['film_id'] = doc.id
            tmp['film'] = self.get_title(doc.id)
            d.append(tmp)
        print(d)
        return d

    def check_if_username_exists(self, username):
        coll_ref = self.client.collection("users")
        query_ref = coll_ref.where("username", "==", username)
        for doc in query_ref.stream():
            print(doc.id, doc.to_dict())
            return doc.to_dict()
        return None

    def check_vk_id_exists(self, vk_id):
        coll_ref = self.client.collection("users")
        query_ref = coll_ref.where("vk_id", "==", vk_id)
        for doc in query_ref.stream():
            print(doc.id, doc.to_dict())
            return doc.to_dict()
        return None

    def rate_film(self, user_id, film_id, rate: True or False):
        ref = self.client.collection('recommendations').document(str(user_id)).collection('recs').document(str(film_id))
        ref.update({
            'liked': rate
        })

    def add_film_to_list(self, user_id, film_id):
        ref = self.client.collection('recommendations').document(str(user_id)).collection('recs').document(str(film_id))
        ref.update({
            'saved': True
        })

    def add_film_recommendations_list(self, user_id, recs):
        ref = self.client.collection('users').document(str(user_id))
        ref.update({
            'recommendations': str(recs)
        })

    def get_film_recommendations_list(self, user_id):
        docs = self.client.collection('recommendations').stream()
        uid = None
        for doc in docs:
            if doc.id == user_id:
                return doc.id.recommendations
        return uid

    def get_undefined_user_recommendations(self, user_id):
        coll_ref = self.client.collection("recommendations").document(str(user_id)).collection('recs')
        query_ref = coll_ref.where("liked", "==", None).where("saved", "==", False).limit(5)
        d = []
        for doc in query_ref.stream():
            d.append(doc.id)
        print(d)
        return d

    def get_number_of_loaded_recs(self, user_id):
        coll_ref = self.client.collection("recommendations").document(str(user_id)).collection('recs')
        count_query = coll_ref.count()
        query_result = count_query.get()
        print("Nb docs in collection:", query_result[0][0].value)
        return query_result[0][0].value

    def get_defined_user_recommendations(self, user_id):
        coll_ref = self.client.collection("recommendations").document(str(user_id)).collection('recs')
        query_ref = coll_ref.where("liked", "in", [True, False]).limit(5)
        d = []
        for doc in query_ref.stream():
            tmp = doc.to_dict()
            tmp['film_id'] = doc.id
            tmp['film'] = self.get_title(doc.id)
            d.append(tmp)
        print(d)
        return d

    def get_next_movie(self, user_id):
        coll_ref = self.client.collection("recommendations").document(str(user_id))
        query_ref = coll_ref.where("liked", "==", None).limit(5)
        res = None
        for doc in query_ref.stream():
            res = doc.id
        print(res)
        return res

    def get_title(self, film_id):
        ref = self.client.collection("films-info").document(str(film_id))
        return ref.get().to_dict()['title']

    def find_info(self, film_id):
        doc_ref = self.client.collection('films-info').document(str(film_id))
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            return None

    def insert_user(self, fullname, username, _hashed_password, pid, sn):
        ref = self.client.collection('users').document(str(pid))
        ref.set({
            'fullname': fullname,
            'username': username,
            'password': _hashed_password,
            'vk_id': pid,
            'screen_name': sn
        })

    def insert_recommendation(self, film_id, user_id):
        ref = self.client.collection('recommendations').document(str(user_id)).collection('recs').document(str(film_id))
        ref.set({
            'liked': None,
            'saved': False
        })

    def insert_film_info(self, film_id, film_title, film_desc, film_image, film_genres, film_stars, film_rating):
        ref = self.client.collection('films-info').document(str(film_id))
        ref.set({
            'film_id': film_id,
            'title': film_title,
            'description': film_desc,
            'link': film_image,
            'genres': film_genres,
            'stars': film_stars,
            'rating': film_rating
        })
