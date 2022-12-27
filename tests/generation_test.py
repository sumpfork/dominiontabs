from __future__ import print_function

import pytest

from domdiv import main


def get_clean_opts(opts):
    options = main.parse_opts(opts)
    options = main.clean_opts(options)
    return options


def test_standard_opts():
    # should be the default
    options = get_clean_opts([])
    main.generate(options)


@pytest.mark.parametrize("lang", main.get_languages("card_db"))
def test_grouped(lang):
    print("checking " + lang)
    options = get_clean_opts(["--special-card-groups", "--language={}".format(lang)])
    main.generate(options)
