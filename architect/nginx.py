"""Commands for dealing with server services"""

from fabric.api import *
from fabric.colors import red, blue, green, yellow
from fabric.decorators import task

@task
def start():
	"""start nginx"""
	require('host', provided_by=('development', 'staging', 'production'))
	sudo('/etc/init.d/nginx start')
	print green('Nginx Started.')

@task
def stop():
	"""stop nginx"""
	require('host', provided_by=('development', 'staging', 'production'))
	sudo('/etc/init.d/nginx stop')
	print yellow('Nginx Stopped.')

@task
def restart():
	"""restart nginx"""
	require('host', provided_by=('development', 'staging', 'production'))
	sudo('/etc/init.d/nginx restart')
	print green('Nginx Restarted.')

@task
def reload():
	"""reload nginx"""
	require('host', provided_by=('development', 'staging', 'production'))
	sudo('/etc/init.d/nginx reload')
	print green('Nginx Reload.')

@task
def status():
	"""nginx status"""
	require('host', provided_by=('development', 'staging', 'production'))
	sudo('/etc/init.d/nginx status')
	
@task
def get_sites():
	"""list sites in nginx"""
	require('host', provided_by=('development', 'staging', 'production'))
	
	with hide('stdout'):
		sites = sudo('ls -la /etc/nginx/sites-enabled/', user=env.project_user)
		
	print cyan(sites)

@task
def get_config():
	"""list sites in nginx"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	
	with hide('stdout'):
		config = sudo('cat /etc/nginx/conf/nginx.conf', user=env.project_user)
		
	print cyan(config)
	