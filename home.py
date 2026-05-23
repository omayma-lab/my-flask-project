from flask import Blueprint ,render_template ,session ,redirect
from db import get_db
home =Blueprint ("home",__name__)
@home.route("/home")
def home_page():
    if "user_id" not in session:
        return redirect("/login")
    db = get_db()
    cursor=db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id=%s",(session["user_id"],))
    user = cursor.fetchone()
    return render_template("home.html",user=user)