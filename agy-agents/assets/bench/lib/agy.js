'use strict';
//
// Reads the per-run sidecars the harness already writes.
//
// The skip rule is the load-bearing decision here. A truncated NDJSON is NOT a
// reason to skip: a deferred run has a truncated stream by definition, and it
// is usually the longest run in the set. Dropping those would bias the split
// toward the short, tidy runs. The real "this was never measured" signal is a
// stream with no .class sidecar, because the sidecar is what the parser writes
// when it completes.

const fs = require('fs');
const path = require('path');

// First match wins, and the CR is stripped before anything looks at a value.
//
// Both rules exist to keep this reader saying the same thing as the shell about
// the same bytes. The shell reads sidecars with class_val(), which is `head -1`
// — so a JS reader that kept the LAST value would disagree with every shell
// caller about a file neither of them wrote wrong. The record they would
// disagree about is the one that matters most: `status=open` above
// `status=success` is precisely the shape .agy/solo's close path rewrites
// rather than appends, and a reader that resolves it to `success` would call a
// bracket finished that the shell still calls open.
//
// The CR is the same failure with a quieter entrance. Number("1000\r") is 1000,
// so every count in a CR-tainted record survives and the record reads healthy;
// only the string comparisons break, which is to say only the rules that decide
// whether the record counts at all.
function parseClass(text) {
	const out = {};
	for (const line of text.split('\n')) {
		const clean = line.replace(/\r$/, '');
		const i = clean.indexOf('=');
		if (i > 0 && !(clean.slice(0, i) in out)) {
			out[clean.slice(0, i)] = clean.slice(i + 1);
		}
	}
	return out;
}

// An absent count is null, never 0: 'the model reported nothing' and 'the model
// used nothing' are different facts, and only one of them is free.
const num = v => (v === undefined || v === '' || v === null) ? null
	: (Number.isFinite(Number(v)) ? Number(v) : null);

function taskOf(base) {
	const m = base.match(/task-(\d+)/);
	return m ? `task-${m[1]}` : 'unknown';
}

function readRuns(logDir) {
	const runs = [];
	const skipped = [];
	let entries = [];
	try {
		entries = fs.readdirSync(logDir);
	} catch (e) {
		return { runs, skipped: [{ path: logDir, reason: 'log directory unreadable' }] };
	}

	for (const name of entries.filter(n => n.endsWith('.ndjson')).sort()) {
		const base = name.replace(/\.ndjson$/, '');
		if (!entries.includes(base + '.class')) {
			skipped.push({ path: path.join(logDir, name), reason: 'no .class sidecar — the run was never measured' });
		}
	}

	for (const name of entries.filter(n => n.endsWith('.class')).sort()) {
		const full = path.join(logDir, name);
		const base = name.replace(/\.class$/, '');
		let c;
		try {
			c = parseClass(fs.readFileSync(full, 'utf8'));
		} catch (e) {
			skipped.push({ path: full, reason: 'class sidecar unreadable' });
			continue;
		}
		if (!('status' in c)) {
			skipped.push({ path: full, reason: 'class sidecar has no status key' });
			continue;
		}

		const arm = c.arm === 'solo' ? 'solo' : 'agy';
		const wall = num(c.wall);
		const total = num(c.tokens_total);
		const status = c.deferred === '1' ? 'deferred' : (c.status || 'unknown');

		// An open solo bracket is not a run yet. Counting it would report a task
		// that is still being worked on as one that finished in zero seconds.
		if (arm === 'solo' && c.status === 'open') {
			skipped.push({ path: full, reason: 'solo bracket still open — close it with `.agy/solo --done`' });
			continue;
		}

		runs.push({
			arm,
			task: c.task || taskOf(base),
			label: base,
			started: num(c.started) === null ? null : num(c.started) * 1000,
			wall,
			model: c.model || (arm === 'solo' ? '' : 'unknown'),
			tokens: {
				in: num(c.tokens_in), out: num(c.tokens_out),
				think: num(c.tokens_think), cache_read: num(c.tokens_cache_read),
				total,
			},
			conversation: c.conversation || '',
			threadTurns: num(c.thread_turns),
			continued: c.continued === '1',
			scope: c.tokens_scope || '',
			tokensOf: '',
			tokensNote: null,
			tools: num(c.tools),
			commits: num(c.commits),
			range: c.range || '',
			status,
			quality: (arm === 'solo')
				? (wall === null ? 'partial' : 'full')
				: ((wall === null || total === null) ? 'partial' : 'full'),
			path: full,
		});
	}

	perTurn(runs);
	return { runs, skipped };
}

