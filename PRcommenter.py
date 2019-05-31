import json
import requests

# Authentication info
USERNAME = 'akinnae'
TOKEN = '703ac8d71e771a38df424b15b7345d9571161d8f'

# The repository to add this issue to
REPO_OWNER = 'akinnae'
REPO_NAME = 'curly-train'
PR_NUMBER = 1

def make_github_comment(body=None, commit_id=None, path=None, position=None):
    '''Create a comment on github.com using the given parameters.'''
    # Our url to create comments via POST
    url = 'https://api.github.com/repos/%s/%s/pulls/%i/comments' % (REPO_OWNER, REPO_NAME, PR_NUMBER)
    # Create an authenticated session to create the comment
    headers = {
        "Authorization": "token %s" % TOKEN,
#        "Accept": "application/vnd.github.golden-comet-preview+json"
    }
#    session = requests.session(auth=(USERNAME, TOKEN))
    # Create our comment
    data = {'comment': {'body': body,
             'commit_id': commit_id,
             'path': path,
             'position': position}}
    # Add the comment to our repository
    r = requests.request(json.dumps(data), url, headers=headers)
    if r.status_code == 201:
        print('Successfully created comment "%s"' % body)
    else:
        print('Could not create comment "%s"' % body)
        print('Response:', r.content)

make_github_comment('Why is this called ant license?', 'f57c0e77b8d1a3dfdc31e1d5641059d63a7d7f79', 'ant_license.txt', 0)
