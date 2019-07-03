from flask import Flask, redirect, request, render_template
from flaskext.mysql import MySQL
import mysql.connector
app = Flask(__name__)

# mysql = MySQL(app)
conn = mysql.connector.connect(user ='root', password='---.', host='localhost', database='repolist', port='3306')
cur = conn.cursor()

# @app.before_request
# def before_request():
#     print('connecting... ')
#     global conn
#     conn = sqlite3.connect("repoList.db")
#     print('connected!')
#
# @app.teardown_request
# def teardown_request(exception):
#     if hasattr(g, 'db'):
#         conn.close()


@app.route('/')
def notes():
    cur.execute("SELECT * FROM rl")
    data = cur.fetchall()
    return render_template('interface.html', data=data)


@app.route('/')
def send_comment():
    name = request.form['name']
    cur.execute("UPDATE rl SET 1 WHERE repo=%s" % name)
    cur.execute("SELECT * FROM rl")
    data = cur.fetchall()
    return render_template('interface.html', data=data)


@app.route('/')
def no_send_comment():
    name = request.form['name']
    cur.execute("UPDATE rl SET 3 WHERE repo=%s" % name)
    cur.execute("SELECT * FROM rl")
    data = cur.fetchall()
    return render_template('interface.html', data=data)


if __name__ == '__main__':
    app.run()
