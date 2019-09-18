from setuptools import setup, find_packages

from smart_insurance import __version__

setup(
    name='smart_insurance',
    version=__version__,
    packages=find_packages(),
    url='',
    license='',
    author='pushpak',
    author_email='mahesh.jadhav@capgemini.com',
    description='Smart Insurance using Zappa',
    classifiers=[
        'Environment :: Rest API Environment',
        'Framework :: Flask',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires=['flask', 'intervaltree'],
    extras_require={'dev': ['pytest', 'pytest-cov', 'tox', 'zappa']}
)
