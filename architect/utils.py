import os.path

def _get_venv_bin():
	# Try to find the virtual environment
	if hasattr(env, 'venv'):
		return os.path.join(env.venv, 'bin')

	# Assume the cwd is a virtualenv
	return os.path.join(env.home, 'bin')