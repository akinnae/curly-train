import json
import requests

# Authentication info

with open('authParams.txt') as f:
    USERNAME, TOKEN = f.read().splitlines()

# The repository to add this issue to

# with open('./input/prParams.txt') as f:
#     REPO_NAME, REPO_OWNER, PR_NUMBER = f.read().splitlines()
#     PR_NUMBER = int(PR_NUMBER, 10)


def make_github_comment(REPO, PR_NUMBER, body=None):
    '''Create a comment on github.com using the given parameters.'''
    # Our url to create comments via POST
    url = 'https://api.github.com/repos/%s/issues/%i/comments' % (REPO, PR_NUMBER)
    # Create an authenticated session to create the comment
    headers = {
        "Authorization": "token %s" % TOKEN,
    }
    # Create our comment
    data = {'body': """__Hi there! This pull request looks like it might be a duplicate of #1, since it has _a similar title_ and _the same issue number.___

Please help us out by clicking one of the options below: 
- This pull request __is a duplicate__, so this comment was [__useful__](http://www.andrew.cmu.edu/user/aesau/dupbot-useful-v1.html).
- This pull request is __not a duplicate__, but this comment was [__useful__](http://www.andrew.cmu.edu/user/aesau/dupbot-useful-v1.html) nevertheless.
- This pull request is __not a duplicate__, so this comment was [__not useful__](http://www.andrew.cmu.edu/user/aesau/dupbot-unuseful-v1.html).
- I do not need this service, so this comment was [__not useful__](http://www.andrew.cmu.edu/user/aesau/dupbot-unuseful-v1.html).
                    """}

    r = requests.post(url, json.dumps(data), headers=headers)
    if r.status_code == 201:
        print('Successfully created comment "%s"' % body)
    else:
        print('Could not create comment "%s"' % body)
        print('Response:', r.content)



# make_github_comment("""__Hi there! This pull request looks like it might be a duplicate of #1, since it has _a similar title_ and _the same issue number.___
#
# Please help us out by clicking one of the options below:
# - This pull request __is a duplicate__, so this comment was [__useful__](http://www.andrew.cmu.edu/user/aesau/dupbot-useful-v1.html).
# - This pull request is __not a duplicate__, but this comment was [__useful__](http://www.andrew.cmu.edu/user/aesau/dupbot-useful-v1.html) nevertheless.
# - This pull request is __not a duplicate__, so this comment was [__not useful__](http://www.andrew.cmu.edu/user/aesau/dupbot-unuseful-v1.html).
# - I do not need this service, so this comment was [__not useful__](http://www.andrew.cmu.edu/user/aesau/dupbot-unuseful-v1.html).
#                     """)
