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
        filepath = path
        filepath += '\\'
        filepath += filename
        with open(filepath) as tsv:
            for line in csv.reader(tsv, delimiter="\t"):    # for every line (PR pair) in the current file
                # check whether this pr pair has already been added to the db:
                flag = 0
                cur.execute("SELECT * FROM duppr_pair")
                check = cur.fetchall()
                for check_line in check:
                    if (check_line[1] == line[0]) & (check_line[2] == line[1]) & (check_line[3] == line[3]):
                        flag = 1
                # if it has not, add it to the db:
                if flag == 0:
                    pr_pair_tuple = (line[0], int(line[1], 10), int(line[3], 10), float(line[4]), float(line[5]), float(line[6]),
                                     float(line[7]), float(line[8]), float(line[9]), float(line[10]), float(line[11]), float(line[12]),
                                     float(line[13]), float(line[14]), line[2])
                    cur.execute('INSERT INTO duppr_pair(repo, pr1, pr2, score, title, description, patch_content, patch_content_overlap, \
                        changed_file, changed_file_overlap, location, location_overlap, issue_number, commit_message, timestamp) \
                        VALUES ("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")', pr_pair_tuple)
    cur.execute("SELECT * FROM duppr_pair")
    data = cur.fetchall()
    for row in data:
        cur.execute("UPDATE duppr_pair SET repo=%s WHERE id=%s", (row[1].replace("'", ""), row[0],))    # if repo names have quotes, remove them.
        cur.execute("UPDATE duppr_pair SET timestamp=%s WHERE id=%s", (row[21].replace("'", ""), row[0],))   # if timestamps have quotes, remove them.
    # save changes and reload page:
    conn.commit()
    load_home()
    return load_home()


# Switches between show and hide mode

@app.route('/show-hide', methods=['POST'])
def show_hide_switch():
    global show_hide
    show_hide = request.form['show_hide_button']
    return load_home()


@app.route('/set-toppair')
def set_toppair(value, repo_id):
    cur.execute("UPDATE duppr_pair SET toppair=%s WHERE id=%s", (value, repo_id,))
    conn.commit()
    return


@app.route('/change-top-pair', methods=['POST'])
def change_toppair():
    repo_id = request.form['move']
    set_toppair(-1, repo_id)
    cur.execute("SELECT * FROM duppr_pair WHERE id=%s", (repo_id,))
    row = cur.fetchall()
    cur.execute("SELECT * FROM duppr_pair")
    data = cur.fetchall()
    for row_check in data:
        if (row[0][0] != row_check[0]) & (row[0][1] == row_check[1]):
            set_toppair(0, row_check[0])
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


# Finds & marks top pair

@app.route('/top-pair')
def top_pair():
    cur.execute("SELECT * FROM duppr_pair ORDER BY timestamp DESC")
    data_sorted = cur.fetchall()
    for row in data_sorted:
        # make a new list, with all the PR pairs from this repo
        data_check = []
        top_already_chosen = 0
        for row_check in data_sorted:
            # if both pairs are from the same repo, and if the one we're looking at isn't discarded
            #   & if the one we're looking at has been chosen as top
            #     then mark that for this repo, we have a manually chosen pair
            #   regardless, add the pair we're looking at to the list (of PR pairs within this repo)
            if (row_check[1] == row[1]) & (row_check[15] != -1):
                if row_check[20] == -1:
                    top_already_chosen = 1
                data_check.append(row_check)

        # if the current pair has not been used or discarded (row[15]==0) and has not been chosen as top
        #   if it is the most recent pair, then mark as 1 (toppair by timestamp)
        #   if it's not, then mark as 0 (default)
        if (row[15] == 0) & (top_already_chosen == 0):
            if row == data_check[0]:
                set_toppair(1, row[0])
            else:
                set_toppair(0, row[0])

        # if it *has* been discarded and there isn't already a comment sent to this repo
        # set toppair value to zero (default)
        elif (row[15] == -1) & (row[20] != 2):
            set_toppair(0, row[0])

        # if it *has* been used (comment's been sent)
        # set as top pair for this repo, update all others from this repo
        elif row[15] == 1:
            set_toppair(1, row[0])
            data_check.remove(row)
            for row_check in data_check:
                set_toppair(2, row_check[0])

        # if there is a pair in this repo that's been manually picked as top and this is not it
        # set toppair value to zero (default)
        elif (top_already_chosen == 1) & (row[20] != -1):
            set_toppair(0, row[0])

    conn.commit()
    return data_sorted


# Runs upon clicking 'send comment.' Edits comment_sent col in db.

@app.route('/home-sc', methods=['POST'])
def send_comment():
    repo_id = request.form['send_comment_button']                                   # gets row id (in db) from value of send_comment_button button
    cur.execute("SELECT * FROM duppr_pair WHERE id=%s", (repo_id,))                 # gets pr number & repo name
    pr_info = cur.fetchall()
    pr = int(pr_info[0][2], 10)                                                     # type as int
    repo = pr_info[0][1]
    PRcommenter.make_github_comment(repo, pr, "")                                   # sends comment
    cur.execute("UPDATE duppr_pair SET comment_sent=1 WHERE id=%s", (repo_id,))     # changes comment_sent value to 1 -- flags as sent
    conn.commit()                                                                   # saves changes
    print(cur.rowcount, "rows updated.")                                            # terminal notification to inform how many rows (repos) have been altered
    load_home()
    return load_home()


# Runs upon clicking 'don't send comment.' Edits comment_sent col in db.
# Adds repo (on home page) to rejects page/list.

@app.route('/home-no-sc', methods=['POST'])
def no_send_comment():
    repo_id = request.form['no_send_comment_button']                                # gets repo name from value of no_send_comment_button button
    cur.execute("UPDATE duppr_pair SET comment_sent=-1 WHERE id=%s", (repo_id,))    # changes comment_sent value to -1 (flags for moving to another list)
    conn.commit()                                                                   # saves changes
    print(cur.rowcount, "rows updated.")                                            # terminal notification to inform how many rows (repos) have been altered
    load_home()
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
    data_init = top_pair()
    for row in data_init:               # loop through pr pairs (rows)
        if row[15] != -1:               # don't display repos for which we've clicked "don't send comment"
            if row[20] == 1:
                data.append(row)
            elif row[20] == -1:
                data.append(row)
            elif (row[20] == 0) & (show_hide == "show"):
                data_dups.append(row)
            elif (row[20] == 2) & (show_hide == "show"):
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
