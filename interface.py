from flask import Flask, redirect, request, render_template
from flaskext.mysql import MySQL
import mysql.connector
import PRcommenter
app = Flask(__name__)

# Connect to MySQL database
conn = mysql.connector.connect(user ='root', password='***.', host='localhost', database='repolist', port='3306')
cur = conn.cursor()


# Runs when the notes 'save' button is clicked; edits notes column in database.
# todo: all. Currently just reloads page.

@app.route('/')
def notes():
    # LOAD PAGE: homepage
    cur.execute("SELECT * FROM duppr_pair")
    data = cur.fetchall()
    return render_template('interface.html', data=data)


# Runs upon clicking 'send comment.' Edits comment_sent col in db.
# todo: change structure of db for comment_sent flags
#       connect to PRcommenter.py

@app.route('/home-sc', methods=['POST'])
def send_comment():
    repo = request.form['send_comment_button']                                  # gets repo name from value of send_comment_button button
    cur.execute("SELECT pr1 FROM duppr_pair WHERE repo=%s", (repo,))            # gets pr number
    pr = cur.fetchall()
    pr = int(pr[0][0], 10)                                                      # type as int
    PRcommenter.make_github_comment(repo, pr, "")                               # sends comment
    cur.execute("UPDATE duppr_pair SET comment_sent=1 WHERE repo=%s", (repo,))  # changes comment_sent value to 1 -- flags as sent
    conn.commit()                                                               # saves changes
    print(cur.rowcount, "rows updated.")                                        # terminal notification to inform how many rows (repos) have been altered
    # LOAD PAGE: homepage
    cur.execute("SELECT * FROM duppr_pair")
    data = cur.fetchall()
    return render_template('interface.html', data=data)


# Runs upon clicking 'don't send comment.' Edits comment_sent col in db.
# todo: determine why this func isn't working even though send_comment is
#       add a separate page for repos with this flag

@app.route('/home-no-sc', methods=['POST'])
def no_send_comment():
    repo = request.form['no_send_comment_button']                           # gets repo name from value of no_send_comment_button button
    cur.execute("UPDATE duppr_pair SET comment_sent=3 WHERE repo=%s", (repo,))      # changes comment_sent value to 3 (flags for moving to another list)
    conn.commit()                                                           # saves changes
    print(cur.rowcount, "rows updated.")                                    # terminal notification to inform how many rows (repos) have been altered
    # LOAD PAGE: homepage
    cur.execute("SELECT * FROM duppr_pair")
    data = cur.fetchall()
    return render_template('interface.html', data=data)


if __name__ == '__main__':
    app.run()
