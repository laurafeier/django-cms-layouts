import os
from setuptools import setup, find_packages


README = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md')


DEPENDENCIES = [
    'django >=1.4, <1.5',
    'django-cms>=2.3.5,<2.3.6',
]


DEPENDENCY_LINKS = []


setup(
    name='django-cms-layouts',
    version='0.1',
    description='Layer over django-cms that allows to create layouts '
                'which can be used to render existing CMS pages with '
                'different content.',
    long_description = open(README, 'r').read(),
    author='Laura Feier',
    author_email='feierlaura10@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=DEPENDENCIES,
    dependency_links=DEPENDENCY_LINKS,
    setup_requires=[],
    classifiers=[]
)
