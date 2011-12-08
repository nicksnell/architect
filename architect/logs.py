"""Utilities for handling logs"""

from fabric.api import *
from fabric.colors import cyan
from fabric.decorators import task

@task(default=True)
def list():
	"""list the available logs"""
	
	require('home', provided_by=('development', 'staging', 'production'))
	require('project_user', provided_by=('development', 'staging', 'production'))
	
	with cd(env.home):
		with hide('stdout'):
			logs = sudo('ls -la logs', user=env.project_user)
		
	print cyan(logs)

@task
def get(log, size=50):
	"""get the last output of a given log"""
	
	require('home', provided_by=('development', 'staging', 'production'))
	
	with cd(env.home):
		with hide('stdout'):
			log_contents = sudo('tail -n %s logs/%s.log' % (size, log))
		
	print cyan(log_contents)

@task
def clear(log, size=50):
	"""get the last output of a given log"""
	
	require('home', provided_by=('development', 'staging', 'production'))
	
	with cd(env.home):
		sudo('echo '' > logs/%s.log' % log)
	
	print cyan(log_contents)
