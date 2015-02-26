#!/usr/bin/python3

import sys
import time
import random
import logging
import re

# import requests
import json
import github

from github.GithubObject import NotSet

from config import CLIENTID, CLIENTSECRET, TOKEN, DEFAULTREPO, \
     SF2GHuserdict, GH2SFuserdict, userdict

__version__ = "0.1"
__author__ = "Thomas Schraitle <toms@opensuse.org>"

log = logging.getLogger(DEFAULTREPO)


def migrateTickets():
    pass

def getCollaborators(git, repo):
    return repo.get_collaborators()
    
    
def getMilestones(git, repo):
    return repo.get_milestones()

    
def setupGitHubRepo(login="tomschr", reponame="daps-test"):
    git = github.Github(TOKEN)
    repo = git.get_repo('{0}/{1}'.format(login, reponame))
    return (git, repo)


def getIssues(git, repo):
    return repo.get_issues()

    
def getGHuser(sfuser):
    return SF2GHuserdict.get(sfuser)
    
def getSFuser(ghuser):
    return GH2SFuserdict.get(ghuser)

def getGHUsers(git):
    res={}
    # Iterate over all GH users:
    for u in SF2GHuserdict.values():
        try:
            r = git.get_user(u)
            res.setdefault(u, r)
        except github.UnknownObjectException:
            log.warn("Couldn't find a matching GitHub user '{}' for {}".format(u, getSFuser(u) ) )
    return res
    
def parser():
    import argparse
    usage = """
    """
    parser = argparse.ArgumentParser(prog=__file__)
    parser.add_argument('input_file', help="JSON export from Sourceforge")
    parser.add_argument('repo', 
        nargs="?",
        help="Repo name as <owner>/<project>", 
        default=DEFAULTREPO,
        )
    parser.add_argument('-d', '--debug',
        dest="debug",
        action="store_true",
        default=False,
        help="Help debugging")
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
    if args.debug:
        github.enable_console_debug_logging()
    git, repo = setupGitHubRepo()
    rt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(git.rate_limiting_resettime))
    print("Github Reset Time:", rt)
    issues = getIssues(git, repo)
    #for i in issues:
    #    print("{i.id}/{i.state} {i.title}".format( **locals() ))
    
    #print("Creating milestone 'foo' now...")
    #res = repo.create_milestone("Foo")
    #print("Result:", res)
    
    print("Creating an issue 'Test Issue' now...")
    milestone = repo.get_milestone(2)
    body="""*Created by tomschr with issue2gh.py*"""
    issue = repo.create_issue(title="Test Issue 9",
        body=body,
        milestone=milestone,
        labels=["Bug"]
        )
    
    #users = getGHUsers(git)
    
    # user = git.get_user("fsundermeyer")
    #user = users.get('fsundermeyer')
    #if user is None:
    #    user = users.get("tomschr")
    
    
    #try:
        #issue.edit(title="Edited Test Issue No.7", 
                #body=body, 
                ##assignee=user, 
                #state="open", 
                ##milestone=milestone, 
                #labels=["Bug"]
                #)
    #except github.GithubException.GithubException as err:
        #print(err)
    #finally:
        #print("Successful!")
    
    print("Successful!")
    