#!/usr/bin/env python3
"""Write a small set of INVENTED chats so you can try Chat Library without your own history.

Usage: make_demo.py <demo-data-dir>      (creates <demo-data-dir>/projects/...)
Nothing here comes from a real person or company.
"""
import json, os, sys, uuid, datetime

out = os.path.join(sys.argv[1], 'projects')
now = datetime.datetime.now(datetime.timezone.utc)
CWD = '/Users/demo/it-desk'
PROJECT = '-Users-demo-it-desk'

def iso(days_ago, minutes=0):
    return (now - datetime.timedelta(days=days_ago, minutes=-minutes)).strftime('%Y-%m-%dT%H:%M:%S.000Z')

# (title, days_ago, [(user, assistant), ...], [(task subject, done?), ...], scheduled-task name or None)
SESSIONS = [
 ("VPN drops every few hours on the new firewall", 2,
  [("Our site-to-site VPN drops every few hours since the firewall swap. Can you help?", "Checked the tunnel logs. The idle timer is shorter than the keepalive interval, so the tunnel is torn down and rebuilt."),
   ("Please fix it.", "I raised the keepalive and the tunnel has been stable for 40 minutes. Still to do: watch it overnight and confirm with the branch office tomorrow. Want me to write up the change note?")], [], None),
 ("Retire the old core switch", 3,
  [("We want to retire the old core switch. Where do I start?", "Start by finding every port that is in use at peak times, then move the uplinks, then remove the switch from monitoring.")],
  [("Map every port in use at peak times", True), ("Move the two uplinks to the new switch", False), ("Remove the old switch from monitoring", False)], None),
 ("Printer offline on level 2", 5,
  [("The level 2 printer keeps going offline.", "It had picked up a new address from DHCP. I set a reservation and printed a test page. All done, nothing left to do.")], [], None),
 ("Roll out BitLocker to laptops", 6,
  [("Plan the BitLocker rollout for our laptops.", "The policy is created. Next steps: assign it to the pilot group, then check the recovery keys are being stored in the directory.")], [], None),
 ("Create accounts and licences for new users", 8,
  [("Three new people start Monday. Create their accounts and licences.", "Accounts are ready. Two of the three licences are assigned.")],
  [("Buy three more licences", False), ("Assign the remaining licence", False), ("Send the welcome email", True)], None),
 ("Mailbox full for the finance team", 9,
  [("Four finance mailboxes are full.", "Archiving is switched on for all four mailboxes and the quota warnings have cleared. Everything is working now.")], [], None),
 ("Patch backlog on file servers", 11,
  [("Several file servers are behind on patches.", "I listed the missing updates. Waiting on the maintenance window. You'll need to approve the reboot before I can finish.")], [], None),
 ("Plan the move of the file server to the cloud", 14,
  [("Draft a plan to move the file server to the cloud.", "I drafted two options. Which do you prefer: lift and shift, or rebuild in the cloud?")], [], None),
 ("Write the weekly IT report runbook", 16,
  [("Write a runbook for our weekly IT report.", "The runbook is written and saved. It covers where the numbers come from and who gets the report. Done.")], [], None),
 ("Build a dashboard of open tickets", 18,
  [("Build a dashboard of open tickets by priority.", "The dashboard shows open tickets by age.")],
  [("Add a filter for priority", False), ("Show tickets by owner", True)], None),
 ("Budget for next year's renewals", 20,
  [("Help me budget next year's software renewals.", "I built the list of renewals with dates. Still need the vendor quotes before the totals mean anything.")], [], None),
 ("Weekend recipe ideas", 4,
  [("Give me three easy weekend dinner ideas.", "Here are three: a tray-bake chicken, a lentil curry and a mushroom pasta. Enjoy.")], [], None),
]
# the same survey run on several days: shows how repeats fold into one card
for d in (7, 6, 5):
    SESSIONS.append(("Switch port survey", d, [("Run the port survey snapshot.", "Snapshot saved.")],
                     [("Parse the snapshots and write the summary", False)], None))
# scheduled runs: land in the Automated runs tab
for d in (1, 2, 3, 4):
    SESSIONS.append(("", d, [('<scheduled-task name="daily-backup-check" file="/demo/daily-backup-check/SKILL.md">Check last night\'s backups and report failures only.</scheduled-task>', "All backups completed. Nothing to report.")], [], "daily-backup-check"))

def rec(kind, sid, parent, ts, **kw):
    r = {"parentUuid": parent, "isSidechain": False, "userType": "external", "cwd": CWD, "sessionId": sid,
         "version": "2.1.0", "type": kind, "uuid": str(uuid.uuid4()), "timestamp": ts}
    r.update(kw)
    return r

os.makedirs(os.path.join(out, PROJECT), exist_ok=True)
for title, days, turns, tasks, sched in SESSIONS:
    sid = str(uuid.uuid4()); parent = None; lines = []; t = 0
    if title: lines.append({"type": "custom-title", "customTitle": title, "sessionId": sid})
    for n, (u, a) in enumerate(turns):
        r = rec("user", sid, parent, iso(days, t), message={"role": "user", "content": u}); lines.append(r); parent = r["uuid"]; t += 1
        is_last = n == len(turns) - 1
        content = []
        if is_last:
            for i, (subj, done) in enumerate(tasks, 1):
                content.append({"type": "tool_use", "id": "toolu_%s" % uuid.uuid4().hex[:12], "name": "TaskCreate", "input": {"subject": subj, "description": subj}})
            for i, (subj, done) in enumerate(tasks, 1):
                if done: content.append({"type": "tool_use", "id": "toolu_%s" % uuid.uuid4().hex[:12], "name": "TaskUpdate", "input": {"taskId": str(i), "status": "completed"}})
        content.append({"type": "text", "text": a})
        r = rec("assistant", sid, parent, iso(days, t), requestId="req_%s" % uuid.uuid4().hex[:10],
                message={"id": "msg_%s" % uuid.uuid4().hex[:10], "type": "message", "role": "assistant", "model": "claude-sonnet-5-5",
                         "content": content, "stop_reason": "end_turn", "stop_sequence": None,
                         "usage": {"input_tokens": 300, "output_tokens": 180, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}})
        lines.append(r); parent = r["uuid"]; t += 1
    with open(os.path.join(out, PROJECT, sid + '.jsonl'), 'w') as f:
        f.write('\n'.join(json.dumps(x) for x in lines) + '\n')
print('demo chats written:', len(SESSIONS), '->', out)
