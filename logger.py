import datetime


VERBOSE = False


class Logger:
    def __init__(self, name):
        self.name = name

    def time(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def verbose(self, msg):
        if VERBOSE:
            print(f"{self.time()} VERBOSE {self.name}: {msg}")

    def info(self, msg):
        print(f"{self.time()} INFO {self.name}: {msg}")

    def error(self, msg):
        print(f"{self.time()} ERROR {self.name}: {msg}")

    def warning(self, msg):
        print(f"{self.time()} WARNING {self.name}: {msg}")
