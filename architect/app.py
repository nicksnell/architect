"""Tools for managing web apps"""

import os.path

from fabric.api import *
from fabric.colors import red, blue, green, yellow
from fabric.contrib.console import confirm
from fabric.decorators import task

from architect.nginx import restart as restart_nginx
from architect.utils import _get_venv_bin

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
		virtual_env_build_dest = env.home

		# Where are we creating the virtual environment
		if hasattr(env, 'venv'):
			virtual_env_build_dest = env.venv

		sudo('virtualenv %s %s' % (virtual_env_args, virtual_env_build_dest), user=env.project_user)

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
	print green('Setup complete.')

@task
def bootstrap(repo_pull_protocol='ssh'):
	"""bootstrap the project"""

	require('home', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('development', 'staging', 'production'))
	require('project_repo', provided_by=('development', 'staging', 'production'))
	require('project_url', provided_by=('development', 'staging', 'production'))
	require('project_user', provided_by=('development', 'staging', 'production'))

	virtual_env_bin = _get_venv_bin(env)
	pip = os.path.join(virtual_env_bin, 'pip')

	with cd(env.home):
		# Pull the repo

		# Default to HG if a protocol isn't specified, otherwise try to match protocol
		if env.project_repo.startswith('hg://') or env.project_repo.startswith('ssh://'):
			real_repo_path = env.project_repo.replace('hg://', '%s://' % repo_pull_protocol)
			sudo('hg clone %s %s' % (real_repo_path, env.project_name), user=env.project_user)

		elif env.project_repo.startswith('git://'):
			real_repo_path = env.project_repo.replace('git://', '')
			sudo('git clone %s %s' % (real_repo_path, env.project_name), user=env.project_user)

		else:
			print red('Unknown repository protocol!')
			return

		pip_cmd = None

		# Check if we need to install any modules
		if os.path.exists('etc/pip.conf'):
			# Setup the pip build command
			pip_cmd = '%s install -q -r %s --log=%s' % (
				pip,
				os.path.join(env.home, env.project_name, 'etc/pip.conf'),
				os.path.join(env.home, 'logs', 'pip.log')
			)

		if os.path.exists('requirements.txt'):
			pip_cmd = '%s install -q -r %s --log=%s' % (
				pip,
				os.path.join(env.home, env.project_name, 'requirements.txt'),
				os.path.join(env.home, 'logs', 'pip.log')
			)

		if pip_cmd is not None:
			# Install the required modules
			sudo(pip_cmd, user=env.project_user)

		else:
			print yellow('No pip installation!')

		if os.path.exists('etc/nginx.conf'):
			# Link the configs
			sudo('ln -s %s /etc/nginx/sites-enabled/%s' % (
				os.path.join(env.home, env.project_name, 'etc/nginx.conf'),
				env.project_url
			))
		else:
			# Link the configs
			sudo('ln -s %s /etc/nginx/sites-enabled/%s' % (
				os.path.join(env.home, env.project_name, 'etc/nginx.%s.conf' % env.environment),
				env.project_url
			))

		if os.path.exists('etc/upstart.conf'):
			sudo('cp %s /etc/init/%s.conf' % (
				os.path.join(env.home, env.project_name, 'etc/upstart.conf'),
				env.project_name
			))
		else:
			if os.path.exists('etc/upstart.%s.conf' % env.environment):
				sudo('cp %s /etc/init/%s.conf' % (
					os.path.join(env.home, env.project_name, 'etc/upstart.%s.conf' % env.environment),
					env.project_name
				))
			else:
				print yellow('No Upstart file added!')

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

	print green('Test ran.')

@task(default=True)
def deploy(branch='master'):
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
			sudo('git pull origin %s' % branch, user=env.project_user)

	else:
		print red('Unknown repository protocol!')
		return

	print green('Application Deployed.')

