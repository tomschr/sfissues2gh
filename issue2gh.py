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


def getPrefix(export):
    prefixes = {
        "Bugs": "[Bug]",
        "Feature Request": "[Feature]",
        "Feature Requests": "[Feature]",
        "Patch": "[Patch]",
        "Patches": "[Patch]",
        "Support Requests": "[Support]",
        "Tech Support": "[Support]"
    }
    trackerName = export["tracker_config"]["options"]["mount_label"]
    if trackerName not in prefixes:
        return ""
    return prefixes[trackerName]


def getCollaborators(repo):
    return repo.collaborators()


def getMilestones(repo):
    return repo.milestones()


def getGHuser(sfuser):
    return SF2GHuserdict.get(sfuser)


def getSFuser(ghuser):
    return GH2SFuserdict.get(ghuser)


def getGHUsers(git):
    res = {}
    # Iterate over all GH users:
    for u in SF2GHuserdict.values():
        try:
            r = git.get_user(u)
            res.setdefault(u, r)
        except github.UnknownObjectException:
            log.warn(
                "Couldn't find a matching GitHub user '{}' for {}".format(u, getSFuser(u)))
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
    # parser.add_argument('-d', '--debug',
    # dest="debug",
    # action="store_true",
    # default=False,
    # help="Help debugging")
    parser.add_argument('-N', '--dry-run',
                        dest="dryrun",
                        action="store_true",
                        default=False,
                        help="Do not execute, just print")
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
    #parser.add_argument('-u', '--user',
    #                    dest='github_user')
    parser.add_argument("-T", "--no-id-in-title",
                        action="store_true",
                        dest="no_id_in_title",
                        help="do not append '[sf#12345]' to issue titles")
    # parser.add_argument('-U', '--user-map',
    #    help="A json file mapping SF username to GitHub username",
    #    default={},
    #    type=load_json)

    args = parser.parse_args()

    if args.start_id < 0:
        parser.error("Start ID has to be positive!")

    if args.end_id is not None and args.end_id < args.start_id:
        parser.error("End ID must be greater than start ID!")

    # By default, start_id and end_id contains (1, None), meaning *all* tickets

    r = args.repo.split("/")
    if len(r) != 2:
        parser.error("Expected for repo format GITUSER/REPO")

    # Assign the splitted format into args:
    args.gituser=r[0]
    args.gitrepo=r[1]

    return args


def setLogging(args):
    leveldict = {
        None: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
        # any greater value is falling back to logging.DEBUG
        'fallback': logging.DEBUG
    }
    level = leveldict.get(args.verbose, leveldict["fallback"])

    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    streamhandler = logging.StreamHandler()# Use sys.stderr by default
    streamhandler.setFormatter(formatter)
    streamhandler.setLevel(level)

    log.addHandler(streamhandler)
    log.setLevel(level)

    # Enable also logging for urllib3
    if args.verbose > 3:
        urllib3 = logging.getLogger('requests.packages.urllib3')
        #urllib3.addHandler(file_handler)
        urllib3.addHandler(streamhandler)
        urllib3.setLevel(level)


def load_json(filename):
    if not os.path.exists(filename):
        log.error("The JSON file '{}' does not exists.".format(filename))
        sys.exit(10)
    with open(filename) as stream:
        return json.load(stream)


def sorttickets(tracker):
    return sorted(tracker['tickets'], key=lambda t: t['ticket_num'])


def auth4GH(args):
    #homedir=os.path.expanduser("~")
    #configdir=os.path.join(homedir, ".config", "sfissues2git")
    #CREDENTIALS_FILE=os.path.join(configdir, "token")

    from getpass import getpass

    user = args.gituser
    password = ''

    while not password:
        password = getpass(prompt='GitHub Password for {0}: '.format(user))

    #note = __file__
    #note_url = ''
    scopes = ['repo']


    gh = github3.login(token=TOKEN)
    auth = gh.authorize(user, password,
                        scopes,
                        # note, note_url,
                        client_id=CLIENTID,
                        client_secret=CLIENTSECRET
                        )

    log.info("Authenticated as '{name}' "
             "with id={client_id}, "
             "URL={url}".format(**auth.app)
            )
    log.info("X-RateLimit-Remaining is {}".format(auth.ratelimit_remaining))
    #if not gh.check_authorization(auth.token):
    #    log.error("Check for authorization has failed. "
    #              "Better check/remove '{}' file.".format(CREDENTIALS_FILE)
    #             )
    return gh, auth


def createRepo(gh, args):
    repo = {'name': args.gitrepo}
    #keys = ['name', 'description', 'homepage', 'private', 'has_issues',
    #'has_wiki', 'has_downloads']
    #  repo[key]

    res=''
    while True:
        res = input("Create repo {}? (y|N)".format(args.repo))
        res=res.strip().lower()
        if not res:
            res = 'n'
        if res in ('y', 'yes', 'n', 'no'):
            break

    if res in ('n', 'no'):
        log.error("Don't create repo, aborting.")
        sys.exit(20)

    r = None
    if repo.get('name'):
        r = gh.create_repository(repo.pop('name'), **repo)

    if r:
        log.info("Created {0} successfully.".format(r.name))
        return r
    else:
        log.error("Could not create repo {}".format(args.repo))
        sys.exit(30)


