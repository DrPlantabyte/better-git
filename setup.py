import os

import setuptools
setuptools.setup(
	name='better_git',
	version='0.0.1',
	scripts=['./scripts/%s' % f for f in os.listdir('./scripts')],
	author='Christopher C. Hall',
	description='Better CLI UI wrapper for Git commands',
	packages=['lib.better_git'],
	install_requires=[],
	license='CC-BY',
	python_requires='>=3.6'
)
