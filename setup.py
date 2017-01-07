from setuptools import setup, find_packages

setup(
    name="domdiv",
    version='3.0.0',
    entry_points={
        'console_scripts': [
            "dominion_dividers = domdiv.main:main"
        ],
    },
    packages=find_packages(exclude=['tests']),
    install_requires=["reportlab>=2.5",
                      "Pillow>=2.1.0"],
    include_package_data=True,
    author="Sumpfork",
    author_email="sumpfork@mailmight.net",
    description="Divider Generation for the Dominion Card Game"
)
