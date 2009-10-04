# -*- coding: utf-8 -*-
"""
rdreilib
========

Various reusable utilities for Glashammer/WSGI projects.


For more information consult the `README` file or have a
look at the `website <http://code.rdrei.net/rdreilib/>`_.
"""

from setuptools import setup

extra = {}
try:
    import babel
except ImportError:
    pass
else:
    extra['message_extractors'] = {
        'rdreilib': [
            ('**.py', 'python', None),
            ('**/templates/**', 'jinja2', None),
            ('**.js', 'javascript', None)
        ]
    }

setup(
    name='rdreilib',
    version='0.1',
    url='http://code.rdrei.net/rdreilib/',
    license='BSD',
    author='Pascal Hartig',
    author_email='phartig@rdrei.net',
    description='Tools for Glashammer',
    long_description=__doc__,
    packages=['rdreilib', 'rdreilib.beaker', 'rdreilib.eauth',
              'rdreilib.middleware']
    platforms='any',
    install_requires=[
        'Werkzeug>0.5',
        'Glashammer',
    ],
)
