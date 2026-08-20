'use strict';
//
// What actually landed, according to git rather than according to a report.
// This is the only source in the benchmark that a model cannot influence by
// describing its work more generously.

const { execFileSync } = require('child_process');

// A run whose range cannot be resolved has not landed nothing. It has landed
// something nobody can count. .agy/solo says this in its own words, about this
// exact quantity — "a rewritten history is not zero commits, it is a range
// nothing can measure" — and the reader has to carry the distinction the writer
// took the trouble to make, or it is discarded one module downstream and the
// dashboard reports a session that may have committed a dozen times as having
// committed none.
function unmeasured(reason) {
	return { commits: null, insertions: null, deletions: null, measured: false, reason };
}

function numstat(range, cwd) {
	if (!range) return unmeasured('no range was recorded for this run');

	// Not a validity check for its own sake. `git log --numstat --format=%H
	// --all` is not an error: it succeeds, and attributes the entire history of
	// the repository to one task. A wrong answer that large arrives with no
	// exit code to notice it, so anything git would read as an option is
	// stopped before git is invoked rather than after.
	if (range.charAt(0) === '-') {
		return unmeasured(JSON.stringify(range) + ' is an option, not a range');
	}

	let out = '';
	try {
		out = execFileSync('git', ['log', '--numstat', '--format=%H', range],
			{ cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
	} catch (e) {
		// A range whose commits have been rebased away is not an error worth
		// aborting a whole scrape for. It is one run that cannot be attributed,
		// and it says so.
		return unmeasured('git could not resolve the range ' + range);
	}

	let commits = 0, insertions = 0, deletions = 0;
	for (const line of out.split('\n')) {
		if (!line.trim()) continue;
		if (/^[0-9a-f]{7,40}$/.test(line.trim())) { commits++; continue; }
		const m = line.split('\t');
		if (m.length >= 3) {
			// '-' is git's marker for a binary file; it is not a line count.
			if (m[0] !== '-') insertions += Number(m[0]) || 0;
			if (m[1] !== '-') deletions += Number(m[1]) || 0;
		}
	}
	return { commits, insertions, deletions, measured: true, reason: null };
}

module.exports = { numstat };
