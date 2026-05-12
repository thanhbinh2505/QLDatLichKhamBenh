from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = "k8HDLZbie2T8UWvC70S7f-SukGY"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:1234@localhost/hospitaldb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app)
login = LoginManager(app=app)

