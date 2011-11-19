"""Tools for working with ubuntu"""

from fabric.api import *
from fabric.colors import red, blue, green
from fabric.contrib.console import confirm
from fabric.decorators import task

import yaml

@task
def build():
	"""build os packages for app using apt-get"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	require('home', provided_by=('development', 'staging', 'production'))
	
	packages = []
	
	with cd(os.path.join(env.home, env.project_name)):
		with hide('stdout'):
			packages = sudo('cat etc/build.conf')
		
	if packages:
		try:
			build = yaml.load(packages)
		except Exception:
			print red('Unable to read build config!')
			return
		
		if packages.has_key('install'):
			sudo('apt-get install %s' % ' '.join(packages['install']))
		
	print green('Packages Built.')

@task
def install(mods=[]):
	"""install os packages using apt-get"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	
	if mods:
		sudo('apt-get install %s' % ' '.join(mods))
		
	print green('Packages Installed.')

@task
def update(mods=[]):
	"""upgrade os packages using apt-get"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	
	sudo('apt-get update')
	
	print green('Upgraded.')

@task
def upgrade(mods=[]):
	"""upgrade os packages using apt-get"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	
	sudo('apt-get update')
	sudo('apt-get upgrade')
	
	print green('Upgraded.')
	