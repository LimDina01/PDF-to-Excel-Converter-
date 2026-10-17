# Operational Rules & Guidelines

## Confirmation Before Sensitive Actions
Always prompt the user and obtain explicit confirmation before executing sensitive or high-impact actions:
- **Git Push & Remote Operations**: Never push to remote (`git push`), force-push, or delete remote branches without asking the user first.
- **Git History & Overwrites**: Never run destructive Git commands (`git reset --hard`, `git clean -f`, stash drops) without confirmation.
- **Massive Changes**: Prompt before large refactors, massive file deletions, or breaking architectural rewrites.
- **Production / Deployment**: Present the planned actions, exact commands, and diffs clearly, and await explicit approval before running them.
