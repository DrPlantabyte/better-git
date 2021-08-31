# Better-Git
Better front-end CLI commands for Git. Fork, Commit, Branch, Merge, and Push with a better UI than Git's "porcelain" commands.

## The 5 Common DVCS Operations
The majority of my Git (and other DVCS) usage follows these 5 operations:
1. Create a named local branch (aka "feature branch") from the authoritative central repository
2. Commit changes to your local branch
3. Go back to an earlier commit and continue development from there (in case you committed a mistake)
4. Merge any new changes from the authoritative central repository since *operation 1* above into your local branch
5. Send your local branch back to the authoritative central repository as a commit to the development/main branch

Let's call these operations (1) *Fork*, (2) *Commit*, (3) *Branch*, (4) *Merge*, and (5) *Push*

This project contains Python scripts for each of the above operations, with the goal of making each of these operations easy to use and *hard to screw-up*. That means that they will be **interactive**, asking for confirmation before doing anything you might regret, and **won't require extra CLI arguments**. If you need to do anything not covered by these 5 scripts, then you can still do so using regular Git commands. **Better-Git** is not a replacement for Git, but simply a wrapper to simplify common use cases.

## fork.py
Creates a named local branch from a remote branch

## commit.py
Commits all changes not ignored by your .gitignore file.

## branch.py
Asks you for a commit to branch from, and creates a new branch from that commit (and makes sure you don't accidentally detach your head or shadow a branch name that already exists).

## merge.py
Walks you through the process of merging two branches.

## push.py
Helps you push your current branch to the remote branch of your choice. Also handles creating new remote branches and deleting feature completed branches, if you so desire.

# Why Fix Git?
I learned Git and Mercurial at the same time in 2010. Since then, I've used Git nearly every day, and Mercurial about once per week. And the sad fact is that **I've had to Google a Git command every day, while I've only had to Google a Mercurial command twice in the past 10 years!** *How* can I find Mercurial so much more *intuitive*, and understand it's built-in documentation so much easier, than Git?

The answer is simple: Git's command-line interface (CLI) UI is terrible, and the few GUI tools that exist are not much better. 

[The reasons Git has such a bad UI are many and controversial](https://stevebennett.me/2012/02/24/10-things-i-hate-about-git/), but I'm just going to pick out two particular issues.

## Problem 1: Overloaded Commands
To be fair, Git is not alone in this sin, but it's a problem that some commands (most notably the checkout command) have very different behavior depending on which options they are given. Just look at the all the uses for the `git checkout`. It seems to do just about everything.

## Problem 2: Gap between high-level and low-level concerns
This problem is a little more subtle, but is no less important.

If you take a step back from Git, and just think about the typical DVCS workflow, you can create a short list of tasks that cover at least 90% of your DVCS interaction: 1. Create a feature branch from the authoritative central repository
2. Commit changes
3. Occasionally branch your feature branch for hot-fixes and the like
4. Update your local branch with any *new* changes to the central repository
5. Merge your feature branch back into the authoritative central repository (often suqashed into a single commit on the main branch)

Each of these operations takes 3-5 git commands:
#### 1. Create a local branch from the central repository
```bash
git clone https://github.com/username/project_name
cd project_name
git config credential.helper cache
git config user.name "My Name"
git config user.email "My.Email@somedomain.com"
git checkout -b feature_branch main_branch
```

#### 2. Commit changes to your local branch
```bash
git status -uall
# check the list of files for surprises
git add -A
git commit -m "my commit message"
```

#### 3. Go back to an earlier commit and continue from there
```bash
# Git does not support anonymous branching, so you need 
# to name a new branch every time you do this or there 
# will be "detached head" problems
git checkout -b new_feature_branch old_commit_hash
```

#### 4. Merge new changes from the central repository
```bash
git merge --no-ff main_branch
# now resolve merge conflicts and re-run tests
git add -A
git commit -m "merged with main_branch"
```

#### 5. Send back to the central repository as a commit 
(TODO: change to rebase)
```bash
git checkout main_branch
git pull
# if any new commits were pulled, go back to operation 4
git merge --squash feature_branch
git commit -m "very detailed commit message"
git push origin main_branch
```

That's a lot of Git for just a 5 operations. As you can see, while a Git user's concerns are quite ligh-level (e.g. "Save my changes"), the commands are rather low-level ("show me all files that changed, then stage files in the index, then make a commit"). There's a big gap between the "what" and the "how" of DVCS that, in other contexts, would usually be filled by front-end software. 

So that's what I've created! **A better front-end user interface for Git** that runs all those fancy Git commands for you (and automatically cleans-up the mess when one of those commands fails).

**Enjoy!**
