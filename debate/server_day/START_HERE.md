# START HERE: the six hours on the server plan

This branch, `debate/server-plan-20261123`, is the branch of the NEW debate. It was made from the head of the
first debate's branch, so everything is here: the plan, the source, your memory files, every message.

**The order comes from the owner himself:** for six hours the only subject is the plan for the server day.
**Stop: 18:35Z on your stamps.** Participants: Astra, Neon, Fable (Fable is in the debate most of its time;
Opus keeps the PC's loop and brings measurements from the PC).

## 1. Read in this order

1. `debate/msgs/20261123T193346Z_fable_owner_order_six_more_hours_server_plan.md` (the order, what the six
   hours must produce, the order of work).
2. Your own memory file `debate/memory/<your name>.md`.
3. `debate/server_day/DRAFT_from_the_PC.md` (the starting text, to take apart).
4. `debate/msgs/20261123T191718Z_fable_closing.md`, sections 3 and 4 (the frame and the facts from the PC).
5. In `debate/FINAL_PLAN.md`: W5 and A11, A14, A23, A26, N12, N16, N17, and the owner's direction for the
   server day (after A24).

Then, alone and before you read the other seat: your own list "what can go wrong on the day, how it is noticed,
what the script does about it", as `debate/server_day/FAILURES_<your name>.md`.

## 2. Where you write. You need not ask, and you need not tell anyone a branch name

- If you can push to this branch: push here. A plain push, never forced; take the newest head first.
- **If you cannot push here: make your OWN branch from this one. Any name works.** A name that starts with
  `debate/server-plan-20261123-` followed by your name is the easiest to recognise.
- **Fable's PC finds your branch by itself.** At every look (every few minutes while it works, at least every
  30 minutes) it reads the list of ALL branch heads of this repository, compares it with the list it took when
  this branch was made, takes every branch that is new or has moved and that descends from this branch, and
  carries its files under `debate/` over to this branch. Each time it says in a message which branch it took
  and at which commit.
- The branches of the first debate stay in step too: `debate/forge-plan-20261123` is kept identical to this
  branch by Fable, and what lands on `debate/forge-plan-20261123-astra` is carried over as before. So a session
  that is still running from the first debate loses nothing by writing where it wrote before.
- If two of us change the same file at once, Fable's PC stops the carrying for that branch, says so, and the
  later writer puts its change in again on top. Nothing is ever forced or deleted.

## 3. The rules of this branch (unchanged from the first debate, plus two)

- Only files under `debate/`. Never `source/`. A branch that changes anything outside `debate/` is NOT carried
  over, and Fable says so.
- Messages: `debate/msgs/<UTC stamp>Z_<your name>_<subject>.md`. One subject a message, the result first.
- The plan of these six hours is ONE file: `debate/server_day/SETUP_PLAN.md`. Whoever changes it says in a
  message which section and why. A part is settled by ONE joint message of Astra and Neon plus Fable's check
  on the PC. Proof, not preference: a measurement with its raw file, file and line, or a test anyone can run.
- **Scripts:** under `debate/server_day/scripts/`, each with its test and a hash list. Every script is read line
  by line by Astra, by Neon and by Fable; each answers `YES <sha256>` for the exact bytes, or `NOT YET` with the
  line and a case that fails. A changed byte needs three new YES. No script runs on the day without three YES.
- Your memory file is updated about every ten minutes and before your context is nearly full.
- Nothing personal goes on this branch: the repository is public.
