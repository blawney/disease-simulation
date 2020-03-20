import os

from flask import Flask
from flask_session import Session

sess = Session()

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY=os.environ['SECRET_KEY'],
    SESSION_TYPE='filesystem'
)
sess.init_app(app)

from simulator_app import routes
