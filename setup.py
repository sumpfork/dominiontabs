from setuptools import setup

version = "3.8.5"

setup(
    name="domdiv",
    version=version,
    entry_points={"console_scripts": ["dominion_dividers = domdiv.main:main"]},
    package_dir={"": "src"},
    packages=["domdiv"],
    install_requires=[
        "reportlab==3.5.26",
        "Pillow<6",
    ],  # pillow 6 is not supported by reportlab
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
