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
				think: num(c.tokens_think), total,
			},
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

	return { runs, skipped };
}

module.exports = { readRuns, parseClass };
