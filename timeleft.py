#!/usr/bin/python3

import sys
import time
import requests

# URL='https://api.github.com/repos/{user}/{repo}'
URL='https://api.github.com/users/{user}'

class SomethingWrong(requests.RequestException):
    pass

def getxratelimitreset(user):
    """
    """
    from config import TOKEN
    header = { 'Authorization': "token {}".format(TOKEN) }
    session = requests.Session()
    r = session.get(URL.format(user=user), headers=header)

    if not r.ok or r.status_code != requests.codes.ok:
        raise SomethingWrong(r.reason, r)

    epoch = r.headers.get("X-RateLimit-Reset", None)
    if not epoch:
        raise AttributeError("Could not find 'X-RateLimit-Reset' in HTTP header.", r)

    r.close()

    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(epoch)))


if __name__ == "__main__":
    user="tomschr"

    try:
        epoch = getxratelimitreset(user)
        print("Next time for '{user}' is {epoch}".format(**locals()))
    except (SomethingWrong, AttributeError) as err:
        print(err.args[0], file=sys.stderr)
        err.args[1].close()

# EOF