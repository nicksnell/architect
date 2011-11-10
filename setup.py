#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Architect - Web application builder

from setuptools import setup, find_packages

from architect import __version__

long_description = """Architect - Web application builder"""

setup(
	name='Architect',
	version=__version__,
	description='Architect',
	long_description=long_description,
	author='Nick Snell',
	author_email='nick@orpo.co.uk',
	url='http://orpo.co.uk/',
	download_url='http://code.orpo.co.uk/',
	license='Private',
	platforms=['Linux',],
	classifiers=[
		'Environment :: Web Environment',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
	],
	zip_safe=True,
	packages=find_packages(exclude=['tests',]),
	dependency_links = [
	
	],
	entry_points = {
		'console_scripts': [
			
		]
	},
	install_requires=[
		'Fabric>=1.3'
	],
	extras_require={}
)
