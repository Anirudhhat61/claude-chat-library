#!/usr/bin/env python3 -I
"""Build catalog.json: one row per session transcript in ../projects (read-only).

Also captures what is left open: the final to-do/plan state and the closing assistant message.
"""
import json, glob, os, re, collections
ROOT = os.environ.get('CHAT_LIBRARY_HOME') or os.path.expanduser('~/Documents/Claude-Chat-Viewer')
PROJ = os.path.join(ROOT, 'projects')

def blocks(msg):
    c = msg.get('content') if isinstance(msg, dict) else None
    if isinstance(c, str): return [{'type': 'text', 'text': c}]
    return [b for b in (c or []) if isinstance(b, dict)]

def text_of(msg):
    return ' '.join(b.get('text', '') for b in blocks(msg) if b.get('type') == 'text').strip()

def apply_plan(state, name, inp):
    """Track the last todo/plan list. TodoWrite replaces; update_plan can replace or step."""
    if name == 'TodoWrite':
        return [{'c': t.get('content', ''), 's': t.get('status', 'pending')} for t in inp.get('todos', []) if isinstance(t, dict)]
    if name.endswith('update_plan'):
        if isinstance(inp.get('items'), list):
            return [{'c': t.get('content', ''), 's': t.get('status', 'pending')} for t in inp['items'] if isinstance(t, dict)]
        st = [dict(x) for x in (state or [])]
        if inp.get('advance'):
            for x in st:
                if x['s'] == 'in_progress': x['s'] = 'completed'; break
            for x in st:
                if x['s'] == 'pending': x['s'] = 'in_progress'; break
        for i in inp.get('done', []) or []:
            if isinstance(i, int) and 0 < i <= len(st): st[i-1]['s'] = 'completed'
        if isinstance(inp.get('start'), int) and 0 < inp['start'] <= len(st): st[inp['start']-1]['s'] = 'in_progress'
        return st
    if name.endswith('wrap_up') and state:
        return [dict(x, s='completed') for x in state]   # wrap_up closes the task list
    return state

rows = {}
for f in glob.glob(PROJ + '/*/*.jsonl'):
    pdir = os.path.basename(os.path.dirname(f)); sid = os.path.basename(f)[:-6]
    title = None; first = None; t0 = t1 = None; n_user = n_asst = 0; cwd = None
    plan = None; last_asst = ''; last_role = None; last_human = ''
    tasks = collections.OrderedDict(); spawned = []
    for l in open(f, errors='replace'):
        try: d = json.loads(l)
        except Exception: continue
        ty = d.get('type')
        if ty == 'custom-title' and d.get('customTitle'): title = d['customTitle']
        ts = d.get('timestamp')
        if ts:
            t0 = ts if not t0 or ts < t0 else t0
            t1 = ts if not t1 or ts > t1 else t1
        if d.get('isSidechain'): continue
        if ty == 'user':
            tx = text_of(d.get('message'))
            if tx and not tx.startswith(('<command-', '<local-command', 'Caveat:', '[Request interrupted', '<task-notification', '<system-reminder', '<side-sessions', '<ci-monitor')) and not any(b.get('type') == 'tool_result' for b in blocks(d.get('message'))):
                n_user += 1; last_role = 'user'; last_human = tx
                if first is None: first = tx
            cwd = cwd or d.get('cwd')
        elif ty == 'assistant':
            m = d.get('message')
            tx = text_of(m)
            for b in blocks(m):
                if b.get('type') != 'tool_use': continue
                nm_, inp_ = b.get('name', ''), b.get('input') or {}
                plan = apply_plan(plan, nm_, inp_)
                if nm_ == 'TaskCreate' and inp_.get('subject'):
                    tasks[str(len(tasks) + 1)] = {'c': inp_['subject'], 's': 'pending'}
                elif nm_ == 'TaskUpdate' and str(inp_.get('taskId')) in tasks:
                    k_ = str(inp_['taskId'])
                    if inp_.get('status') == 'deleted': tasks[k_]['s'] = 'completed'
                    elif inp_.get('status'): tasks[k_]['s'] = inp_['status']
                elif nm_.endswith('spawn_task') and inp_.get('title'):
                    spawned.append(inp_['title'])
            if tx:
                n_asst += 1; last_asst = tx; last_role = 'assistant'
    if first is None and n_user == 0 and n_asst == 0: continue
    first = first or ''
    auto = bool(re.match(r'\s*<scheduled-task', first))
    src = 'Cowork' if 'local-agent-mode-sessions' in pdir else 'Code'
    nm = re.search(r'<scheduled-task name="([^"]+)"', first)
    snippet = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', first))[:240].strip()
    pend = [x['c'] for x in list(plan or []) + list(tasks.values()) if x['s'] in ('pending', 'in_progress') and x['c']]
    rows[(pdir, sid)] = dict(pdir=pdir, sid=sid, src=src, auto=auto, task=nm.group(1) if nm else None,
        title=title or snippet[:80] or '(untitled)', titled=bool(title), snippet=snippet,
        start=t0, end=t1, users=n_user, asst=n_asst, cwd=cwd, size=os.path.getsize(f),
        pending=pend[:8], plan_total=len(plan or []) + len(tasks), spawned=spawned[:6], last_text=last_asst[-2200:], last_role=last_role,
        last_human=re.sub(r'\s+', ' ', last_human)[:240])
out = sorted(rows.values(), key=lambda r: r['start'] or '', reverse=True)
json.dump(out, open(os.path.join(ROOT, 'catalog.json'), 'w'))
print('sessions', len(out), '| automated', sum(r['auto'] for r in out), '| with unfinished plan items', sum(1 for r in out if r['pending'] and not r['auto']))
