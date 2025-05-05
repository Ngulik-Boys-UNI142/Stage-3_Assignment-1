from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import pandas as pd
import numpy as np
import cv2
from ultralytics import YOLO

import base64

import os

class Model():
    def __init__(self):
        self.__client = MongoClient('mongodb+srv://elchilz:Elco1001@smartfarm.zrqtr.mongodb.net/?retryWrites=true&w=majority&appName=smartfarm',  server_api=ServerApi('1'))
        try:
            self.__database = self.__client.get_database('smartfarm')
            self.__collection()
            self.__specification()
        except Exception as e:
            print(f'Error: {e}')

    def __collection(self):
        self.__collection_data = self.__database.get_collection('data')
        self.__collection_user = self.__database.get_collection('user')
        self.__collection_image = self.__database.get_collection('image')

    def __specification(self):
        self.__collection_user.create_index([('pot_id')], unique=True)

    def insert_user(self, chat_id, pot_id):
        user_search = self.__collection_user.find_one({'chat_id' : chat_id})
        if user_search is None:
            if pot_id == None:
                return False
            else:
                new_user = {
                    'chat_id' : chat_id,
                    'pot_ids' : [pot_id]
                }
                try:
                    self.__collection_user.insert_one(new_user)
                    print(f"Inserted new user: {chat_id} with pot: {pot_id}")
                    return True
                except Exception as e:
                    print(f"Error inserting user {chat_id}: {e}")
                    return False
        else:
            try:
                result = self.__collection_user.update_one(
                    {'chat_id': chat_id},
                    {'$addToSet': {'pot_ids': pot_id}}
                )
                if result.modified_count > 0:
                    print(f"Added pot_id {pot_id} to user {chat_id}")
                else:
                    print(f"Pot_id {pot_id} already associated with user {chat_id}")
                return True
            except Exception as e:
                print(f"Error updating user {chat_id}: {e}")
                return False

    def is_user(self, pot_id):
        user = self.__collection_user.find_one({'pot_id' : pot_id}, {'_id': 0,'chat_id' : 1})
        if user == None:
            return False
        else:
            return True

    def predict(self, image_bytes):
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is not None:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            model_pest = YOLO('best_pest.pt')
            results_pest = model_pest(frame_rgb, verbose=False)
            detected_frame_rgb_with_pests = results_pest[0].plot()

            model_sickness = YOLO('best_sickness.pt')
            results_sickness = model_sickness(detected_frame_rgb_with_pests, verbose=False, conf=0.5)
            final_detected_frame_rgb = results_sickness[0].plot()

            detected_frame_bgr = cv2.cvtColor(final_detected_frame_rgb, cv2.COLOR_RGB2BGR)

            _, buffer = cv2.imencode('.jpg', detected_frame_bgr)
            processed_image_bytes = buffer.tobytes()

            return processed_image_bytes
        else:
            return None

    def get_pot_ids(self, chat_id):
        user = self.__collection_user.find_one({'chat_id' : chat_id}, {'_id': 0,'pot_ids' : 1})

        if user == None:
            return False
        else:
            return user['pot_ids']

    def find_pot(self, id):
        pot = self.__collection_user.find({'chat_id' : id}, {'_id': 0,'pot_id' : 1})
        raw_data = list(pot)
        df = pd.json_normalize(raw_data)
        return df['pot_id'].values.tolist()

    def insert_image(self, pot_id, url):
        image = {
            'pot_id' : pot_id,
            'url' : url
        }

        self.__collection_image.insert_one(image)


    def find_image(self, pot_id):
        image = self.__collection_image.find_one({'pot_id' : pot_id}, {'_id': 0,'url' : 1})

        if image == None:
            return False
        else:
            return image['url']

    def insert_data(self, id, ph, soil):
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour
        minute = now.minute

        data = {
            'pot_id' : id,
            'year' : year,
            'month' : month,
            'day' : day,
            'hour' : hour,
            'minute' : minute,
            'data' : {
                'ph': ph,
                'soil': soil,
                }
            }

        self.__collection_data.insert_one(data)

    def find_data(self, pot_id):
        cursor = self.__collection_data.find({'pot_id' : pot_id}, {'_id': 0, 'data.ph': 1, 'data.soil': 1}).sort('_id', -1).limit(10)
        raw_data = list(cursor)

        df = pd.json_normalize(raw_data)

        df = df[['data.ph', 'data.soil']].iloc[::-1]

        return df.rename(columns={'data.ph': 'ph', 'data.soil': 'soil'}).to_dict(orient='records')