// ---------------------------------------------------------------- per turn
//
// agy reports usage for the THREAD, not for the run. Measured against the real
// binary: three calls, the second and third on --continue, reported output
// 25 -> 49 -> 73 for turns that each did the same tiny amount of work. Every
// fix round the protocol sends back on --continue therefore writes a sidecar
// carrying every earlier round's tokens as well as its own, and a collector
// that sums the sidecars counts the first turn once per round after it.
//
// The reserve handover is the sharp case. A primary that has already made tool
// calls is handed over rather than restarted, on --continue, and the reserve
// writes its own sidecar under a different model. The failed primary's tokens
// sit inside that cumulative total, so summing bills them a second time at the
// reserve's rate. Both errors inflate the agy arm, on exactly the long runs.
//
// conversation_id does all the work here: runs that share a thread difference
// against each other, and a handover that opened a NEW thread carries a
// different id and is correctly left alone rather than being differenced
// against a total it never accumulated on.
const TOKEN_KEYS = ['in', 'out', 'think', 'cache_read', 'total'];

// Nulled, not guessed, and not left at the cumulative figure either. A number
// that is known to be too large is worse than an absent one, because it reads
// as a measurement. This is the project rule in its other direction: an absent
// measurement must never read as a zero one, and an unattributable one must
// never read as a measured one.
function cannotAttribute(r, note) {
	for (const k of TOKEN_KEYS) r.tokens[k] = null;
	r.tokensOf = 'unknown';
	r.tokensNote = note;
	r.quality = 'partial';
}

function perTurn(runs) {
	const threads = new Map();

	for (const r of runs) {
		if (r.scope !== 'thread') {
			// Written before this instrumentation existed. The numbers may well
			// be a turn's and may well be a thread's; nothing on disk says
			// which. They are kept visible, because they are the only figures
			// there are, and marked partial so nothing downstream reports them
			// as a measured turn.
			if (r.arm === 'agy' && r.tokens.total !== null) {
				r.tokensOf = 'unknown';
				r.tokensNote = 'logged before thread accounting: this may be the '
					+ 'whole thread, not this run';
				r.quality = 'partial';
			}
			continue;
		}
		if (!threads.has(r.conversation)) threads.set(r.conversation, []);
		threads.get(r.conversation).push(r);
	}

	for (const group of threads.values()) {
		// Position first, then start time for anything agy numbered the same.
		group.sort((a, b) =>
			((a.threadTurns === null ? Infinity : a.threadTurns)
				- (b.threadTurns === null ? Infinity : b.threadTurns))
			|| ((a.started || 0) - (b.started || 0)));

		// The cumulative figures have to be read before any of them is
		// overwritten, or the second subtraction runs against a delta.
		const raw = group.map(r => Object.assign({}, r.tokens));

		for (let i = 0; i < group.length; i++) {
			const r = group[i];
			const n = r.threadTurns;

			// The run that opened the thread accumulated nothing before it, so
			// its running total is its own. That is decided by `continued`, not
			// by num_turns: one fresh dispatch that made four tool calls
			// reports num_turns 4 and owns every one of those tokens, while a
			// --continue reporting 4 is carrying three turns it did not spend.
			// The two numbers are identical and mean opposite things.
			if (!r.continued) { r.tokensOf = 'turn'; continue; }

			// Continued, and there is nothing in the log to continue from. The
			// earlier turns are inside this total and cannot be taken back out.
			if (i === 0) {
				cannotAttribute(r, 'this run continued a thread whose earlier '
					+ 'turns are not in the log, and its total includes them');
				continue;
			}

			if (n === null) {
				cannotAttribute(r, 'agy reported no position in the thread, so '
					+ 'this run cannot be separated from the ones before it');
				continue;
			}

			const prev = group[i - 1];
			if (prev.threadTurns === null || prev.threadTurns >= n) {
				cannotAttribute(r, 'the run before this one in the thread has no '
					+ 'position after it, so the two cannot be ordered');
				continue;
			}

			const before = raw[i - 1];
			const delta = {};
			let ok = true;
			for (const k of TOKEN_KEYS) {
				const a = r.tokens[k], b = before[k];
				if (a === null || b === null) { ok = false; break; }
				// A running total cannot shrink. If it did, one of the two
				// sidecars is not what it says it is, and the difference is not
				// a measurement of anything.
				if (a < b) { ok = false; break; }
				delta[k] = a - b;
			}
			if (!ok) {
				cannotAttribute(r, 'the thread total is not larger than the turn '
					+ 'before it, so the difference is not this run');
				continue;
			}
			Object.assign(r.tokens, delta);
			r.tokensOf = 'turn';
		}
	}
	return runs;
}

module.exports = { readRuns, parseClass, perTurn };
