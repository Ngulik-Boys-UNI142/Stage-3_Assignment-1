from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import pandas as pd
import os

class Model():
    def __init__(self):
        self.__client = MongoClient(os.environ.get("MONGODB_API"),  server_api=ServerApi('1'))
        try:
            self.__database = self.__client.get_database('smartfarm')
            self.__collection = self.__database.get_collection('data')
        except Exception as e:
            print(f'Error: {e}')


    def insert_data(self, ph, soil):
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour
        minute = now.minute

        data = {
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
        
        self.__collection.insert_one(data)
    
    def find_data(self):
        cursor = self.__collection.find({}, {'_id': 0, 'data.ph': 1, 'data.soil': 1}).sort('_id', -1).limit(10)
        raw_data = list(cursor)

        df = pd.json_normalize(raw_data) 

        df = df[['data.ph', 'data.soil']].iloc[::-1]  

        return df.rename(columns={'data.ph': 'ph', 'data.soil': 'soil'}).to_dict(orient='records')