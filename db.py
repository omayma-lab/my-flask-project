import mysql.connector
def get_db():
    return mysql.connector.connect(
        host="mysql-1d69b561-my-flask-projectt.c.aivencloud.com",
        port='11637',
        user ="avnadmin",
        password="AVNS_d-Czq0Rmam2PLwH78xU",
        database="defaultdb",
        ssl_mode='REQUIRED'
    )
print("DB connected successsfully")