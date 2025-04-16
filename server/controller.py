from flask import request, jsonify, send_file
from model import Model
import io

class Controller():
    def __init__(self, app_instance):
        self._app = app_instance
        self.__model = Model()

        self.__image = ''

        self._app.add_url_rule('/post/image', view_func=self._post_image, methods=['POST'])
        self._app.add_url_rule('/get/image', view_func=self._get_image, methods=['GET'])
        self._app.add_url_rule('/insert/data', view_func=self._insert_data, methods=['POST'])
        self._app.add_url_rule('/find/data', view_func=self._find_data, methods=['GET'])

    def _post_image(self):
        try:
            self.__image = request.data
            return jsonify({"message": "Image received successfully!"}), 200
        except Exception as e:
            return str(e), 500

    def _get_image(self):
        try:
            return send_file(io.BytesIO(self.__image), mimetype='image/jpeg')
        except Exception as e:
            return str(e), 500
        
    def _insert_data(self):
        try:
            data = request.get_json()
            ph = data.get('ph')
            soil = data.get('soil')
            self.__model.insert_data(ph, soil)
            
            return jsonify({'message': 'Data saved successfully'}), 201
        except Exception as e:
            return str(e), 500
        
    def _find_data(self):
        try:
            data = self.__model.find_data()
            return jsonify(data), 201
        except Exception as e:
            return str(e), 500

    def run(self):
        self._app.run(host='0.0.0.0')