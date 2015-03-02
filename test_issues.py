#!/usr/bin/python3

import os
import sys
import logging
import random
from time import sleep

import github3

from config import CLIENTID, CLIENTSECRET, TOKEN, GITUSER, GITREPO

log = logging.getLogger(__file__)
level = logging.DEBUG
formatter = logging.Formatter('[%(levelname)s] %(message)s')
streamhandler = logging.StreamHandler()# Use sys.stderr by default
streamhandler.setFormatter(formatter)
streamhandler.setLevel(level)

log.addHandler(streamhandler)
log.setLevel(level)

# Enable also logging for urllib3
urllib3 = logging.getLogger('requests.packages.urllib3')
urllib3.addHandler(streamhandler)
urllib3.setLevel(level)


def auth4GH():
    from getpass import getpass

    password = ''
    while not password:
        password = getpass(prompt='GitHub Password for {}: '.format(GITUSER))

    scopes = ['repo']

    gh = github3.login(token=TOKEN)
    auth = gh.authorize(GITUSER, password,
                        scopes,
                        client_id=CLIENTID,
                        client_secret=CLIENTSECRET
                        )

    log.info("Authenticated as '{name}' "
             "with id={client_id}, "
             "URL={url}".format(**auth.app)
            )
    log.info("X-RateLimit-Remaining is {}".format(auth.ratelimit_remaining))

    return gh, auth


if __name__ == "__main__":
    g, auth = auth4GH()
    if not len(sys.argv[1:]):
        print("ERROR: Expect a GitHub repo", file=sys.stderr)

    reponame = sys.argv[1]

    repo = g.repository(GITUSER, reponame)

    if not repo:
        repo = g.create_repository(reponame)
        if repo:
            log.info("Created {0} successfully.".format(reponame))
        else:
            log.error("Could not create repo {}".format(reponame))
            sys.exit(30)

    for t in range(1, 101):
        log.debug("** Trying to create ticket #{}".format(t))
        issuedict = dict(title="Ticket #{}".format(t),
                         body="This is **ticket #1**".format(t),
                         )
        log.debug("  X-RateLimit-Remaining is {}".format(auth.ratelimit_remaining))
        issue = repo.create_issue(**issuedict)

        sleep(2)

        if random.choice([True, False]):
            issue.create_comment(body="Hi, it's a comment to ticket #{}".format(t))
            log.debug("  Comment added")

        sleep(2)

# EOF