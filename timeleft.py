#!/usr/bin/python3

import sys
import time
import requests

# URL='https://api.github.com/repos/{user}/{repo}'
URL='https://api.github.com/users/{user}?client_id={clientid}&client_secret={clientsecret}'

class SomethingWrong(requests.RequestException):
    pass

def fixurl(user):
    from config import TOKEN, CLIENTID, CLIENTSECRET
    return URL.format(user=user, clientid=CLIENTID, clientsecret=CLIENTSECRET)


def getxratelimits(user):
    """
    """
    
    session = requests.Session()
    r = session.get( fixurl(user) )

    if not r.ok or r.status_code != requests.codes.ok:
        raise SomethingWrong(r.reason, r)

    X = {
        "X-RateLimit-Reset":     None,
        "X-RateLimit-Remaining": None,
        "X-RateLimit-Limit":     None,
        }

    try:
        for key in X.keys():
            X[key] = r.headers.get(key, None)
            X[key] = int(X[key])
    except TypeError:
        raise AttributeError("Could not find '{}' in HTTP header.".format(key), r)
    finally:
        r.close()

    reset="X-RateLimit-Reset"
    X[reset] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(X[reset]))
    return X


if __name__ == "__main__":
    user="tomschr"

    try:
        result = getxratelimits(user)
        for key in result:
            print("{} = {}".format(key, result[key]))

    except (SomethingWrong, AttributeError) as err:
        print(err.args[0], file=sys.stderr)
        err.args[1].close()
    except ImportError as err:
        print("Missing config.py not found\n  {}".format(err), file=sys.stderr)

# EOF