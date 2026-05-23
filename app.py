from flask import Flask
from auth import auth
from admin import admin
from home import home
app = Flask(__name__)
app.secret_key = "secret123"
app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(home)
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
    