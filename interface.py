from flask import Flask, redirect, request, render_template
from flaskext.mysql import MySQL
import mysql.connector
import PRcommenter
app = Flask(__name__)

# Connect to MySQL database
conn = mysql.connector.connect(user='root', password='***.', host='localhost', database='repolist', port='3306')
cur = conn.cursor()


@app.route('/')
def home():
    return reload_home()


# Runs when the notes 'save' button is clicked; edits notes column in database.

@app.route('/notes', methods=['POST'])
def notes():
    note = request.form['notebox']                                                  # get notes from textarea in html
    repo = request.form['save_button']                                              # get repo name
    cur.execute("UPDATE duppr_pair SET notes=%s WHERE repo=%s", (note, repo,))      # save notes to db
    conn.commit()                                                                   # save changes
    return reload_home()


# Runs upon clicking 'send comment.' Edits comment_sent col in db.
# todo: when clicked, change available buttons shown

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
    return reload_home()


# Runs upon clicking 'don't send comment.' Edits comment_sent col in db.
# todo: add a separate page for repos with this flag

@app.route('/home-no-sc', methods=['POST'])
def no_send_comment():
    repo = request.form['no_send_comment_button']                                # gets repo name from value of no_send_comment_button button
    cur.execute("UPDATE duppr_pair SET comment_sent=-1 WHERE repo=%s", (repo,))  # changes comment_sent value to 3 (flags for moving to another list)
    conn.commit()                                                                # saves changes
    print(cur.rowcount, "rows updated.")                                         # terminal notification to inform how many rows (repos) have been altered
    return reload_home()


def reload_home():
    cur.execute("SELECT * FROM duppr_pair")
    data_init = cur.fetchall()
    data = []
    for row in data_init:               # don't display repos for which we've clicked "don't send comment"
        if row[14] != -1:
            data.append(row)
    return render_template('interface.html', data=data)


if __name__ == '__main__':
    app.run()
