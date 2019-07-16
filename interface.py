from flask import Flask, redirect, request, render_template
from flaskext.mysql import MySQL
import mysql.connector
import csv
import os
import PRcommenter
app = Flask(__name__)


# Connect to MySQL database
conn = mysql.connector.connect(user='root', password='***.', host='localhost', database='repolist', port='3306')
cur = conn.cursor()
# Create flag for showing all PR pairs vs one per repo
show_hide = 'show'


# Updates database by parsing files

@app.route('/update-db', methods=['POST'])
def update_db():
    path = 'C:\\Users\\annik\\Documents\\REUSE\\interface\\dupPR'
    for filename in os.listdir(path):                       # for every file (repository) in the dupPR directory
        path += '\\'
        path += filename
        with open(path) as tsv:
            for line in csv.reader(tsv, delimiter="\t"):    # for every line (PR pair) in the current file
                # check whether this pr pair has already been added to the db:
                flag = 0
                cur.execute("SELECT * FROM duppr_pair")
                check = cur.fetchall()
                for check_line in check:
                    if (check_line[1] == line[0]) & (check_line[2] == line[1]) & (check_line[3] == line[2]):
                        flag = 1
                # if it has not, add it to the db:
                if flag == 0:
                    pr_pair_tuple = (line[0], int(line[1], 10), int(line[2], 10), float(line[3]), float(line[4]),
                                     float(line[5]), float(line[6]), float(line[7]), float(line[8]),
                                     float(line[9]), float(line[10]), float(line[11]), float(line[12]), float(line[13]))
                    cur.execute('INSERT INTO duppr_pair(repo, pr1, pr2, score, title, description, patch_content, patch_content_overlap, \
                        changed_file, changed_file_overlap, location, location_overlap, issue_number, commit_message) \
                        VALUES ("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")', pr_pair_tuple)
    # save changes and reload page:
    conn.commit()
    return load_home()


# Switches between show and hide mode

@app.route('/show-hide', methods=['POST'])
def show_hide_switch():
    global show_hide
    show_hide = request.form['show_hide_button']
    return load_home()


@app.route('/change-top-pair', methods=['POST'])
def change_toppair():
    repo_id = request.form['move']
    cur.execute("UPDATE duppr_pair SET toppair=-1 WHERE id=%s", (repo_id,))     # save notes to db
    cur.execute("SELECT * FROM duppr_pair WHERE id=%s", (repo_id,))
    row = cur.fetchall()
    cur.execute("SELECT * FROM duppr_pair")
    data = cur.fetchall()
    for row_check in data:
        if (row[0][0] != row_check[0]) & (row[0][1] == row_check[1]):
            cur.execute("UPDATE duppr_pair SET toppair=0 WHERE id=%s", (row_check[0],))
    conn.commit()
    return load_home()


# Runs when the notes 'save' button is clicked; edits notes column in database.

@app.route('/notes', methods=['POST'])
def notes():
    note = request.form['notebox']                                                  # get notes from textarea in html
    repo_id = request.form['save_button']                                           # get repo name
    cur.execute("UPDATE duppr_pair SET notes=%s WHERE id=%s", (note, repo_id,))     # save notes to db
    conn.commit()                                                                   # save changes
    return load_home()


# Runs upon clicking 'send comment.' Edits comment_sent col in db.

@app.route('/home-sc', methods=['POST'])
def send_comment():
    repo_id = request.form['send_comment_button']                                   # gets repo name from value of send_comment_button button
    cur.execute("SELECT pr1 FROM duppr_pair WHERE id=%s", (repo_id,))               # gets pr number
    pr = cur.fetchall()
    pr = int(pr[0][0], 10)                                                          # type as int
    PRcommenter.make_github_comment(repo, pr, "")                                   # sends comment
    cur.execute("UPDATE duppr_pair SET comment_sent=1 WHERE id=%s", (repo_id,))     # changes comment_sent value to 1 -- flags as sent
    conn.commit()                                                                   # saves changes
    print(cur.rowcount, "rows updated.")                                            # terminal notification to inform how many rows (repos) have been altered
    return load_home()


# Finds & marks top pair

