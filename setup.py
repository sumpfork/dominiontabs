from setuptools import setup

setup(
    name="domdiv",
    entry_points={"console_scripts": ["dominion_dividers = domdiv.main:main"]},
    package_dir={"": "src"},
    packages=["domdiv"],
    use_scm_version=True,
    setup_requires=["setuptools_scm", "pytest-runner"],
    install_requires=["reportlab", "Pillow"],
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
