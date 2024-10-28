import atexit
import contextlib
import gzip
import importlib.resources
import os


def iter_resource_dir(path):
    return importlib.resources.files(f"domdiv").joinpath(path).iterdir()


def is_resource_dir(path):
    return importlib.resources.files(f"domdiv").joinpath(path).is_dir()


@contextlib.contextmanager
def get_resource_stream(path):
    ref = importlib.resources.files("domdiv").joinpath(path)
    with ref.open("rb") as f:
        yield gzip.GzipFile(fileobj=f)


def get_resource_filepath(fpath):
    file_manager = contextlib.ExitStack()
    atexit.register(file_manager.close)
    ref = importlib.resources.files("domdiv") / fpath
    path = file_manager.enter_context(importlib.resources.as_file(ref))
    return path


def get_image_filepath(fname):
    return get_resource_filepath(os.path.join("images", fname))


def resource_exists(fpath):
    return importlib.resources.files("domdiv").joinpath(fpath).is_file()
