import datetime


VERBOSE = False


def time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def verbose(msg):
    if VERBOSE:
        print(time() + " VERBOSE: %s" % msg)


def log(msg):
    print(time() + " LOG: %s" % msg)


def error(msg):
    print(time() + " ERROR: %s" % msg)
