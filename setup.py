#!/usr/bin/env python3

import setuptools

setuptools.setup(name='wlkata-mirobot-python',
                 version='0.1.2',
                 description="WKlata Mirobot Python SDK",
                 author='Shunkai Xing',
                 author_email='xingshunkai@qq.com',
                 long_description=open("README.md", "r", encoding="utf-8").read(),
                 long_description_content_type = 'text/markdown',
                 url="https://github.com/mushroom-x/wlkata-mirobot-python",
                 packages=  ['wlkata_mirobot'],
                 classifiers="""
                 Development Status :: 4 - Beta
                 Programming Language :: Python :: 3 :: Only
                 Programming Language :: Python :: 3.6
                 Programming Language :: Python :: 3.7
                 Programming Language :: Python :: 3.8
                 Programming Language :: Python :: 3.9
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
                 install_requires=[
                     'pyserial', 
                     'bleak'
                 ],
                 package_dir={
                     'wlkata_mirobot': 'wlkata_mirobot'
                 },
                 package_data={
                    'wlkata_mirobot': ['resources/*'], 
                 }
)
