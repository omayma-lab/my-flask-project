from flask import Blueprint  ,render_template, request ,session,redirect
from db import get_db

admin =Blueprint ("admin",__name__)
@admin.route("/admin")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Accès refusé ❌"

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # total users

    cursor.execute(
        "SELECT COUNT(*) as total FROM users where role!='admin' "
    )

    total_users = cursor.fetchone()["total"]
    
     # active users

    cursor.execute(
        "SELECT COUNT(*) as active FROM users WHERE status='active' and role!='admin'"
    )

    active_users = cursor.fetchone()["active"]


    # logs

    cursor.execute(
        "SELECT COUNT(*) as total_logs FROM logs join users on logs.user_id= users.id where role!='admin'"
    )

    total_logs= cursor.fetchone()["total_logs"]

    # sessions

    cursor.execute(
        "SELECT COUNT(*) as total_sessions FROM user_session join users on user_session.user_id= users.id where users.role!='admin'"
    )
    total_sessions = cursor.fetchone()["total_sessions"]
    #notification
    
    cursor.execute(""" SELECT nom, email FROM users WHERE status = 'pending' and role!='admin' ORDER BY id DESC """)

    notifications = cursor.fetchall()
    notification_count = len(notifications)
   # pending ...
    cursor.execute(
    "SELECT COUNT(*) as pending FROM users WHERE status='pending'")

    pending_users = cursor.fetchone()["pending"]


    cursor.execute(
    "SELECT COUNT(*) as blocked FROM users WHERE status='blocked'")

    blocked_users = cursor.fetchone()["blocked"] 
    #plus active
    cursor.execute("""SELECT users.nom,COUNT(user_session.id) as total FROM user_session JOIN users ON users.id = user_session.user_id where users.role!='admin'

        GROUP BY users.nom ORDER BY total DESC LIMIT 5 """)

    top_users = cursor.fetchall()
    
    

    cursor.close()
    db.close()
   

    return render_template(
        "admin_dashboard.html",
        top_users = top_users ,
        active_users=active_users,
        pending_users=pending_users,
        blocked_users=blocked_users,
        total_logs=total_logs,
        
        notification_count=notification_count,

        notifications= notifications,

        total_users=total_users,

        

        total_sessions=total_sessions
    )



@admin.route("/admin/users")
def users():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Accès refusé ❌"

    db = get_db()

    cursor = db.cursor(dictionary=True)

    page = request.args.get('page', 1, type=int)

    per_page = 5

    offset = (page - 1) * per_page

    cursor.execute(
    "SELECT * FROM users WHERE role!='admin' LIMIT %s OFFSET %s",
    (per_page, offset)
)

    users = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as total FROM users where role!='admin' ")
    total_users = cursor.fetchone()["total"]
    total_pages = (total_users + per_page - 1) // per_page

    cursor.execute(
        "SELECT COUNT(*) as active FROM users WHERE status='active' and  role!='admin'"
    )
    active_users = cursor.fetchone()["active"]

    cursor.execute(
        "SELECT COUNT(*) as pending FROM users WHERE status='pending'"
    )
    pending_users = cursor.fetchone()["pending"]

    cursor.close()
    db.close()

    return render_template(
        "admin_users.html",
        users=users,
        total_users=total_users,
        active_users=active_users,
        pending_users=pending_users,
        page=page,
        total_pages=total_pages
    )


@admin.route("/admin/user/toggle/<int:user_id>")
def toggle_user(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Accès refusé ❌"

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT status FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    if not user:
        return "User not found ❌"

   
    if user[0] == "active":
        new_status = "blocked"
    else:
        new_status = "active"

    cursor.execute(
        "UPDATE users SET status=%s WHERE id=%s",
        (new_status, user_id)
    )

    db.commit()
    cursor.close()
    db.close()

    return redirect("/admin/users")

@admin.route("/admin/user/delete/<int:user_id>")
def delete_user(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Accès refusé ❌"

    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))

    db.commit()
    cursor.close()
    db.close()

    return redirect("/admin/users")

@admin.route("/admin/sessions")
def sessions():

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT users.nom,
               users.email,
               user_session.ip_address,
               user_session.user_agent,
               user_session.created_at,
               user_session.expires_at,
               user_session.is_revoked
        FROM user_session
        JOIN users
        ON users.id = user_session.user_id and role!='admin'

        ORDER BY user_session.created_at DESC
    """)

    sessions_data = cursor.fetchall()

    return render_template(
        "admin_sessions.html",
        sessions=sessions_data
    )
@admin.route("/admin/logs")
def logs_page():
    if "user_id" not in session:
        return redirect("/login")
    db= get_db()
    cursor=db.cursor(dictionary=True)
    cursor.execute("""select users.nom,logs.action,logs.date
                   FROM logs JOIN users on users.id = logs.user_id and users.role!="admin" ORDER BY logs.date DESC  """)
    logs =cursor.fetchall()
    return render_template("admin_logs.html",logs=logs )

@admin.route ("/admin/logout")
def logout():
    db= get_db()
    cursor=db.cursor()
    token= session .get("session_token")
    if token:
        cursor.execute("""UPDATE user_session SET is_revoked=1 WHERE session_token=%s""",(token,))
        db.commit()
    session.clear()
    return redirect("/login")
