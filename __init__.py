from flask import Flask

from .events import socketio
from .routes import main

def create_app():
    app = Flask(__name__)
    app.config["DEBUG"] = True
    app.config["SECRET_KEY"] = "abcdef"

    app.register_blueprint(main)

    socketio.init_app(app, manage_session=True)

    return app