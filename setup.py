from __init__ import __version__
from setuptools import setup, find_packages

setup(
    name="dominiontabs",
    version=__version__,
    entry_points={
        'console_scripts': [
            "dominion_dividers = domdiv.main:main"
        ],
    },
    packages=find_packages(exclude=['tests']),
    install_requires=["reportlab>=2.5",
                      "Pillow>=2.1.0"],
    package_data={
        'domdiv': ['images/*.png', 'card_db/*/*.json']
    },
    author="Sumpfork",
    author_email="sumpfork@mailmight.net",
    description="Divider Generation for the Dominion Card Game"
)
