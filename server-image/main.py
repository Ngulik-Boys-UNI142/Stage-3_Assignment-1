from controller import Controller
from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
controller = Controller(app)

if __name__ == '__main__':
    controller.run()
