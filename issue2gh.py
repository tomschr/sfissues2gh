#!/usr/bin/python3

import sys
import os
import os.path
import time
import random
import logging
import re

# import requests
import json
import github3


from config import CLIENTID, CLIENTSECRET, TOKEN, DEFAULTREPO, \
     SF2GHuserdict, GH2SFuserdict, userdict

__version__ = "0.1"
__author__ = "Thomas Schraitle <toms@opensuse.org>"


log = logging.getLogger(__file__)
formatter = logging.Formatter('[%(levelname)s] %(message)s')
handler = logging.StreamHandler(stream=sys.stderr)
handler.setFormatter(formatter)


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
   pass

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
   parser.add_argument('jsonfile', help="JSON export from Sourceforge")
   parser.add_argument('repo',
      nargs="?",
      help="Repo name as <owner>/<project>",
      default=DEFAULTREPO,
      )
   #parser.add_argument('-d', '--debug',
      #dest="debug",
      #action="store_true",
      #default=False,
      #help="Help debugging")
   parser.add_argument('-v', '--verbose',
      dest="verbose",
      action="count",
      help="Raise verbosity level",
      )
   parser.add_argument('-s', '--start',
      dest='start_id',
      action='store',
      type=int,
      default=1,
      help='id of first issue to import (inclusive); useful for aborted runs')
   parser.add_argument('-e', '--end',
      dest='end_id',
      type=int,
      action='store',
      help='id of end issue to import (inclusive); useful for aborted runs')
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

   if args.start_id < 0:
      parser.error("Start ID has to be positive!")

   if args.end_id is not None and args.end_id < args.start_id:
      parser.error("End ID must be greater than start ID!")

   # By default, start_id and end_id contains (1, None), meaning *all* tickets

   return args

def setLogging(args, examples=True):
   leveldict = {
      None: logging.ERROR,
         1: logging.WARNING,
         2: logging.INFO,
         3: logging.DEBUG,
         # any greater value is falling back to logging.DEBUG
         'fallback': logging.DEBUG
       }

   handler.setLevel(leveldict.get(args.verbose, leveldict["fallback"]))

   log.addHandler(handler)
   log.setLevel(leveldict.get(args.verbose, leveldict["fallback"]))

   if examples:
      log.debug("Debug")
      log.info("Info")
      log.warn("Warning")
      log.error("Error")
      log.critical("OHje!!")


def load_json(filename):
   with open(filename) as stream:
      return json.load(stream)

def sorttickets(tracker):
   return sorted(tracker['tickets'], key=lambda t: t['ticket_num'])

def foo():
   r = args.repo.split("/") if args.repo else DEFAULTREPO.split("/")

   log.info("Using repo {}".format(r))

   g = github3.login(token=TOKEN)
   repo = g.repository(*r)

   log.info("URL    : {}".format(repo.url))
   log.info("Git URL: {}".format(repo.git_url))

   missingcollabs=[]
   found=[]
   # Remove any double entries
   for c in set(userdict.values()):
      if not repo.is_collaborator(c):
         missingcollabs.append(c)
         # add collaborator
         # dapstest.add_collaborator(username=c) -> bool
      else:
         found.append(c)

   if not found:
      log.warning("No collaborator found. Add {}".format(found) )

   if not missingcollabs:
      log.warning("Missing collaborators:", ",".join(missingcollabs))

   log.info("Collaborators: Found {} - missing {}".format( len(found),
                                                           len(missingcollabs),
                                                         ))


if __name__ == "__main__":
   args = parser()
   setLogging(args, False)
   log.debug("Arguments: {}".format(args))

   if not os.path.exists(args.jsonfile):
      log.error("The JSON file '{}' does not exists.".format(args.jsonfile))
      sys.exit(10)

   tracker = load_json(args.jsonfile)

   for i, t in enumerate(sorttickets(tracker)):
      no = t['ticket_num']
      labels = t['labels']
      assigned_to = t['assigned_to']
      created_date = t['created_date']
      summary = t['summary']
      status = t['status']
      description = t['description']
      custom_fields = t['custom_fields']
      print("""* Ticket #{no}: {summary}
  Created:  {created_date}
  Assigned: {assigned_to}
  Status:   {status}
         """.format(**locals()))

# EOF