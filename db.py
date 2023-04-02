import asyncio
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore, storage


# serviceAccount.json

class FirebaseAdminDB:
    def __init__(self, cred_file_path=None):
        self._cred_file_path = cred_file_path
        self._cred = credentials.Certificate(self._cred_file_path)
        # Initialize app
        firebase_admin.initialize_app(
            self._cred, {'storageBucket': "face-id-turnstile-tripod.appspot.com"})
        # instanciate db
        self._db = firestore.client()
        self._bucket = storage.bucket()

    async def upload_image(self, file_path, image_name):
        blob = self._bucket.blob(image_name)
        blob.upload_from_filename(file_path)
        blob.make_public()
        return blob.public_url

    async def save_data(self, user_id, status, current_time, image_url):
        data = {
            'user_id': user_id,
            'status': status,
            'current_time': current_time,
            'image_url': image_url
        }
        self._db.collection('face_ids').add(data)
