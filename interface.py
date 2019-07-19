#
#
# INTERFACE.PY
#
# An interface webpage for viewing potentially redundant pairs of GitHub pull request & for sending
# out comments to them. Interacts with a MySQL database called duppr_pair, which is structured with
# the following columns and values:
#       0: id - a unique key for each pair of PRs
#       1: repo - the name of the repository the PRs are contained within
#       2: pr1 - the number of the primary repository
#       3: pr2 - the number of the secondary repository
#       4: score - the similarity score of the pair
#       5-14: {feature scores of the pair}
#       15: comment_sent - records if a comment has been sent to this pair (1), if it has not yet
#           been sent (0), or if this pair has been added to the 'do not send' list (-1)
#       16: notes - a blob for storing any notes that the users of this webpage may want to record
#       17-19: {not currently in use}
#       20: toppair - (0) if the pair is marked as 'not a top pair' (default)
#                     (1) if the pair is the most recent pair from its repo, or if a comment has been
#                         sent to this pair
#                     (-1) if the pair has been manually chosen as top pair
#                     (2) if a comment has been sent to another pair from the current pair's repo
#       21: timestamp - the timestamp of the most recent pr in the pair. Format: yyyy-mm-ddThh:ee:ssZ
#           where y is year, m is month, d is day, h is hour (24-hr), e is minute, and s is second
# This page, using the 'update' button, pulls .txt tab-separated files from a local file to fill in
# PR pair entries to the database. It uses Flask to connect to the database and render its entries.
# It also uses PRcommenter.py to send out comments to the pull requests listed.
#
#

from flask import Flask, redirect, request, render_template
from datetime import datetime, timedelta
from flaskext.mysql import MySQL
import mysql.connector
import csv
import os
import platform
import PRcommenter
app = Flask(__name__)

# Connect to MySQL database
with open('input/mysqlParams.txt') as f:
    MYSQL_USER, MYSQL_PASS, MYSQL_HOST = f.read().splitlines()
conn = mysql.connector.connect(user=MYSQL_USER, password=MYSQL_PASS, host=MYSQL_HOST, database='repolist', port='3306')
cur = conn.cursor()
# Create flag for showing all PR pairs vs one per repo
show_hide = 'hide'


# Updates database by parsing files
# Removes pairs if they're 2+ days old

@app.route('/update-db', methods=['POST'])
def update_db():
    # get the current date
    date = (datetime.now() - timedelta(2)).isoformat()
    if platform.system() == 'Windows':
        path = 'C:\\Users\\annik\\Documents\\REUSE\\interface\\dupPR'
    elif platform.system() =='Linux':
        path = '/DATA/luyao'
    else:
        path = '/Users/shuruiz/Work/researchProjects'
    # for every file (repository) in the dupPR directory
    for filename in os.listdir(path):
        # find path to this file
        filepath = path
        if platform.system() == 'Windows':
            filepath += '\\'
        else:
            filepath += '/'
        filepath += filename
        # open this file
        with open(filepath) as tsv:
            # for every line (PR pair) in the current file
            for line in csv.reader(tsv, delimiter="\t"):
                # check whether this pr pair has already been added to the db:
                flag = 0
                cur.execute("SELECT * FROM duppr_pair")
                check = cur.fetchall()
                # for every pair already in the db
                for check_line in check:
                    # if they share the same repo name, pr1 name, and pr2 name, flag as already added
                    if (check_line[1] == line[0]) & (check_line[2] == line[1]) & (check_line[3] == line[3]):
                        flag = 1
                # if it has not already been added, and if it is newer than 2 days, add it to the db:
                if (flag == 0) & (date < line[2]):
                    pr_pair_tuple = (line[0], int(line[1], 10), int(line[3], 10), float(line[4]), float(line[5]), float(line[6]),
                                     float(line[7]), float(line[8]), float(line[9]), float(line[10]), float(line[11]), float(line[12]),
                                     float(line[13]), float(line[14]), line[2])
                    cur.execute('INSERT INTO duppr_pair(repo, pr1, pr2, score, title, description, patch_content, patch_content_overlap, \
                        changed_file, changed_file_overlap, location, location_overlap, issue_number, commit_message, timestamp) \
                        VALUES ("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")', pr_pair_tuple)
    # grab all pairs from the updated database, and format each in a more friendly way
    cur.execute("SELECT * FROM duppr_pair")
    data = cur.fetchall()
    for row in data:
        cur.execute("UPDATE duppr_pair SET repo=%s WHERE id=%s", (row[1].replace("'", ""), row[0],))        # if repo names have quotes, remove them.
        cur.execute("UPDATE duppr_pair SET timestamp=%s WHERE id=%s", (row[21].replace("'", ""), row[0],))  # if timestamps have quotes, remove them.
        # delete any pairs that are older than 2 days if they haven't had a comment sent to them yet
        if (date > row[21]) & (row[15] != 1):
            cur.execute("DELETE FROM duppr_pair WHERE id=%s", (row[0],))
    # save changes and reload page:
    conn.commit()
    load_home()
    return load_home()


# Switches between show and hide mode
# Show: all pairs visible. Hide: only one pair per repo visible.

@app.route('/show-hide', methods=['POST'])
def show_hide_switch():
    global show_hide
    show_hide = request.form['show_hide_button']    # check whether user clicked "show" button or "hide" button
    return load_home()


