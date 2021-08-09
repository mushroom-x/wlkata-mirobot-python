#!/usr/bin/env python3

import setuptools


setuptools.setup(name='mirobot-py',
                 version='v2.0.0-beta',
                 description="A Python interface library for WKlata's Mirobot",
                 author='Sourabh Cheedella',
                 author_email='cheedella.sourabh@gmail.com',
                 long_description=open("README.md", "r").read(),
                 long_description_content_type='text/markdown',
                 url="https://github.com/rirze/mirobot-py",
                 packages=['mirobot'],
                 classifiers="""
                 Development Status :: 4 - Beta
                 Programming Language :: Python :: 3 :: Only
                 Programming Language :: Python :: 3.6
                 Programming Language :: Python :: 3.7
                 Programming Language :: Python :: 3.8
                 License :: OSI Approved :: MIT License
                 Operating System :: OS Independent
                 Operating System :: Microsoft :: Windows
                 Operating System :: POSIX
                 Operating System :: Unix
                 Operating System :: MacOS
                 Topic :: Scientific/Engineering
                 Topic :: Education
                 Topic :: Documentation
                 Topic :: Home Automation
                 Topic :: Scientific/Engineering :: Artificial Intelligence
                 Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)
                 Topic :: Scientific/Engineering :: Image Recognition
                 Topic :: Software Development :: Embedded Systems
                 Topic :: Software Development :: Version Control :: Git
                 Topic :: Terminals :: Serial
                 Intended Audience :: Education
                 Intended Audience :: Science/Research
                 Intended Audience :: Manufacturing
                 Intended Audience :: Developers
                 """.splitlines(),
                 python_requires='>=3.6',
                 install_requires=open('requirements.txt', 'r').read().splitlines(),
                 package_dir={'mirobot': 'mirobot'},
                 package_data={'mirobot': ['resources/*']}
)
