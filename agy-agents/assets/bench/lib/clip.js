'use strict';
//
// Active time, with human-idle gaps removed.
//
// A task run across a lunch break and a task run in one sitting are not
// different-speed tasks, but raw elapsed time says they are — and one overnight
// gap would decide the whole comparison. So gaps longer than the threshold are
// excluded, uniformly, whether they fall inside a phase or between two phases.
// Elapsed is kept beside it because clipping is a judgement and the reader is
// entitled to see the number it was applied to.

const IDLE_GAP_DEFAULT = 600;

// The threshold is validated rather than trusted, because every way of getting
// it wrong produces the same answer as a task that took no time at all.
// `BENCH_IDLE_GAP=10m` is Number -> NaN, and `d <= NaN` is false for every gap,
// so a malformed setting clips *all* of the run and reports 0s active for both
// arms. That is the project's standing rule in its sharpest form: an absent
// measurement must never read as a zero one. A throw here is loud at the one
// point where the mistake is still cheap; a 0 is a lie that survives into the
// dashboard and reads as a result.
function requireGap(gapS) {
	if (typeof gapS !== 'number' || !Number.isFinite(gapS) || gapS <= 0) {
		throw new Error(
			'clipActive: idle gap must be a finite positive number of seconds, got ' +
			JSON.stringify(gapS) + '. An unusable threshold clips every gap and ' +
			'reports the run as instantaneous.'
		);
	}
	return gapS;
}

function ordered(stampsMs) {
	if (!Array.isArray(stampsMs)) return [];
	return stampsMs.filter(n => typeof n === 'number' && Number.isFinite(n))
		.sort((a, b) => a - b);
}

// Fewer than two stamps is 0 by contract, and the contract is only safe because
// the collector refuses to publish a run whose stamp count is below two. Zero
// here means "no interval to measure", not "measured, and it was nothing" —
// nothing downstream may read it as the latter.
function clipActive(stampsMs, gapS) {
	requireGap(gapS);
	const t = ordered(stampsMs);
	let total = 0;
	for (let i = 1; i < t.length; i++) {
		const d = (t[i] - t[i - 1]) / 1000;
		// Inclusive: a gap of exactly the threshold is active. The boundary has
		// to fall on one side deliberately, and counting it keeps the default
		// (600) meaning "ten minutes of silence is still working", not "ten
		// minutes of silence is already a break".
		if (d <= gapS) total += d;
	}
	// The sum is rounded once, not each delta, so a run of many sub-second
	// intervals does not accumulate half a second of rounding per stamp.
	return Math.round(total);
}

function elapsed(stampsMs) {
	const t = ordered(stampsMs);
	if (t.length < 2) return 0;
	return Math.round((t[t.length - 1] - t[0]) / 1000);
}

module.exports = { clipActive, elapsed, IDLE_GAP_DEFAULT };
