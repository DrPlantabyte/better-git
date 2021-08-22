#!/usr/bin/python3
# Author: Dr. Christopher C. Hall, aka DrPlantabyte
# Copyright 2021 Christopher C. Hall
# Permission granted to use and redistribute this code in accordance with the Creative Commons (CC BY 4.0) License:
# https://creativecommons.org/licenses/by/4.0/
from subprocess import call, Popen, PIPE, STDOUT
import os, sys, re
from os import path

def main():
	# Check for presense of ".git" folder
	## use dummy git command to check if in git repo
	if not test_run('git', 'status'):
		# not in a git repo, clone it
		# Ask user for remote URL
		remote_url = ask_for_text('Enter remote git repository URL')
		clone_dir = remote_url.replace('\\','/').split('/')[-1]
		if clone_dir.endswith('.git'): clone_dir = clone_dir[:-4]
		if path.isdir(clone_dir):
			print('Failed to clone git repository "%s": directory "%s" already exists' % (remote_url, clone_dir))
			exit(1)
		# Clone from remote URL
		run('git', 'clone', remote_url, clone_dir,
			fail_msg='Failed to clone git repository "%s"' % remote_url, 
			capture_stdout=False)
		# Change directory into the cloned repo folder
		os.chdir(clone_dir)
		# Setup the local git repo (eg ask user for name and email)
		run('git', 'config', 'credential.helper', 'cache')
		username=ask_for_text('Enter your name on this project')
		useremail=''
		while re.match('^\\S+@\\S+\\.\\S+$', useremail) == None:
			useremail=ask_for_text('Enter your email address on this project')
		run('git', 'config', 'user.name', username)
		run('git', 'config', 'user.email', username)
	# Get list of remote branches
	run('git', 'fetch', '--all')
	this_branch = run('git', 'symbolic-ref', '--short', '-q', 'HEAD',
		capture_stdout=True)
	## for local branches, replace 'refs/remotes/' with 'refs/heads/'
	branch_list = [x for x in run('git', 'for-each-ref', '--format', '%(refname:short)', 'refs/remotes/',
		capture_stdout=True).replace('\r','').split('\n') if len(x) > 0] # necessary because git prints an extra new-line!
	# Ask user which branch to fork
	print()
	_, fork_src = choose_from('Which branch would you like to fork from?', branch_list)
	fork_name = ''
	while True:
		fork_name = ask_for_text('Name of new local branch').strip()
		# If local branch already exists, keep asking for a different name
		if len(fork_name) > 0 and fork_name not in branch_list:
			break
		else:
			print('Error: Branch name "%s" is invalid or already exists. Try again.' % fork_name)
	# Run "git checkout -b local_branch remote_branch" command
	run('git', 'checkout', '-b', fork_name, fork_src)
	# Done!
	print('Done!')
#
def ask_for_text(msg, **kwargs):
	print("%s: " % msg, **kwargs)
	return input()
def confirm(msg):
	while True:
		r = input('%s [y/n]: ' % msg).strip().lower()
		if r == 'y' or r == 'yes':
			return True
		elif r == 'n' or r == 'no':
			return False
		else:
			continue
def choose_from(msg, options_list):
	while True:
		try:
			print(msg)
			num = 1
			for opt in options_list:
				print('%s:\t%s' % (num, opt))
				num += 1
			r = input('Enter number: ')
			i = int(r)-1
			return i, options_list[i]
		except ValueError:
			print('Not a number, try again.')
		except IndexError:
			print('Not a valid option, try again.')
def run(command, *args, fail_msg=None, capture_stdout=False):
	args = list(args) # convert tuple to list
	if fail_msg == None:
		fail_msg = "Error: non-zero exit code returned by %s %s" % (command," ".join(args))
	if capture_stdout == False:
		exit_code = call([command]+args)
		ret_val = None
	else:
		p = Popen([command]+args, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
		o, e = p.communicate()
		if e is not None and len(e) > 0: print(e.decode('utf8'), file=sys.stderr)
		ret_val = o.decode('utf8')
		exit_code = p.returncode
	if exit_code != 0:
		print(fail_msg)
		exit(1)
	return ret_val
def test_run(command, *args):
	args = list(args)
	p = Popen([command] + args, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
	exit_code = p.wait()
	return exit_code == 0
#
if __name__ == '__main__':
	main()
