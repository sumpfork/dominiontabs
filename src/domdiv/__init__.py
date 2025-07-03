from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("domdiv")
except PackageNotFoundError:
    # package is not installed
    pass