def prepareGithub(args):
    r = args.repo.split("/") if args.repo else DEFAULTREPO.split("/")

    log.info("Using GitHub repo {}".format(args.repo))

    missingcollabs = []
    found = []
    repo = None

    if not args.dryrun:
        g, auth = auth4GH(args)
        # g = github3.login(token=TOKEN)
        repo = g.repository(*r)
        if not repo :
            # create this repo?
            repo = createRepo(g, args)

        log.debug("URL    : {}".format(repo.url))
        log.debug("Git URL: {}".format(repo.git_url))

        # Remove any double entries
        for c in set(userdict.values()):
            if not repo.is_collaborator(c):
                missingcollabs.append(c)
                # add collaborator
                # if dapstest.add_collaborator(username=c):
                #  log.error("Could not add user '{}' as collaborator".format(c))
            else:
                found.append(c)

        if not found:
            log.warning(
                "No collaborator found. Add {} manually.".format(found))

        if not missingcollabs:
            log.warning("Missing collaborators:", ",".join(missingcollabs))

        log.info("Collaborators: Found {} - missing {}".format(len(found),
                                                               len(missingcollabs),
                                                               ))
    return repo, auth, found, missingcollabs


def getMilestoneNumbers(repo):
    milestoneNumbers = {}

    for milestone in repo.milestones():
        milestoneNumbers[milestone.title] = milestone.number

    return milestoneNumbers


def updateIssue(args, repo, tracker, issue, sfTicket, prefix=""):
    #(githubIssue, sfTicket, auth, milestoneNumbers, userdict,
    #     closedStatusNames, appendSFNumber, collaborators, prefix = ""
    closedStatusNames = tracker['closed_status_names']
    milestoneNumbers = getMilestoneNumbers(repo)

    updateData = {
        'title': prefix + ("" if prefix == "" else " ") + issue.title
    }
    # if not args.no_id_in_title:
    #     updateData['title'] += " [sf#{}]".format(sfTicket['ticket_num'])

    milestone = sfTicket['custom_fields'].get('_milestone')
    if milestone in milestoneNumbers:
        updateData['milestone'] = milestoneNumbers[milestone]

    labels = sfTicket["labels"]
    if labels:
        updateData["labels"] = labels

    status = sfTicket['status']
    if status in closedStatusNames:
        updateData['state'] = "closed"

    if not args.dryrun:
        return issue.edit(**updateData)


if __name__ == "__main__":
    args = parser()
    setLogging(args)
    log.debug("Arguments: {}".format(args))

    tracker = load_json(args.jsonfile)
    repo, auth, *collabs = prepareGithub(args)
    prefix = getPrefix(tracker)

    for i, t in enumerate(sorttickets(tracker)):
        no = t['ticket_num']
        # Check, if we need to process only some tickets
        # should be in the range [startid, endid] or [start, oo]
        #
        if no < args.start_id or (args.end_id is not None and no > args.end_id):
            continue

        labels = t['labels']
        assigned_to = t['assigned_to']
        created_date = t['created_date']
        summary = t['summary']
        if not args.no_id_in_title:
            summary += " [sf#{}]".format(no)
        status = t['status']
        reported_by = t['reported_by']
        custom_fields = t['custom_fields']
        milestone = custom_fields.get('_milestone')
        timestamp = re.sub(':\d+(\.\d+)?$', '', created_date)
        description = t['description']
        description = "**Reported by {reported_by} on {timestamp} UTC**\n{description}".format(
            **locals())
        print("""* Ticket #{no}: {summary}
  Created:  {created_date}
  Assigned: {assigned_to}
  Status:   {status}
  Labels:   {labels}
  Milestone: {milestone}
         """.format(**locals()))
        milestoneNumbers = getMilestoneNumbers(repo)

        issuedict = dict(title=summary,
                         body=description,
                         labels=labels,
                         )
        if assigned_to in collabs[0]:
            issuedict.update(assignee=assigned_to)

        if milestone in milestoneNumbers:
            issuedict.update(milestone=milestoneNumbers[milestone])

        if args.dryrun:
            log.debug("dryrun: Will create issue with: {}".format(issuedict))

        if not args.dryrun:
            issue = repo.create_issue(**issuedict)
            result = updateIssue(args, repo, tracker, issue, t, prefix)

        for post in t['discussion_thread']['posts']:
            timestamp = re.sub(':\d+(\.\d+)?$', '', post['timestamp'])
            body = '**'
            if re.match('^- \*\*', post['text']):
                body += 'Updated by '
            else:
                body += 'Commented by '
            body += post['author'] + ' on ' + timestamp + "**\n" + post['text']

            print("  Comment from {} on {}".format(post['author'], timestamp))
            if not args.dryrun:
                issue.create_comment(body=body)
        print()

# EOF
