from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='opencore_zinefarm',
      version=version,
      description="",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='',
      author_email='',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        "Werkzeug",
        "Jinja2",
        "SQLAlchemy==0.6.3",
        "libopencore",
        "simplejson",
        "pytz",
        "Babel",
        "lxml",
        "html5lib",
        "PasteScript",
        "WebOb",
        "pysqlite",
        "topp.utils",
        "sqlalchemy-migrate",
      ],
      entry_points="""
      [paste.app_factory]
      main = opencore_zinefarm.paste:app_factory
      """,
      )
