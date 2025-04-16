from controller import Controller
from flask import Flask

app = Flask(__name__)
controller = Controller(app)

if __name__ == '__main__':
    controller.run()