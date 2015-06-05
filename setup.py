from __init__ import __version__
from distribute_setup import use_setuptools
from setuptools import setup, find_packages

use_setuptools()


setup(
    name="dominiontabs",
    version=__version__,
    scripts=["dominion_tabs.py"],
    packages=find_packages(),
    install_requires=["reportlab>=2.5",
                      "Pillow>=2.1.0",
                      "PyYAML"],
    package_data={
        '': ['*.txt', '*.png']
    },
    author="Sumpfork",
    author_email="sumpfork@mailmight.net",
    description="Tab Divider Generation for the Dominion Card Game"
)

