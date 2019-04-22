from setuptools import setup

version = "3.7.1"

setup(
    name="domdiv",
    version=version,
    entry_points={"console_scripts": ["dominion_dividers = domdiv.main:main"]},
    packages=find_packages(exclude=["tests"]),
    install_requires=["reportlab==3.5.17", "Pillow==5.4.1"],
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "six", "pytest-flake8", "pre-commit"],
    url="http://domtabs.sandflea.org",
    include_package_data=True,
    author="Peter Gorniak",
    author_email="sumpfork@mailmight.net",
    description="Divider Generation for the Dominion Card Game",
    keywords=["boardgame", "cardgame", "dividers"],
    long_description="This script and library generate dividers for the Dominion Card Game by Rio Grande Games.\
     See it in action at http://domtabs.sandflea.org.",
)
