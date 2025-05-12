from decouple import config
from flask import Flask
from flask_wtf.csrf import CSRFProtect

# from .utils import

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = config("SECRET_KEY")
csrf = CSRFProtect(app)
