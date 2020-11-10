from setuptools import setup

setup(
    name="domdiv",
    entry_points={
        "console_scripts": [
            "dominion_dividers = domdiv.main:main",
            "domdiv_update_language = domdiv.tools.update_language:run",
        ]
    },
    package_dir={"": "src"},
    packages=["domdiv"],
    use_scm_version=True,
    setup_requires=["setuptools_scm", "pytest-runner"],
    install_requires=["reportlab", "Pillow", "configargparse"],
    tests_require=["pytest", "six", "pytest-flake8", "pre-commit", "doit"],
    url="http://domtabs.sandflea.org",
    project_urls={
        "Say Thanks!": "https://boardgamegeek.com/thread/926575/web-page-generate-tabbed-dividers",
        "Source": "https://github.com/sumpfork/dominiontabs",
        "Tracker": "https://github.com/sumpfork/dominiontabs/issues",
    },
    include_package_data=True,
    author="Peter Gorniak",
    author_email="sumpfork@mailmight.net",
    description="Divider Generation for the Dominion Card Game",
    keywords=["boardgame", "cardgame", "dividers"],
    long_description="This script and library generate dividers for the Dominion Card Game by Rio Grande Games.\
     See it in action at http://domtabs.sandflea.org.",
)
