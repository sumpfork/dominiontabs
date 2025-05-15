import argparse
from copy import deepcopy

from domdiv import config_options


def parse_and_clean_args(opts) -> argparse.Namespace:
    parsed = config_options.parse_opts(opts)
    cleaned = config_options.clean_opts(parsed)
    # TODO: Uncomment and ensure correctness after https://github.com/sumpfork/dominiontabs/pull/565 is merged
    # expected_recleaned_opts = deepcopy(cleaned)
    # cleaned_again = config_options.clean_opts(expected_recleaned_opts)
    # assert cleaned_again == expected_recleaned_opts
    # assert cleaned == expected_recleaned_opts
    return cleaned
