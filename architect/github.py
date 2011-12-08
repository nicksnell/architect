"""Management commands for dealing with github"""

import os.path

from fabric.api import *
from fabric.colors import green
from fabric.decorators import task

#import github

@task
def add_deploy_key(key):
	"""Add a deployment key to the repository"""
	
	require('github_user', provided_by=('development', 'staging', 'production'))
	require('github_api_key', provided_by=('development', 'staging', 'production'))
	require('github_repo_name', provided_by=('development', 'staging', 'production'))
	
	#client = github.GitHub(env.github_user, env.github_api_key)
	