import os
from setuptools import setup
from gikala_history import gikala_history

setup(
    name = "digikala_history",
    version = "1.0",
    author = "Jadi Mirmirani",
    author_email = "jadijadi@gmail.com",
    description = "Extract and analyze the history of your purchases on Digikala",
    license = "MIT License",
    url = "https://github.com/jadijadi/digikala_history",
    packages=['digikala_history'],
    entry_points = {
        'console_scripts' : ['digikala_history = digikala_history.digikala_history:main']
    },
    data_files = [
        ('share/applications/', ['digikala_history.desktop'])
    ],
    classifiers=[
        "License :: MIT License",
    ],
)