@task
def redeploy(repo_pull_protocol='ssh'):
	"""deploy the application"""

	require('host', provided_by=('development', 'staging', 'production'))
	require('home', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('development','staging', 'production'))
	require('project_user', provided_by=('development','staging', 'production'))

	if not confirm(red('Remove application "%s"?' % os.path.join(env.home, env.project_name))):
		print red('Aborted.')
		return

	# Remove the app
	sudo('rm -rf %s' % os.path.join(env.home, env.project_name))

	# Re pull the repo
	with cd(env.home):
		# Default to HG if a protocol isn't specified, otherwise try to match protocol
		if env.project_repo.startswith('hg://') or env.project_repo.startswith('ssh://'):
			real_repo_path = env.project_repo.replace('hg://', '%s://' % repo_pull_protocol)
			sudo('hg clone %s %s' % (real_repo_path, env.project_name), user=env.project_user)

		elif env.project_repo.startswith('git://'):
			real_repo_path = env.project_repo.replace('git://', '')
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
	require('project_name', provided_by=('develpment', 'staging', 'production'))

	virtual_env_bin = _get_venv_bin(env)
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
def install_crontab():
	"""install a crontab"""

	require('host', provided_by=('staging', 'production'))
	require('home', provided_by=('staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))
	require('project_user', provided_by=('development', 'staging', 'production'))

	# Check we have a cron file
	if not os.path.exists('etc/cron.txt'):
		print red('No crontab found! - looking for etc/cron.txt')
		return

	with cd(env.home):
		# Install the cron file
		sudo('crontab -u %s %s' % (
			env.project_user,
			os.path.join(env.home, env.project_name, 'etc/cron.txt')
		))

	print green('Crontab installed.')

@task
def upstart_link():
	"""load upstart script"""

	require('host', provided_by=('development', 'staging', 'production'))
	require('home', provided_by=('develpment', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))

	if os.path.exists('etc/upstart.conf'):
		sudo('cp %s /etc/init/%s.conf' % (
			os.path.join(env.home, env.project_name, 'etc/upstart.conf'),
			env.project_name
		))
	else:
		require('environment', provided_by=('develpment', 'staging', 'production'))

		sudo('cp %s /etc/init/%s.conf' % (
			os.path.join(env.home, env.project_name, 'etc/upstart.%s.conf' % env.environment),
			env.project_name
		))

	print green('Upstart conf linked.')

@task
def upstart_unlink():
	"""unload upstart script"""

	require('host', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))

	sudo('rm /etc/init/%s.conf' % env.project_name)

	print green('Upstart conf unlinked.')

@task
def nginx_link():
	"""load upstart script"""

	require('host', provided_by=('development', 'staging', 'production'))
	require('home', provided_by=('develpment', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))

	if os.path.exists('etc/nginx.conf'):
		# Link the configs
		sudo('ln -s %s /etc/nginx/sites-enabled/%s' % (
			os.path.join(env.home, env.project_name, 'etc/nginx.conf'),
			env.project_url
		))
	else:
		require('environment', provided_by=('develpment', 'staging', 'production'))

		# Link the configs
		sudo('ln -s %s /etc/nginx/sites-enabled/%s' % (
			os.path.join(env.home, env.project_name, 'etc/nginx.%s.conf' % env.environment),
			env.project_url
		))

	print green('Nginx conf linked.')

@task
def nginx_unlink():
	"""unload upstart script"""

	require('host', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))

	sudo('rm /etc/nginx/sites-enabled/%s' % env.project_url)

	print green('Nginx conf unlinked.')

@task
def start():
	"""start the uwsgi application"""

	require('host', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))

	sudo('start %s' % env.project_name)

	print green('Project started.')

@task
def restart():
	"""restart the uwsgi application"""

	require('host', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))

	sudo('restart %s' % env.project_name)

	print green('Project restarted.')

@task
def stop():
	"""stop the uwsgi application"""

	require('host', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))

	sudo('stop %s' % env.project_name)

	print yellow('Project stopped.')

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

@task
def get_ssh_key():
	"""get the apps ssh key"""

	require('host', provided_by=('development', 'staging', 'production'))
	require('home', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('develpment', 'staging', 'production'))

	with hide('stdout'):
		public_key = sudo('cat %s' % os.path.join(env.home, '.ssh', 'id_rsa.pub'))

	print blue(public_key)
