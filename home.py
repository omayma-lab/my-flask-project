from flask import Blueprint ,render_template ,session ,redirect
from flask import Blueprint
home =Blueprint ("home",__name__)


@home.route("/home")
def home_page():
    return "HOME PAGE 🚀"

@home.route("/")
def index():
    return "App is working"