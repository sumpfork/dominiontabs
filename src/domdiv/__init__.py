from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution("domdiv").version
except DistributionNotFound:
    # package is not installed
    pass
