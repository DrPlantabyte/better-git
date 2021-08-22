#!/usr/bin/python3
# Author: Dr. Christopher C. Hall, aka DrPlantabyte
# Copyright 2021 Christopher C. Hall
# Permission granted to use and redistribute this code in accordance with the Creative Commons (CC BY 4.0) License:
# https://creativecommons.org/licenses/by/4.0/
from subprocess import call, Popen, PIPE, STDOUT
import os, sys, re
from os import path

def main():
	# Check for uncommited changes, aborting if there are any
	changes = run('git', 'status', '-uall', '--porcelain', capture_stdout=True,
				  fail_msg='Cannot push, current working directory is not in a git repository!')
	remote_name = run('git', 'remote', capture_stdout=True, fail_msg='Failed to determine remote name of repository. Please set remote origin name and try again').strip()
	## with --porcelain, changes will be an empty string if there are no uncommitted changes
	if len(changes.strip()) > 0:
		## uncommitted changes detected, abort
		print('Error: uncommitted changes detected! Commit first and then push.')
		exit(1)
	# Fetch list remote branches
	run('git', 'fetch', '--all')
	remote_branches = [x for x in run('git', 'for-each-ref', '--format', '%(refname:short)', 'refs/remotes/',
		capture_stdout=True).replace('\r','').split('\n') if len(x) > 0]
	## get local branch info too
	this_branch = run('git', 'symbolic-ref', '--short', '-q', 'HEAD',
					  capture_stdout=True).strip()
	local_branches = [x for x in run('git', 'for-each-ref', '--format', '%(refname:short)', 'refs/heads/',
								  capture_stdout=True).replace('\r', '').split('\n') if len(x) > 0]
	# Ask user which branch to push to
	print('Currrently on branch: %s' % this_branch)
	_, push_branch = choose_from('Choose branch to push to:', ['(new branch)']+remote_branches)
	# special case: make new upstream branch instead of pushing to existing branch
	if push_branch == '(new branch)':
		push_branch = ask_for_text('New branch name')
		if confirm('Push from local branch %s to new remote branch %s?' % (this_branch, push_branch)):
			run('git', 'push', '--set-upstream', remote_name, '%s:%s' % (this_branch,push_branch))
			print('Done!')
			exit(0)
	# get user confirmation
	if not confirm('Push from local branch %s to remote branch %s?' % (this_branch, push_branch)):
		print('Push canceled.')
		exit(0)
	if (squash_merge := confirm('Squash push into single commit?')):
		commit_msg_lines = []
		print('Enter squashed commit message: (hit enter twice to finish message)')
		while len((msg_line := ask_for_text('', end='>>>   ')).strip()) > 0:
			## clever way to support multi-line messages
			commit_msg_lines.append(msg_line)
		commit_msg = '\n'.join(commit_msg_lines)
		if len(commit_msg.strip()) == 0:
			print('Empty messages are not allowed!')
			exit(1)
	else:
		commit_msg = 'Merge from %s to %s' % (this_branch, push_branch)
	# If pushing to a different branch than the current branch:
	push_branch_local_name = push_branch
	if '/' in push_branch_local_name: push_branch_local_name = push_branch_local_name[push_branch_local_name.rfind('/')+1:]
	if this_branch != push_branch_local_name:
		## different branches
		# Checkout push-to branch
		run('git', 'switch', push_branch_local_name)
		# Pull push-to branch
		run('git', 'pull', remote_name, push_branch_local_name)
		# Merge current branch into push-to branch
		if squash_merge:
			run('git', 'merge', '--squash', this_branch, '-m', commit_msg)
		else:
			if not test_run('git', 'merge', this_branch, '-m', commit_msg, hide_output=False):
				print('Error: unable to cleanly merge branches')
				run('git', 'merge', '--abort')
				run('git', 'clean', '-f')
				run('git', 'switch', this_branch)
				print('Please merge from %s into %s and resolve conflicts, then try again.' % (push_branch, this_branch))
				exit(1)
	else:
		# Pull push-to branch
		run('git', 'pull', remote_name, push_branch_local_name)
	# Try to push
	run('git', 'push', remote_name, push_branch_local_name)
	# If push-to branch is different from this branch, ask user if they want to delete the current branch
	if this_branch != push_branch_local_name:
		if confirm('Delete branch %s?' % this_branch):
			# If yes, delete current branch
			run('git', 'branch', '-D', this_branch)
		else:
			# If no, ask use if they want to add/update current branch to upstream
			run('git', 'switch', this_branch)
			if this_branch in remote_branches \
					or this_branch in [x[x.rfind('/')+1:] for x in remote_branches if '/' in x]:
				## corresponding remote branch exists
				if confirm('Push this branch as well?'):
					run('git', 'push', remote_name, this_branch)
			else:
				## branch not in upstream
				if confirm('Add this branch to remote repository?'):
					# If yes, add or push current branch to remote respository
					run('git', 'push', '--set-upstream', remote_name, this_branch)
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
def test_run(command, *args, hide_output=True):
	args = list(args)
	if hide_output:
		p = Popen([command] + args, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
		exit_code = p.wait()
	else:
		exit_code = call([command] + args)
	return exit_code == 0
#
if __name__ == '__main__':
	main()
