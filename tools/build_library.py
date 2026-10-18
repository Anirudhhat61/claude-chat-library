#!/usr/bin/env python3
"""Build projects/library.html: a categorised front door for the claude-code-log archive.

Reads catalog.json (made by catalog.py), tags each session with a Topic and a Type using
categories.json in your archive folder (editable; created on first run), groups repeats, and writes one
self-contained HTML file. No external network resources. Session text is untrusted, so the
page builds every card with textContent, never innerHTML.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get('CHAT_LIBRARY_HOME') or os.path.expanduser('~/Documents/Claude-Chat-Viewer')
PROJ = os.path.join(ROOT, 'projects')
CAT_FILE = os.path.join(ROOT, 'categories.json')   # your own copy; edit freely

DEFAULT = {
    "_help": "Rules run top to bottom, first regex match on title+first message wins. Add words, reorder, or pin a session with overrides: {\"<session id>\": {\"topic\": \"...\", \"type\": \"...\"}}. Then run scripts/refresh.sh.",
    "topics": [
        ["Personal", r"resume|job search|holiday|family|recipe|\btax\b|personal", 220],
        ["Business & Management", r"\bceo\b|budget|invoice|renewal|vendor|contract|brand", 88],
        ["Customers & Projects", r"customer|client|project|\buat\b|handoff", 335],
        ["Printing", r"printer|print queue|printing|printix", 130],
        ["Security & Compliance", r"security|compliance|allowlist|phish|cyber|bitlocker|vulnerab|audit|crowdstrike", 350],
        ["Identity & Access", r"entra|conditional access|\bmfa\b|password|\bsso\b|access list|user access|new user|active directory|licen[cs]e|bitwarden|teamviewer", 275],
        ["Network & Connectivity", r"switch|meraki|\bvpn\b|\bwan\b|ssid|wi-?fi|firewall|\bdns\b|vlan|connectivity|internet|uplink|unifi|\bsfp\b|port usage", 212],
        ["Endpoints & Patching", r"ninja|patch|laptop|\bram\b|memory usage|endpoint|\bgpo\b|device|vuln", 165],
        ["Microsoft 365 & Email", r"exchange|m365|mail|teams|sharepoint|onedrive|outlook|smtp|mailbox|meeting", 190],
        ["Servers & Cloud", r"nutanix|azure|\baws\b|\bvm\b|server|domain controller|backup|storage|sftp", 28],
        ["Ticketing & Documentation", r"autotask|ticket|jira|confluence|documentation|runbook|training|survey|spec\b", 45],
        ["Claude & Automation", r"claude|cowork|\bmcp\b|skill|automation|connector|hook|workflow|agent", 250],
    ],
    "types": [
        ["UI / Dashboard", r"dashboard|visuali[sz]|\bui\b|portal|console hub|viewer|artifact|library"],
        ["Integration", r"integration|connector|\bmcp\b|\bapi\b|\bsso\b|\bsync\b|connected|connect to"],
        ["Fix / Troubleshoot", r"issue|fix|error|fail|broken|not working|disconnect|troubleshoot|blocking|denied|freeze|can.?t|cannot|bogus"],
        ["Improve / Modernise", r"improv|moderni[sz]e|optimi|clean ?up|upgrade|migrat|resourcing|path to|100%|stale|retire|decommission|replace"],
        ["Plan / Strategy", r"\bplan\b|\bpoa\b|strategy|framework|roadmap|curriculum|design|handoff|positioning"],
        ["Build / Setup", r"setup|set up|build|create|\badd\b|install|provision|deploy|implementation|configuration|skill pack|training materials"],
        ["Review / Audit", r"survey|audit|review|analysis|anaylsis|check|inventory|coverage|monitoring|investigate|track|size|usage|find|discovery"],
    ],
    "overrides": {},
}

if not os.path.exists(CAT_FILE):
    json.dump(DEFAULT, open(CAT_FILE, 'w'), indent=1)
cfg = json.load(open(CAT_FILE))

subprocess.run([sys.executable, '-I', os.path.join(HERE, 'catalog.py')], check=True, stdout=subprocess.DEVNULL, env=dict(os.environ, CHAT_LIBRARY_HOME=ROOT))
rows = json.load(open(os.path.join(ROOT, 'catalog.json')))

def pick(rules, text, default):
    for rule in rules:
        name, rx = rule[0], rule[1]
        if re.search(rx, text, re.I): return name
    return default

def clean_title(r):
    t = r['title']
    if t.startswith('This session is being continued'): t = 'Continued session: ' + (r['start'] or '')[:10]
    t = re.sub(r'@"[^"]+"\s*', '', t).strip()
    return t[:110] or '(untitled)'

OPEN_RX = re.compile(r"next steps?|still (need|to do|left|open|has to)|not (yet )?(done|verified|tested|confirmed|committed|started)|remaining|left to do|to-?do\b|follow[- ]?up|blocked|waiting (on|for)|pending|outstanding|deferred|for later|you.ll need|needs? (your|you)\b|once you|i couldn.t|could not|didn.t get|isn.t (done|working)|manual(ly)?\b", re.I)
ASK_RX = re.compile(r"\?\s*$|want me to|shall i|should i|which (one|option)|let me know|your call|do you want|would you like", re.I)
NEG_RX = re.compile(r"nothing (is )?(left|more|else|remaining|outstanding|pending)( to do)?|no (further|more|remaining|outstanding) (action|work|steps|tasks)|nothing to do|all done|nothing further", re.I)
MD_RX = re.compile(r"[*`#>_]+|^\s*([-•]|\d+[.)])\s*")

def left_lines(txt):
    """Pick the lines of the closing message that say what is still open."""
    lines = [MD_RX.sub('', l).strip() for l in txt.splitlines()]
    lines = [l for l in lines if l and not l.startswith('|')]
    out = []
    for i, l in enumerate(lines):
        if OPEN_RX.search(NEG_RX.sub('', l)) or ASK_RX.search(l):
            out.append(l[:220])
            if len(l) < 60:                       # a short heading: take the lines under it
                out += [x[:220] for x in lines[i+1:i+4]]
        if len(out) >= 5: break
    if not out and lines: out = [lines[-1][:220]]
    seen = set(); res = []
    for l in out:
        if l not in seen: seen.add(l); res.append(l)
    return res[:5]

titles_lc = {r['title'].strip().lower() for r in rows}

def status_of(r):
    left = []
    tail = r['last_text'][-900:]
    started_gap = [t for t in r.get('spawned', []) if t.strip().lower() not in titles_lc]
    if r['pending']:
        return 'plan', r['pending'][:6]
    if r['last_role'] == 'assistant' and ASK_RX.search(r['last_text'][-350:]):
        return 'ask', left_lines(r['last_text'][-900:])
    if OPEN_RX.search(NEG_RX.sub('', tail)):
        return 'open', left_lines(tail)
    if started_gap:
        return 'proposed', ['Proposed a follow-up session that was never started: ' + t for t in started_gap[:3]]
    if r['last_role'] == 'user' and r['users']:
        return 'unanswered', ['Last message was yours, no reply: ' + r['last_human'][:160]]
    return 'done', []

items = []
for r in rows:
    has_page = os.path.exists(os.path.join(PROJ, r['pdir'], 'session-%s.html' % r['sid']))
    text = (clean_title(r) + ' ' + r['snippet'][:160])
    # classify mostly on the title; the first message only breaks ties
    topic = pick(cfg['topics'], clean_title(r), None) or pick(cfg['topics'], text, 'Other')
    typ = pick(cfg['types'], clean_title(r), None) or pick(cfg['types'], text, 'Other')
    ov = cfg.get('overrides', {}).get(r['sid'], {})
    items.append(dict(
        id=r['sid'], t=clean_title(r), sn=r['snippet'][:200], topic=ov.get('topic', topic), type=ov.get('type', typ),
        src=r['src'], auto=r['auto'], task=r['task'], s=(r['start'] or '')[:10], e=(r['end'] or '')[:10],
        st=status_of(r)[0], left=status_of(r)[1], n=r['users'], href=('%s/session-%s.html' % (r['pdir'], r['sid'])) if has_page else '%s/combined_transcripts.html' % r['pdir']))

topics = [t[0] for t in cfg['topics']] + ['Other']
types = [t[0] for t in cfg['types']] + ['Other']
data = json.dumps(dict(items=items, topics=topics, types=types, hues={t[0]: t[2] for t in cfg['topics'] if len(t) > 2}, built=__import__('datetime').datetime.now().strftime('%d %b %Y %H:%M')), separators=(',', ':'))
data = data.replace('</', '<\\/')

html = open(os.path.join(HERE, 'library_template.html')).read().replace('__DATA__', data)
open(os.path.join(PROJ, 'library.html'), 'w').write(html)

import collections
c = collections.Counter(i['topic'] for i in items if not i['auto'])
print('library.html written:', len(items), 'sessions;', sum(i['auto'] for i in items), 'automated')
for k, v in c.most_common(): print('  %-32s %d' % (k, v))
print('status:', dict(collections.Counter(i['st'] for i in items if not i['auto'])))
print('types:', dict(collections.Counter(i['type'] for i in items if not i['auto'])))
print('missing session pages:', sum(1 for i in items if i['href'].endswith('combined_transcripts.html')))
