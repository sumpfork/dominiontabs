import glob
import os

from domdiv.tools import bgg_release, update_language

DOIT_CONFIG = {"default_tasks": ["build"]}


def glob_no_dirs(spec):
    return [fname for fname in glob.glob(spec) if os.path.isfile(fname)]


def task_compile_requirements():
    return {
        "file_dep": ["pyproject.toml"],
        "actions": [
            "pip-compile -U --no-emit-index-url --resolver=backtracking pyproject.toml",
        ],
        "targets": ["requirements.txt"],
    }


def task_update_languages():
    files = glob.glob("card_db_src/**/*.json") + glob.glob("card_db_src/*.json")
    return {
        "file_dep": files
        + ["src/domdiv/tools/update_language.py", "src/domdiv/tools/common.py"],
        "actions": [lambda: update_language.main("card_db_src", "src/domdiv/card_db")],
        "targets": [
            os.path.join(
                "src",
                "domdiv",
                "card_db",
                os.path.sep.join(fname.split(os.path.sep)[1:]),
            )
            for fname in files
        ],
        "clean": True,
    }


def task_build():
    files = [
        fname
        for fname in glob_no_dirs("src/domdiv/**/*")
        + glob.glob("card_db_src/**/*.json" + "pyproject.toml")
        if os.path.isfile(fname)
    ]
    return {
        "file_dep": files,
        "task_dep": ["update_languages"],
        "actions": ["pip install -e .[dev]", "python -m build"],
    }


def task_make_bgg_release():
    return {"actions": [lambda: bgg_release.make_bgg_release()]}


def task_test():
    files = glob_no_dirs("src/domdiv/**")
    return {"file_dep": files, "actions": ["pip install -e .[dev]", "pytest"]}
