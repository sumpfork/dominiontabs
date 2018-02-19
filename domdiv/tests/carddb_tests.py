from __future__ import print_function
import subprocess
import shutil
import os
import contextlib

import pytest

from .. import main
from .. import cards as domdiv_cards


@pytest.fixture
def rmtestcardb(request):

    def rmd():
        testcardb_dir = os.path.join(str(request.config.rootdir), 'tools/card_db')
        if os.path.exists(testcardb_dir):
            print('removing {}'.format(testcardb_dir))
            shutil.rmtree(testcardb_dir)
    request.addfinalizer(rmd)


def test_cardread():
    options = main.parse_opts([])
    options.data_path = '.'
    cards = main.read_card_data(options)
    assert len(cards) == 524
    valid_cardsets = {
        u'base',
        u'dominion1stEdition',
        u'dominion2ndEdition',
        u'dominion2ndEditionUpgrade',
        u'intrigue1stEdition',
        u'intrigue2ndEdition',
        u'intrigue2ndEditionUpgrade',
        u'seaside',
        u'alchemy',
        u'prosperity',
        u'cornucopia extras',
        u'cornucopia',
        u'hinterlands',
        u'dark ages',
        u'dark ages extras',
        u'guilds',
        u'adventures',
        u'adventures extras',
        u'empires',
        u'empires extras',
        u'nocturne',
        u'nocturne extras',
        u'promo',
        u'extras',
        u'animals'
    }
    for c in cards:
        assert isinstance(c, domdiv_cards.Card)
        assert c.cardset_tag in valid_cardsets


def test_languages():
    languages = main.get_languages('card_db')
    for lang in languages:
        print('checking ' + lang)
        # for now, just test that they load
        options = main.parse_opts(['--language', lang])
        options.data_path = '.'
        cards = main.read_card_data(options)
        assert cards, '"{}" cards did not read properly'.format(lang)
        cards = main.add_card_text(options, cards, 'en_us')
        cards = main.add_card_text(options, cards, lang)
        if lang == 'it':
            assert "Maledizione" in [card.name for card in cards]
        elif lang == 'de':
            assert "Fluch" in [card.name for card in cards]


@contextlib.contextmanager
def change_cwd(d):
    curdir = os.getcwd()
    try:
        os.chdir(d)
        yield
    finally:
        os.chdir(curdir)


def test_languagetool_run(pytestconfig):
    with change_cwd(str(pytestconfig.rootdir)):
        cmd = 'python tools/update_language.py'
        print(cmd)
        assert subprocess.check_call(cmd.split()) == 0
        cmd = 'diff -rw domdiv/card_db tools/card_db'
        out = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
        print(out)
        assert out == ''