# Sets toppair value
# Arguments: value, the value to set toppair to
#            pair_id, the id of the pair whose value we're changing

@app.route('/set-toppair')
def set_toppair(value, pair_id):
    cur.execute("UPDATE duppr_pair SET toppair=%s WHERE id=%s", (value, pair_id,))
    conn.commit()
    return


# Runs upon user clicking "Choose this [pair] instead".
# Manually sets the given pair (identified by id returned by 'move' form request) as the top pair for its repo.
# This entails setting its toppair value to -1, and that of all others within its repo to 0.

@app.route('/change-top-pair', methods=['POST'])
def change_toppair():
    pair_id = request.form['move']                                      # get id of the pair in question
    set_toppair(-1, pair_id)                                            # set its toppair value to -1
    cur.execute("SELECT * FROM duppr_pair WHERE id=%s", (pair_id,))     # get the entire row corresponding to this pair
    row = cur.fetchall()
    cur.execute("SELECT * FROM duppr_pair")                             # get all rows from the db
    data = cur.fetchall()
    for row_check in data:                                              # look at each row in the database
        if (row[0][0] != row_check[0]) & (row[0][1] == row_check[1]):   # if the current row is not the original row, but if they are from the same repo
            set_toppair(0, row_check[0])                                # set the current row's toppair value to -1
    # save changes and reload page
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


# Finds & marks the 'top pair' (most recent) in each repository
# Edits toppair column in database.
# Called during loading of homepage.

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

    conn.commit()           # save changes
    return data_sorted      # return the sorted list of all pairs


# Runs upon clicking 'send comment.' Edits comment_sent col in db.

@app.route('/home-sc', methods=['POST'])
def send_comment():
    pair_id = request.form['send_comment_button']                                   # get row id (in db) from value of send_comment_button button
    cur.execute("SELECT * FROM duppr_pair WHERE id=%s", (pair_id,))                 # get info about pr pair
    pr_info = cur.fetchall()
    pr = int(pr_info[0][2], 10)                                                     # get pr number, type as int
    repo = pr_info[0][1]                                                            # get repo name
    PRcommenter.make_github_comment(repo, pr, "")                                   # send comment
    cur.execute("UPDATE duppr_pair SET comment_sent=1 WHERE id=%s", (pair_id,))     # change comment_sent value to 1 -- flags as sent
    conn.commit()                                                                   # save changes
    print(cur.rowcount, "rows updated.")                                            # terminal notification to inform how many rows (pairs) have been altered
    load_home()                                                                     # reload page. FYI: not sure why two load_homes are required, but they seem to be.
    return load_home()


# Runs upon clicking 'don't send comment.' Edits comment_sent col in db.
# Adds repo (on home page) to rejects page/list.

@app.route('/home-no-sc', methods=['POST'])
def no_send_comment():
    pair_id = request.form['no_send_comment_button']                                # get row id (in db) from value of no_send_comment_button button
    cur.execute("UPDATE duppr_pair SET comment_sent=-1 WHERE id=%s", (pair_id,))    # change comment_sent value to -1 (flags for moving to another list)
    conn.commit()                                                                   # save changes
    print(cur.rowcount, "rows updated.")                                            # terminal notification to inform how many rows (pairs) have been altered
    load_home()
    return load_home()


# Runs upon clicking 'reset.' Edits comment_sent col in db.
# Adds repo (on rejects page) back to home page.

@app.route('/rejects-reset-sc', methods=['POST'])
def reset_send_comment():
    pair_id = request.form['reset_button']                                          # get row id (in db) from value of reset_button button
    cur.execute("UPDATE duppr_pair SET comment_sent=0 WHERE id=%s", (pair_id,))     # change comment_sent value to 0 (flags for returning to main list)
    conn.commit()                                                                   # save changes
    print(cur.rowcount, "rows updated.")                                            # terminal notification to inform how many rows (pairs) have been altered
    return load_reject_page()


# Render homepage
# Lists:
#   data[] - top pairs to be displayed in the homepage
#   data_dups[] - non-top pairs to be displayed in the homepage (if the show_hide switch is on "show")
#   data_init[] - all pairs

@app.route('/')
def load_home():
    data = []
    data_dups = []
    data_init = top_pair()
    for row in data_init:               # loop through pr pairs (rows)
        if row[15] != -1:               # don't display repos for which we've clicked "don't send comment"
            if (row[20] == 1) or (row[20] == -1):
                data.append(row)
            elif (row[20] == 0) & (show_hide == "show"):
                data_dups.append(row)
            elif (row[20] == 2) & (show_hide == "show"):
                data_dups.append(row)
    return render_template('interface.html', data=data, id="home", data_dups=data_dups)


# Render page with rejected PR pairs
# Lists:
#   data[] - rejected pairs, to be displayed on this page
#   data_init[] - all pairs

@app.route('/rejects')
def load_reject_page():
    cur.execute("SELECT * FROM duppr_pair")     # get all pr pairs from the db
    data_init = cur.fetchall()
    data = []
    for row in data_init:                       # loop through pr pairs (rows)
        if row[15] == -1:                       # only display repos for which we've clicked "don't send comment"
            data.append(row)
    return render_template('interface.html', data=data, id="rejects", data_dups=[])


if __name__ == '__main__':
    app.run()
