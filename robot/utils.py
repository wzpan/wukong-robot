import os

def check_and_delete(fp):
    if os.path.exists(fp):
        os.remove(fp)
