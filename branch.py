#!/usr/bin/python3
# Author: Dr. Christopher C. Hall, aka DrPlantabyte
# Copyright 2021 Christopher C. Hall
# Permission granted to use and redistribute this code in accordance with the Creative Commons (CC BY 4.0) License:
# https://creativecommons.org/licenses/by/4.0/
from subprocess import call, Popen, PIPE, STDOUT
import os, sys, re
from os import path

def main():
	# first, check if there are uncommitted changes and abort if so
	changes = run('git', 'status', '-uall', '--porcelain', capture_stdout=True, fail_msg='Cannot branch, current working directory is not in a git repository!')
	## with --porcelain, changes will be an empty string if there are no uncommitted changes
	if len(changes.strip()) > 0:
		## uncommitted changes detected, abort
		print('Error: uncommitted changes detected! Commit first and then branch.')
		exit(1)
	# then ask for a branch and commit to branch from
	this_branch = run('git', 'symbolic-ref', '--short', '-q', 'HEAD',
					  capture_stdout=True).strip()
	branch_list = [x for x in run('git', 'for-each-ref', '--format', '%(refname:short)', 'refs/heads/',
								  capture_stdout=True).replace('\r', '').split('\n') if len(x) > 0]  # necessary because git prints an extra new-line!
	options = ['current branch (%s)' % this_branch] + branch_list
	index, history_branch = choose_from('Which branch do you want to branch from?', options)
	if index == 0:
		history_branch = this_branch

	## get entire history
	commits = [ln for ln in # note: , '--no-pager' MUST come between 'git' and the git command name (because git is git)
					run('git', '--no-pager', 'log', history_branch, '--date=short', '--pretty=%H  %ad  %an  %s', capture_stdout=True)
					.replace('\r', '').split('\n') if len(ln.strip()) > 0]
	## first 40 digits are the long hash (first 7 are the short hash)
	## show the user a few commits at a time
	entry_count = 10
	log_start = 0
	while True:
		log_end = log_start + entry_count
		options=[]
		if log_start != 0:
			options.append('<<< PREVIOUS <<<')
		else:
			options.append('HEAD')
		for ln in commits[log_start:min(log_end,len(commits))]: options.append(ln[0:7]+ln[40:])
		if log_end < len(commits):
			options.append('>>> NEXT >>>')
		index, choice = choose_from('Choose a commit to branch from:', options)
		if choice == '>>> NEXT >>>':
			if log_end < len(commits):
				log_start = log_end
		elif choice == '<<< PREVIOUS <<<':
			log_start -= entry_count
		elif choice == 'HEAD':
			commit_index = 0
			break
		else:
			commit_index = index + log_start-1
			break
	full_hash = commits[commit_index][0:40]
	print('Branching from commit %s' % full_hash)
	print('%s' % commits[commit_index][40:])

	# then ask for a new branch name (or automatically make one)
	bname = ask_for_text('New branch name? (leave blank to auto-name)').strip()
	if len(bname) == 0:
		## generate a unique branch name
		remote_branches = [x for x in
										 run('git', 'for-each-ref', '--format', '%(refname:short)', 'refs/remotes/',
											 capture_stdout=True).replace('\r', '').split('\n') if len(x) > 0]
		all_branches = [x[x.find('/')+1:] for x in branch_list + remote_branches]
		ref_branch = history_branch
		if '.' in ref_branch: ref_branch = ref_branch[:ref_branch.rfind('.')]
		i = 1
		while (bname := '%s.%s' % (ref_branch, i)) in all_branches:
			i += 1

	# finally, make the new branch
	if confirm('Create new branch %s from commit %s?' % (bname, full_hash[0:7])):
		run('git', 'checkout', '-b', bname, full_hash)
		print('Branch %s successfully created!' % bname)
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
