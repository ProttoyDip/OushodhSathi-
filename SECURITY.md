# Security policy

OushodhSathi is a research prototype. It is not a medical device and is not intended to store
real patient data in its current form.

## Reporting a vulnerability

Please **do not open a public issue** for a security problem. Use GitHub's
[private vulnerability reporting](https://github.com/ProttoyDip/OushodhSathi-/security/advisories/new)
for this repository, with steps to reproduce and the impact you see. We aim to reply within a
week.

Especially relevant reports:

- any way for the family view to show a finding that a clinician has not confirmed;
- any path that sends patient names or phone numbers to a model provider;
- uploaded photos being stored after extraction;
- reviewer-token bypass on the review endpoints.

## Secrets

- API keys belong only in `backend/.env`, which is git-ignored. `backend/.env.example` lists
  the variable **names** only.
- Never paste keys into issues, pull requests, commits, screenshots or chat logs. If a key is
  exposed anywhere, rotate it with the provider immediately; deleting the text is not enough.
- Before a release, scan the history for key prefixes:

  ```bash
  git log --all -p | grep -nE "sk-[A-Za-z0-9_-]{10,}|pplx-|tvly-[A-Za-z0-9]|xpl_"
  ```
