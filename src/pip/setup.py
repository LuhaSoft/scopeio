import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='vxi11',
    version='0.2',
    packages=['vxi11'],
    include_package_data=True,
    license='GNU General Public License',  # example license
    description='A simple library for instrument control.',
    long_description=README,
    url='http://luhasoft.github.io/scopeio/',
    author='Kari Hameenaho',
    author_email='kjh.tre@gmail.com',
    classifiers=[
        'Environment :: Instruments',
        'Framework :: VXI11',
        'Intended Audience :: Labusers',
        'License :: OSI Approved :: GNU General Public License', # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python/C/C++',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 2.7',
        'Topic :: Laboratory :: Instruments',
        'Topic :: Laboratory :: Instruments :: IO',
    ],
)

