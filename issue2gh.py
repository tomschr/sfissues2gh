#!/usr/bin/python3

import sys
import time
import random
import logging
import json

# import requests
import github

from config import CLIENTID, CLIENTSECRET, TOKEN, DEFAULTREPO

__version__ = "0.1"
__author__ = "Thomas Schraitle <toms@opensuse.org>"

def migrateTickets():
    pass


def setupGitHubRepo(login="tomschr", reponame="daps-test"):
    github.enable_console_debug_logging()
    git = github.Github(TOKEN)
    repo = git.get_repo('{0}/{1}'.format(login, reponame))
    return (git, repo)

    
def parser():
    import argparse
    usage = """
    """
    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument('input_file', help="JSON export from Sourceforge")
    parser.add_argument('repo', 
        help="Repo name as <owner>/<project>", 
        default=DEFAULTREPO,
        )
    parser.add_argument('-M', '--skip-milestone', 
        dest='skipmilestone',
        action="store_true", default=False,
        help="Skip creation of milestones")
    parser.add_argument('-C', '--skip-issue-creation', 
        dest='skipissuecreation',
        action="store_true", default=False,
        help="Skip the creation of issues, just update them")
    parser.add_argument('-s', '--start', 
        dest='start_id', 
        action='store',
        help='id of first issue to import; useful for aborted runs')
    parser.add_argument('-u', '--user',
        dest='github_user')
    parser.add_argument("-T", "--no-id-in-title", 
        action="store_true",
        dest="no_id_in_title", 
        help="do not append '[sf#12345]' to issue titles")
    #parser.add_argument('-U', '--user-map',
    #    help="A json file mapping SF username to GitHub username",
    #    default={},
    #    type=load_json)
    
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parser()
    git, repo = setupGitHubRepo()
    rt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(git.rate_limiting_resettime))
    print("Reset time:", rt)
    
    