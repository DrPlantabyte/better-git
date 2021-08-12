#!/usr/bin/python3
# Author: Dr. Christopher C. Hall, aka DrPlantabyte
# Copyright 2021 Christopher C. Hall
# Permission granted to use and redistribute this code in accordance with the Creative Commons (CC BY 4.0) License:
# https://creativecommons.org/licenses/by/4.0/
from subprocess import call, Popen, PIPE, STDOUT
import os, sys, re
from os import path

def main():
	# show all changes
	run('git', 'add', '--all', fail_msg='Cannot commit, current working directory is not in a git repository!')
	run('git', 'status', '-uall', '--porcelain')
	# ask user to confirm
	if not confirm('Commit all file changes?'):
		run('git', 'reset')
		exit(1)
	# ask for commit message
	commit_msg_lines = []
	print('Enter commit message: (hit enter twice to finish message)')
	while len((msg_line := ask_for_text('', end='>>>   ')).strip()) > 0:
		## clever way to support multi-line messages
		commit_msg_lines.append(msg_line)
	msg = '\n'.join(commit_msg_lines)
	if len(msg.strip()) == 0:
		print('Empty messages are not allowed!')
		exit(1)
	print()
	print('Changed files:')
	run('git', 'status', '-uall', '--porcelain')
	print()
	print('Commit message:')
	print(msg)
	print()
	if not confirm('Confirm?'):
		run('git', 'reset')
		exit(1)
	# run the commit command
	run('git', 'commit', '-m', msg)
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
