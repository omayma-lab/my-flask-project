from flask import Blueprint ,render_template ,session ,redirect

home =Blueprint ("home",__name__)

@home.route("/")
def index():
    return "App is working "