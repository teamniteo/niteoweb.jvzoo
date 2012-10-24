# -*- coding: utf-8 -*-
"""Installer for this package."""

from setuptools import find_packages
from setuptools import setup

import os


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = \
    read('README.rst') + \
    read('docs', 'HISTORY.rst') + \
    read('docs', 'LICENSE.rst')

setup(
    name='niteoweb.jvzoo',
    version='0.1',
    description="Integrates JVZoo digital products retailer system with "
                "Plone for paid memberships.",
    long_description=long_description,
    classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
    ],
    keywords='Plone Python JVZoo',
    author='NiteoWeb Ltd.',
    author_email='info@niteoweb.com',
    url='http://www.niteoweb.com',
    license='BSD',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['niteoweb'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'plone.app.registry',
        'plone.api',
    ],
    extras_require={
        # list libs needed for unittesting this project
        'test': [
            'mock',
            'plone.app.testing',
            'Products.PloneTestCase',
            'repoze.sphinx.autointerface',  # this is not really used in tests
            'unittest2',
        ],
        # list libs needed for releasing this project
        'release': [
            'zest.releaser',   # bin/longtest
            'jarn.mkrelease',  # bin/mkrelease
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]

    target = plone
    """,
)