@app.route('/top-pair')
def top_pair(data):
    data_check = data
    for row in data:
        if row[15] == 0:            # if the pair isn't in the "don't send comment" section
            if row[21] != -1:       # if this pair hasn't been chosen manually for this repo
                for row_check in data_check:
                    if (row[0] != row_check[0]) & (row[1] == row_check[1]) & (row_check[21] != -1) & (row_check[15] != -1):
                        if (row_check[21] == 1) & (row[4] > row_check[4]):
                            cur.execute("UPDATE duppr_pair SET toppair=1 WHERE id=%s", (row[0],))
                            cur.execute("UPDATE duppr_pair SET toppair=0 WHERE id=%s", (row_check[0],))
                        if (row[21] == 1) & (row[4] < row_check[4]):
                            cur.execute("UPDATE duppr_pair SET toppair=0 WHERE id=%s", (row[0],))
                            cur.execute("UPDATE duppr_pair SET toppair=1 WHERE id=%s", (row_check[0],))
                    elif row_check[21] == -1:
                        cur.execute("UPDATE duppr_pair SET toppair=0 WHERE id=%s", (row[0],))
        elif row[15] == -1:
            cur.execute("UPDATE duppr_pair SET toppair=0 WHERE id=%s", (row[0],))
        else:
            cur.execute("UPDATE duppr_pair SET toppair=1 WHERE id=%s", (row[0],))
            for row_check in data_check:
                if (row[0] != row_check[0]) & (row[1] == row_check[1]):
                    cur.execute("UPDATE duppr_pair SET toppair=2 WHERE id=%s", (row_check[0],))
    conn.commit()
    return data


# Runs upon clicking 'don't send comment.' Edits comment_sent col in db.
# Adds repo (on home page) to rejects page/list.

@app.route('/home-no-sc', methods=['POST'])
def no_send_comment():
    repo_id = request.form['no_send_comment_button']                                # gets repo name from value of no_send_comment_button button
    cur.execute("UPDATE duppr_pair SET comment_sent=-1 WHERE id=%s", (repo_id,))    # changes comment_sent value to -1 (flags for moving to another list)
    conn.commit()                                                                   # saves changes
    print(cur.rowcount, "rows updated.")                                            # terminal notification to inform how many rows (repos) have been altered
    return load_home()


# Runs upon clicking 'reset.' Edits comment_sent col in db.
# Adds repo (on rejects page) back to home page.

@app.route('/rejects-reset-sc', methods=['POST'])
def reset_send_comment():
    repo_id = request.form['reset_button']                                          # gets repo name from value of no_send_comment_button button
    cur.execute("UPDATE duppr_pair SET comment_sent=0 WHERE id=%s", (repo_id,))     # changes comment_sent value to 0 (flags for returning to main list)
    conn.commit()                                                                   # saves changes
    print(cur.rowcount, "rows updated.")                                            # terminal notification to inform how many rows (repos) have been altered
    return load_reject_page()


# Render homepage

@app.route('/')
def load_home():
    data = []
    data_dups = []
    cur.execute("SELECT * FROM duppr_pair")
    data_init = cur.fetchall()
    data_init = top_pair(data_init)
    for row in data_init:               # loop through pr pairs (rows)
        cur.execute("UPDATE duppr_pair SET repo=%s WHERE id=%s", (row[1].replace("'", ""), row[0],))    # if repo names have quotes, remove them.
        if row[15] != -1:               # don't display repos for which we've clicked "don't send comment"
            if row[21] == 1 or -1:
                data.append(row)
            elif (row[21] == 0 or 2) & (show_hide == "show"):
                data_dups.append(row)
    return render_template('interface.html', data=data, id="home", data_dups=data_dups)


# Render page with rejected PR pairs

@app.route('/rejects')
def load_reject_page():
    cur.execute("SELECT * FROM duppr_pair")
    data_init = cur.fetchall()
    data = []
    for row in data_init:               # only display repos for which we've clicked "don't send comment"
        if row[15] == -1:
            data.append(row)
    return render_template('interface.html', data=data, id="rejects", data_dups=[])


if __name__ == '__main__':
    app.run()
