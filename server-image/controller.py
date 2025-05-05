from doctest import debug
from flask import request, jsonify, send_file
from model import Model
from cloudinary_handler import CloudinaryHandler
import io
import requests

class Controller:
    def __init__(self, app_instance):
        self._app = app_instance
        self.__db_model = Model()
        self.__cloudinary = CloudinaryHandler()

        self.__setup_routes()

    def __setup_routes(self):
        self._app.add_url_rule('/insert/user', view_func=self._insert_user, methods=['POST'])
        self._app.add_url_rule('/post/image/<id>', view_func=self._post_image, methods=['POST'])
        self._app.add_url_rule('/get/image/<id>', view_func=self._get_image, methods=['GET'])
        self._app.add_url_rule('/insert/data/<id>', view_func=self._insert_data, methods=['POST'])
        self._app.add_url_rule('/find/data/<id>', view_func=self._find_data, methods=['GET'])
        self._app.add_url_rule('/find/pot/<id>', view_func=self._find_pot, methods=['GET'])
        self._app.add_url_rule('/find/user/<id>', view_func=self._find_pot_ids, methods=['GET'])

    def _insert_user(self):
        try:
            data = request.get_json()
            chat_id = data.get('chat_id')
            pot_id = data.get('pot_id')
            self.__db_model.insert_user(chat_id, pot_id)
            url = self.__cloudinary.upload_image('white.jpg', public_id=str(pot_id))
            self.__db_model.insert_image(pot_id, url)

            return jsonify({'message': 'User saved successfully'}), 201
        except Exception as e:
            return str(e), 500

    def _find_pot(self, id):
        try:
            id = int(id)
            pot = self.__db_model.find_pot(id)
            return jsonify(pot), 200
        except Exception as e:
            return str(e), 500

    def _post_image(self, id):
        try:
            id = int(id)
            if self.__db_model.is_user(id):
                image_bytes = request.data
                image_processed = self.__db_model.predict(image_bytes)

                if image_processed is not None:
                    url = self.__cloudinary.upload_image(image_processed, public_id=str(id))
                    return jsonify({'message': 'Image processed and uploaded successfully!', 'url': url}), 200
                else:
                    return jsonify({'message': 'Image could not be processed or no objects detected.'}), 400
            else:
                return jsonify({'message': 'User not found.'}), 404
        except Exception as e:
            print(f"Error in _post_image: {e}")
            return str(e), 500

    def _get_image(self, id):
        try:
            id = int(id)
            if self.__db_model.is_user(id):
                image_url = self.__db_model.find_image(id)
                response = requests.get(image_url)
                if response.status_code == 200:
                    return send_file(io.BytesIO(response.content), mimetype='image/jpeg')
                else:
                    return jsonify({'message': 'Image not found.'}), 404
            else:
                return jsonify({'message': f'User not found.'}), 404
        except Exception as e:
            return str(e), 500


    def _insert_data(self, id):
        try:
            id = int(id)
            if self.__db_model.is_user(id):
                data = request.get_json()
                ph = data.get('ph')
                soil = data.get('soil')
                self.__db_model.insert_data(id, ph, soil)
                return jsonify({'message': 'Data saved successfully'}), 201
            else:
                return jsonify({'message': 'User not found.'}), 404
        except Exception as e:
            return str(e), 500

    def _find_data(self, id):
        try:
            id = int(id)
            if self.__db_model.is_user(id):
                data = self.__db_model.find_data(id)
                return jsonify(data), 200
            else:
                return jsonify({'message': 'User not found.'}), 404
        except Exception as e:
            return str(e), 500

    def _find_pot_ids(self, id):
        try:
            id = int(id)
            data = self.__db_model.get_pot_ids(id)
            return jsonify(data), 200
        except Exception as e:
            return str(e), 500
    def run(self):
        self._app.run(host='0.0.0.0', port=5001)
