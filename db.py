import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore, storage


# serviceAccount.json

class FirebaseAdminDB:
    def __init__(self, path=None, database_url=None):

        self.cred = credentials.Certificate(path)
        # Initialize app
        firebase_admin.initialize_app(
            self.cred, {'storageBucket': "face-id-turnstile-tripod.appspot.com"})
        # instanciate db
        self.db = firestore.client()


    def upload_picture(self, image_path):
        bucket = storage.bucket()  # get the bucket storage
        blob = bucket.blob(image_path)
        blob.upload_from_filename(image_path)
        return blob.url
    
    def save_data(self, user_id, result):
        pass

    
