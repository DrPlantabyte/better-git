#!/usr/bin/python3
# Author: Dr. Christopher C. Hall, aka DrPlantabyte
# Copyright 2021 Christopher C. Hall
# Permission granted to use and redistribute this code in accordance with the Creative Commons (CC BY 4.0) License:
# https://creativecommons.org/licenses/by/4.0/
from subprocess import call, Popen, PIPE, STDOUT
import os, sys, re
from os import path

def main():
	# check if in a merge
	if not merge_in_progress():
		# abort if there are uncommited changes
		changes = run('git', 'status', '-uall', '--porcelain', capture_stdout=True,
					  fail_msg='Cannot merge, current working directory is not in a git repository!')
		## store current commit hash for undo capability
		this_branch = run('git', 'symbolic-ref', '--short', '-q', 'HEAD',
						  capture_stdout=True).strip()
		## with --porcelain, changes will be an empty string if there are no uncommitted changes
		if len(changes.strip()) > 0:
			## uncommitted changes detected, abort
			print('Error: uncommitted changes detected! Commit first and then merge.')
			exit(1)
		# ask which branch/commit to merge from and to
		run('git', 'fetch', '--all')
		branch_list = [x for x in run('git', 'for-each-ref', '--format', '%(refname:short)', 'refs/heads/',
									  capture_stdout=True).replace('\r', '').split('\n') if len(x) > 0]
		print('Currently on branch:',this_branch)
		_, m_from = choose_from('Which branch do you want to merge from?', branch_list)
		if len(m_from) == 0: m_from = this_branch
		_, m_to = choose_from('Which branch do you want to merge into?', branch_list)
		if len(m_to) == 0: m_to = this_branch
		if m_from == m_to:
			print('Error: From-branch and into-merge branch must be different')
			exit(1)
		## test that both branches exist
		run('git', 'cat-file', '-e', m_from, fail_msg='Error: target "%s" does not exist' % m_from)
		run('git', 'cat-file', '-e', m_to, fail_msg='Error: target "%s" does not exist' % m_to)
		# test for merge conflicts
		if no_merge_conflicts(m_from, m_to, this_branch):
			print('No merge conflicts detected.')
			# can do simple merge, ask user for confirmation
			if confirm('Merge %s -> %s?' % (m_from, m_to)):
				# do merge
				## need to be in the into-branch and call merge on the from-branch
				run('git', 'switch', m_to)
				run('git', 'merge', m_from)
				print('Done!')
				exit(0)
		else:
			# merge conflicts exist
			print('Merge conflicts detected. You will need to resolve them before you can merge.')
			if not confirm('Start merge operation?'):
				print('Merge canceled.')
				exit(0)
			# start merge and show conflicts
			run('git', 'switch', m_to)
			test_run('git', 'merge', '--no-commit', '--no-ff', m_from) # git merge will return an error code here, even on success
			unresolved_files = list_unresolved()
			print('Files with unresolved merge conflicts:')
			for f in unresolved_files: print('\t', f, sep='')
			# ask user if they would like to use the git merge tool
			if not merge_tool_ui(this_branch):
				print('Edit the files to resolve all conflicts, then re-run this command.')
				# exit
				exit(0)
	else:
		print('Merge operation in progress.')
		# show unresolved files (git diff --name-only --diff-filter=U)
		unresolved_files = list_unresolved()
		if len(unresolved_files) > 0:
			print('The following files are marked as unresolved:')
			for f in unresolved_files: print('\t', f, sep='')
		# ask if user wants to abort the merge
		if confirm('Abort merge?'):
			run('git', 'merge', '--abort')
			run('git', 'clean', '-f')
			print('Merge aborted.')
			exit(0)
		# if there are unresolved files, ask if user wants to run the merge tool
		if len(unresolved_files) > 0: merge_tool_ui()
		# Ask user if all conflicts have been resolved
		if confirm('Have ALL merge conflicts been resolved and all changes tested?') and confirm('Confirm merge?'):
			# If yes, complete merge and clean up (git clean -f)
			merge_msg = ask_for_text('Merge commit message')
			run('git', 'add', '--all')
			run('git', 'commit', '-m', merge_msg)
			run('git', 'clean', '-f')
			print('Done!')
			exit(0)
		else:
			# If no, exit script
			print('Resolve any merge conflicts and re-run this command when you are ready to complete the merge or wish to abort.')
			exit(0)
	# Done
	print('Done!')

def merge_tool_ui(revert_commit=None):
	merge_tool = run('git', 'config', '--get', 'merge.tool', capture_stdout=True).replace('\r', '').replace('\n', '')
	if confirm('Resolve conflicts using %s?' % merge_tool):
		# run mergetool command
		mt_sucess = test_run('git', 'mergetool', hide_output=False)
		## Note: git mergetool will ask 'Was the merge successful [y/n]?' at the end if the merge tool program exits non-zero,
		## and return non-zero if user says 'no' (and mark all files ar resolved if 'yes' and exits with code 0)
		if mt_sucess == False:
			print('Edit the files to resolve all conflicts, then re-run this command.')
			exit(0)
		# ask if merge is done
		if confirm('Ready to complete merge operation?'):
			unresolved_files = list_unresolved()
			if len(unresolved_files) > 0:
				print('The following files are still marked as unresolved:')
				for f in unresolved_files: print('\t', f, sep='')
				if confirm('Mark all files as resolved?'):
					run('git', 'add', '--all')
			if confirm('Have all changes been tested? Confirm merge:'):
				if revert_commit is not None:
					merge_msg = 'merged commit %s into this branch' % revert_commit
				else:
					merge_msg = ask_for_text('Merge commit message')
				run('git', 'add', '--all')
				run('git', 'commit', '-m', merge_msg)
				run('git', 'clean', '-f')
				print('Done!')
				exit(0)
		# if not done, ask if user wants to abort the merge (git merge --abort)
		if confirm('Abort merge?'):
			run('git', 'merge', '--abort')
			run('git', 'clean', '-f')
			if revert_commit is not None: run('git', 'switch', revert_commit)
			print('Merge aborted.')
			exit(0)
	return False

def merge_in_progress():
	## return True if a merge is in progress, False if not
	root_dir = run('git', 'rev-parse', '--show-toplevel', capture_stdout=True)
	if root_dir.endswith('\n'): root_dir = root_dir[:-1]
	if root_dir.endswith('\r'): root_dir = root_dir[:-1]
	merge_head_file = path.join(root_dir, '.git', 'MERGE_HEAD')
	if path.exists(merge_head_file):
		with open(merge_head_file, 'r') as fin:
			return len(fin.read().strip()) > 0
	return False
def no_merge_conflicts(merge_from, merge_to, revert_to):
	# git checkout fails if already on that branch, switch does not
	run('git', 'switch', merge_to, capture_stdout=True)
	can_merge = test_run('git', 'merge', '--no-commit', '--no-ff', merge_from, hide_output=False)
	test_run('git', 'merge', '--abort') ## undo test merge
	run('git', 'switch', revert_to, capture_stdout=True)
	return can_merge
def list_unresolved():
	return [x for x in run('git', 'diff', '--name-only', '--diff-filter=U',
									  capture_stdout=True).replace('\r', '').split('\n') if len(x) > 0]
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
