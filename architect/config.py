"""Tools for building web environments"""

import os.path

from fabric.api import *
from fabric.colors import red, blue, green
from fabric.contrib.console import confirm
from fabric.decorators import task

@task
def setup():
	"""setup the environment"""
	
	require('host', provided_by=('development', 'staging', 'production'))
	require('home', provided_by=('development', 'staging', 'production'))
	require('project_user', provided_by=('development', 'staging', 'production'))
	require('project_group', provided_by=('development', 'staging', 'production'))
	
	# Setup the environment
	# 1. Build structure
	# 2. Install code
	# 3. Configure
	
	# Create the home directory
	sudo('mkdir -p %s' % env.home)
	
	# Add the user
	sudo('useradd -U -d %s %s' % (env.home, env.project_user))
	
	# Get the user/group id
	with hide('stdout'):
		uid = run('id -u %s' % env.project_user)
		gid = run('id -g %s' % env.project_user)
	
	print blue('User ID is: %s' % uid)
	print blue('Group ID is: %s' % gid)
	
	# Change the owner of the site instance
	sudo('chown -R %s:%s %s' % (env.project_user, env.project_group, env.home))
	
	# Create the virtual environment
	with cd(env.home):
		virtual_env_args = '--clear --distribute'
		sudo('virtualenv %s %s' % (virtual_env_args, env.home), user=env.project_user)
		
	# Create other needed folders
	with cd(env.home):
		sudo('mkdir -p data logs tmp static .ssh', user=env.project_user)
		
	# Create a SSH key for site
	sudo('ssh-keygen -q -t rsa -f %s -N ""' % os.path.join(
		env.home, '.ssh', 'id_rsa'
	), user=env.project_user)
	
	# Get the public key
	with hide('stdout'):
		public_key = sudo('cat %s' % os.path.join(env.home, '.ssh', 'id_rsa.pub'))
	
	print blue(public_key)

@task
def bootstrap(repo_pull_protocol='ssh'):
	"""bootstrap the project"""
	
	require('home', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('development', 'staging', 'production'))
	require('project_repo', provided_by=('development', 'staging', 'production'))
	require('project_url', provided_by=('development', 'staging', 'production'))
	require('project_user', provided_by=('development', 'staging', 'production'))
	
	# Build the paths to some necessary binaries
	virtual_env_bin = os.path.join(env.home, 'bin')
	pip = os.path.join(virtual_env_bin, 'pip')
	
	with cd(env.home):
		# Pull the repo
		
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
		
		# Setup the pip build command
		pip_cmd = '%s install -q -r %s --log=%s' % (
			pip, 
			os.path.join(env.home, env.project_name, 'etc/pip.conf'), 
			os.path.join(env.home, 'logs', 'pip.log')
		)
		
		# Install the required modules
		sudo(pip_cmd, user=env.project_user)
		
		# Link the configs
		sudo('ln -s %s /etc/nginx/sites-enabled/%s' % (
			os.path.join(env.home, env.project_name, 'etc/nginx.conf'), 
			env.project_url
		))
		
		sudo('cp %s /etc/init/%s.conf' % (
			os.path.join(env.home, env.project_name, 'etc/upstart.conf'), 
			env.project_name
		))
	
	print green('Environment is setup.')

@task
def remove_app():
	"""clean the site instance - enabels site to be re-bootstrapped"""
	
	require('home', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('development', 'staging', 'production'))
	
	if not confirm(red('Remove application "%s"?' % os.path.join(env.home, env.project_name))):
		print red('Aborted.')
		return
	
	# Remove the application
	sudo('rm -rf %s' % os.path.join(env.home, env.project_name))
	
	print green('App removed.')
	
@task
def test():
	"""run a test command on a host, prints hosts type"""
	run('uname -a')
