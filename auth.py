from flask import  Blueprint ,render_template , request,redirect,session

from db import get_db

import bcrypt
import random 
import smtplib
from email.mime.text import MIMEText
import uuid
from datetime import datetime, timedelta
auth = Blueprint ("auth", __name__)

def send_email(to_email, code):
    try:
        msg = MIMEText(f"your verification code is: {code}")
        msg["Subject"] = "verification code"
        msg["From"] = "your_email@gmail.com"
        msg["To"] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        server.login("your_email@gmail.com", "efrk zwel arvz ievb")

        server.send_message(msg)
        server.quit()

        print("EMAIL SENT SUCCESS ")

    except Exception as e:
        print("EMAIL ERROR ", e)
@auth.route("/register", methods=["Get","POST"])
def register():
    
    db = get_db()
    cursor =db.cursor(dictionary=True)
    if request.method=="POST":
        nom =request.form["nom"]
        email = request.form["email"]
        password= request.form["password"]
        # hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
        
        role ="utilisateur"
        #check email
        cursor.execute("SELECT * FROM users where email =%s",(email,))
        user= cursor.fetchone()
        if user:
            return render_template("register.html", message = "Email déja existe")
        #insert user 
        code = str(random.randint(100000,999999))
        cursor.execute("INSERT INTO users(nom,email,password,role,verification_code)VALUES(%s, %s, %s,%s,%s)",(nom, email, hashed_password,role,code))
        user_id = cursor.lastrowid

        cursor.execute("INSERT INTO logs (user_id, action, date) VALUES (%s,%s,NOW())",(user_id, "inscription"))

        db.commit()

        cursor.close()
        db.close()
        send_email( email , code)
        session["verify_email"]= email
        return redirect("/verification")
    
    return render_template("register.html")

@auth.route("/verification",methods=["GET","POST"])
def verification():
    db = get_db()
    cursor =db.cursor(dictionary=True)
    email = session.get("verify_email")
    if not email :
         return redirect("/register")
    if request.method =="POST":
        code =request.form["code"]
        
        cursor.execute("SELECT * FROM users WHERE email=%s and verification_code=%s",( email, code,))
        user = cursor.fetchone();
        if user :
            cursor.execute("UPDATE users SET is_verified=1, status='pending' where id =%s",(user["id"],))
            db.commit()
            cursor.close()
            db.close()
            session.pop("verify_email",None)
            return redirect("/login?success=Compte vérifié avec succès ✅")
        else:
            return render_template("verification.html",error="code incorrect")
        
    return render_template("verification.html")

   

@auth.route("/login", methods=["GET", "POST"])
def login():
    db = get_db()
    cursor =db.cursor(dictionary=True)
    success =request.args.get("success")
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        cursor.execute("SELECT * FROM users WHERE email=%s ", (email,))
        user = cursor.fetchone()
        if not user :
            return render_template("login.html", error = "Email incorrect ❌")
        if not  bcrypt.checkpw(password.encode('utf-8'),user["password"].encode('utf-8')) :
            return render_template("login.html", error ="mot de passe incorrect ❌")

        
        if  user["is_verified"]==0:
            return render_template("login.html", error = "veuillez vérifier votre email ❌")
        if user["status"] !="active":
            return render_template("login.html", error = "Compte non approuvé pour le moment ❌")
        
        session["user_id"] = user["id"]
        session["role"] = user["role"] 
        session_token = str (uuid.uuid4()) 

        ip = request.remote_addr
        user_agent = request.headers.get("User-Agent")

        expires_at = datetime.now() + timedelta(days=1)
        cursor.execute("""INSERT INTO user_session (user_id, session_token,ip_address, user_agent, expires_at, is_revoked, created_at) VALUES(%s,%s,%s,%s,%s,0,NOW())""",(user["id"], session_token ,ip, user_agent, expires_at))
        session["session_token"]= session_token

        cursor.execute("INSERT INTO logs (user_id, action, DATE) VALUES(%s,%s,Now())",(user["id"],"login"))
        db.commit()
        cursor.close()
        db.close()
        
        return redirect("/admin" if user["role"]== "admin" else "/home")

    return render_template("login.html", success=success) 

@auth.route("/forgot-password",methods=["GET", "POST"])
def forgt_password():
    db = get_db()
    cursor= db.cursor(dictionary=True)
    email= request.args.get("email")
    if request.method =="POST":
        email= request.form["email"]
        cursor.execute("SELECT * FROM users where email=%s ",(email,))
        user= cursor.fetchone()
        if not user :
            return render_template("forgot-password.html",error= "Email non trouvé",email=email)
         
        token = str (uuid.uuid4()) 
        expires_at= datetime.now() + timedelta(minutes=15)
        cursor.execute( " INSERT into password_resets (user_id, token, expires_at, used, created_at) values(%s,%s,%s,0,NOW())",(user["id"], token, expires_at))
        db.commit()
        cursor.close()
        db.close()
        #reset link 
        reset_link= f"https://gunicorn-app-production-13f0.up.railway.app/reset_password/{token}"
        #send email
        send_email( email,f"Lien de réinitialisation:{reset_link}")
        return render_template("forgot-password.html",success="Lien envoyé par email ✅",email=email)
    return render_template("forgot-password.html",email=email)

@auth.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM password_resets WHERE token=%s AND used=0",
        (token,)
    )

    reset = cursor.fetchone()
    if not reset:
        return "Lien invalide ❌"
    if reset["expires_at"] < datetime.now():
        return "Lien expiré ❌"

    

    if request.method == "POST":

        password = request.form["password"]

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute(
            "UPDATE users SET password=%s WHERE id=%s",
            (hashed_password, reset["user_id"])
        )

        cursor.execute(
            "UPDATE password_resets SET used=1 WHERE id=%s",
            (reset["id"],)
        )

        db.commit()
        cursor.close()
        db.close()

        return redirect(
            "/login?success=Mot de passe modifié avec succès ✅"
        )

    return render_template(
        "reset_password.html"
    )

    