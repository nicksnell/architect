"""Tools for managing projects"""

import os.path

from fabric.api import *
from fabric.colors import red, blue, green
from fabric.contrib.console import confirm
from fabric.decorators import task

from architect.nginx import restart as restart_nginx

@task(default=True)
def deploy():
	"""deploy the application"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	require('home', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('development','staging', 'production'))
	require('project_user', provided_by=('development','staging', 'production'))
	require('project_repo', provided_by=('development', 'staging', 'production'))
	
	# Deploy the application
	if env.project_repo.startswith('hg://') or env.project_repo.startswith('ssh://'):
		with cd(os.path.join(env.home, env.project_name)):
			sudo('hg pull -u', user=env.project_user)
			
	elif env.project_repo.startswith('git://'):
		with cd(os.path.join(env.home, env.project_name)):
			sudo('git pull origin master', user=env.project_user)
		
	else:
		print red('Unknown repository protocol!')
		return
	
	print green('Application Deployed.')

@task
def redeploy():
	"""deploy the application"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	require('home', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('development','staging', 'production'))
	require('project_user', provided_by=('development','staging', 'production'))
	
	# Remove the app
	sudo('rm -rf %s' % os.path.join(env.home, env.project_name))
	
	# Re pull the repo
	with cd(env.home):
		# Default to HG if a protocol isn't specified, otherwise try to match protocol
		if env.project_repo.startswith('hg://') or env.project_repo.startswith('ssh://'):
			real_repo_path = env.project_repo.replace('hg://', '%s://' % repo_pull_protocol)
			sudo('hg clone %s %s' % (real_repo_path, env.project_name), user=env.project_user)
			
		elif env.project_repo.startswith('git://'):
			real_repo_path = env.project_repo.replace('hg://', '%s://' % repo_pull_protocol)
			sudo('git clone %s %s' % (real_repo_path, env.project_name), user=env.project_user)
			
		else:
			print red('Unknown repository protocol.')
			return
		
	print green('Application Re-deployed.')

@task
def install_mods():
	"""install needed python modules using pip"""
	
	require('host', provided_by=('staging', 'production'))
	require('home', provided_by=('staging', 'production'))
	
	virtual_env_bin = os.path.join(env.home, 'bin')
	pip = os.path.join(virtual_env_bin, 'pip')
	
	with cd(env.home):
		# Setup the pip build command
		pip_cmd = '%s install -q -r %s --log=%s' % (
			pip, 
			os.path.join(env.home, env.project_name, 'etc/pip.conf'), 
			os.path.join(env.home, 'logs', 'pip.log')
		)
		
		# Install the required modules
		sudo(pip_cmd, user=env.project_user)
	
	print green('Modules installed.')

@task
def upstart_link():
	"""load upstart script"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	require('home', provided_by=('develpment', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))
	
	sudo('cp %s /etc/init/%s.conf' % (
		os.path.join(env.home, env.project_name, 'etc/upstart.conf'), 
		env.project_name
	))
	
@task
def upstart_unlink():
	"""unload upstart script"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))
	
	sudo('rm /etc/init/%s.conf' % env.project_name)

@task
def start():
	"""start the uwsgi application"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))
	
	sudo('start %s' % env.project_name)

@task
def restart():
	"""restart the uwsgi application"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))
	
	sudo('restart %s' % env.project_name)

@task
def stop():
	"""stop the uwsgi application"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))
	
	sudo('stop %s' % env.project_name)

@task
def destroy():
	"""destroy the application"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	require('home', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))
	require('project_user', provided_by=('develpment', 'staging', 'production'))
	require('project_url', provided_by=('develpment', 'staging', 'production'))
	
	if not confirm(red('Remove application "%s"?' % env.home)):
		print red('Aborted.')
		return
		
	# Stop the application
	stop()
	
	# Remove the application
	sudo('rm -rf %s' % env.home)
	
	# Remove the user
	sudo('userdel %s' % env.project_user)
	
	# Remove the nginx script
	sudo('unlink /etc/nginx/sites-enabled/%s' % env.project_url)
	
	# Remove the upstart script
	upstart_unlink()
	
	# Restart NGINX
	restart_nginx()
	
	print red('Application Destroyed.')
