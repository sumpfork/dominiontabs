import glob
import os
import distutils.core

from tools import update_language

DOIT_CONFIG = {"default_tasks": ["build"]}


def glob_no_dirs(spec):
    return [fname for fname in glob.glob(spec) if os.path.isfile(fname)]


def task_update_languages():
    files = glob.glob("card_db_src/**/*.json") + glob.glob("card_db_src/*.json")
    return {
        "file_dep": files,
        "actions": [lambda: update_language.main("card_db_src", "src/domdiv/card_db")],
        "targets": [
            os.path.join("src/domdiv/card_db", "/".join(fname.split("/")[1:]))
            for fname in files
        ],
        "clean": True,
    }


def task_build():
    files = [
        fname
        for fname in glob_no_dirs("src/domdiv/**/*")
        + glob.glob("card_db_src/**/*.json" + "setup.py")
        if os.path.isfile(fname)
    ]
    return {
        "file_dep": files,
        "task_dep": ["update_languages"],
        "actions": [
            lambda: True if distutils.core.run_setup("setup.py", "sdist") else False
        ],
    }


def task_test():
    files = glob_no_dirs("src/domdiv/**")
    return {"file_dep": files, "actions": ["python setup.py test"]}
