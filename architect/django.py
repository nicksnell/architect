"""Management commands for dealing with django applications"""

import os.path

from fabric.api import *
from fabric.colors import green
from fabric.decorators import task

from architect.utils import _get_venv_bin

@task
def manage(cmd, *args, **kwargs):
	"""run a management command"""

	require('home', provided_by=('development', 'staging', 'production'))
	require('project_name', provided_by=('development', 'staging', 'production'))
	require('project_user', provided_by=('development', 'staging', 'production'))

	virtual_env_bin = _get_venv_bin()
	py = os.path.join(virtual_env_bin, 'python')

	with cd(env.home):
		manage_cmd = '%s %s %s' % (
			py,
			os.path.join(env.home, env.project_name, 'manage.py'),
			cmd
		)

		if args:
			manage_cmd += ' %s' % ' '.join(args)

		if kwargs:
			manage_cmd += ' %s' % ' '.join(['--%s=%s' % (k, v) for k, v in kwargs.items()])

		sudo(manage_cmd, user=env.project_user)

	print green('Manage command ran.')
