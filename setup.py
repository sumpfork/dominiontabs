from setuptools import setup, find_packages

version = '3.3.2'

setup(
    name="domdiv",
    version=version,
    entry_points={
        'console_scripts': [
            "dominion_dividers = domdiv.main:main"
        ],
    },
    packages=find_packages(exclude=['tests']),
    install_requires=["reportlab>=3.4.0",
                      "Pillow>=4.1.0"],
    include_package_data=True,
    author="Peter Gorniak",
    author_email="sumpfork@mailmight.net",
    description="Divider Generation for the Dominion Card Game",
    url="http://domtabs.sandflea.org",
    download_url='https://github.com/sumpfork/dominiontabs/archive/v{}.tar.gz'.format(version),
    keywords=['boardgame', 'cardgame', 'dividers']
)
