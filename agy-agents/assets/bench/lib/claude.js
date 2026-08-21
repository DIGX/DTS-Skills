'use strict';
//
// Reads Claude Code session transcripts.
//
// isSidechain is the whole reason this is cheap: it separates the reviewer
// subagent's turns from the main thread with no new instrumentation, which is
// exactly the split the Effort panel needs. Cache reads and writes are broken
// out too, so cost prices them at their real rates instead of counting a cache
// hit as fresh input — which would inflate Claude's side several-fold.

const fs = require('fs');
const path = require('path');
const { clipActive, elapsed } = require('./clip.js');

function slugFor(cwd) {
	return String(cwd).replace(/[:\\/ ]/g, '-');
}

function totalOf(t) {
	const k = t.tokens;
	return k.in + k.out + k.think + k.cache_read + k.cache_write;
}

// Resuming a session rewrites the earlier turns into the new session file, so
// the same turn sits on disk in as many copies as the session was resumed.
// Against this project's own transcripts that is 1161 usage-bearing turns for
// 585 distinct ids — summing them would report 2.25x the output tokens and
// 1.91x the cache reads for the arm the benchmark is measuring.
//
// Two rules, and both were chosen from what the copies actually look like
// rather than from what is convenient. Keep the fullest copy: the one id whose
// copies disagree has two carrying real usage and four carrying zeroes, and
// file order is alphabetical by session uuid, so first-seen would book that
// turn as free whenever a zero copy sorted first. Take the earliest stamp: the
// turn happened once, and these stamps are what active time is clipped from, so
// a replay written hours later must not stretch the session it belongs to.
//
// A turn with no id is kept as it stands. Nothing can match it to anything, and
// folding every id-less turn onto one undefined key would lose them all.
function dedupe(turns) {
	const byId = new Map();
	const out = [];
	for (const t of turns) {
		if (!t.id) { out.push(t); continue; }
		const seen = byId.get(t.id);
		if (!seen) { byId.set(t.id, t); out.push(t); continue; }
		if (t.ts < seen.ts) seen.ts = t.ts;
		if (totalOf(t) > totalOf(seen)) {
			seen.model = t.model;
			seen.sidechain = t.sidechain;
			seen.session = t.session;
			seen.tokens = t.tokens;
		}
	}
	return out;
}

function readTurns(projectsDir, slug) {
	const dir = path.join(projectsDir, slug);
	let files;
	try {
		files = fs.readdirSync(dir).filter(n => n.endsWith('.jsonl'));
	} catch (e) {
		// Not `return []`. An unreadable project directory is the Claude arm
		// being unmeasurable, and an empty turn list is indistinguishable from
		// an arm that spent no time and no tokens — a complete-looking result
		// that is false. A directory that exists and holds no sessions still
		// answers [], because that answer is true.
		throw new Error(
			'cannot read the Claude project directory (' + dir + '): ' +
			(e.code === 'ENOENT'
				? 'nothing is there. The slug is the working directory with ' +
				  'each of : \\ / and space replaced by -'
				: e.message)
		);
	}

	const turns = [];
	for (const f of files.sort()) {
		let text = '';
		try { text = fs.readFileSync(path.join(dir, f), 'utf8'); } catch (e) { continue; }
		for (const line of text.split('\n')) {
			if (!line) continue;
			let j;
			// A half-written last line is normal in a live session. Skipping it
			// loses one turn; aborting the file would lose the whole session.
			try { j = JSON.parse(line); } catch (e) { continue; }
			if (j.type !== 'assistant') continue;
			const m = j.message || null;
			const u = (m && m.usage) || null;
			if (!u) continue;
			const ts = Date.parse(j.timestamp);
			if (!Number.isFinite(ts)) continue;
			// Anthropic bills a cache write by its lifetime: 1.25x input for
			// five minutes, 2x for an hour. Claude Code writes hour-long
			// entries — 4,411,940 of these tokens against zero five-minute ones
			// across this project — and cache writes are about half the arm's
			// notional cost, so a reader that drops the breakdown makes the
			// hour rate unreachable and understates the arm by about a fifth.
			const cc = u.cache_creation || null;
			turns.push({
				ts,
				id: (m && m.id) || null,
				model: (m && m.model) || 'unknown',
				sidechain: j.isSidechain === true,
				session: j.sessionId || f.replace(/\.jsonl$/, ''),
				tokens: {
					in: u.input_tokens || 0,
					out: u.output_tokens || 0,
					think: (u.output_tokens_details && u.output_tokens_details.thinking_tokens) || 0,
					cache_read: u.cache_read_input_tokens || 0,
					cache_write: u.cache_creation_input_tokens || 0,
					cache_write_1h: (cc && cc.ephemeral_1h_input_tokens) || 0,
				},
			});
		}
	}
	const unique = dedupe(turns);
	unique.sort((a, b) => a.ts - b.ts);
	return unique;
}

function blank() {
	return { turns: 0, in: 0, out: 0, think: 0, cache_read: 0, cache_write: 0, cache_write_1h: 0 };
}

function summarise(turns, gapS) {
	const main = blank();
	const side = blank();
	for (const t of turns) {
		const bucket = t.sidechain ? side : main;
		bucket.turns++;
		bucket.in += t.tokens.in;
		bucket.out += t.tokens.out;
		bucket.think += t.tokens.think;
		bucket.cache_read += t.tokens.cache_read;
		bucket.cache_write += t.tokens.cache_write;
		bucket.cache_write_1h += t.tokens.cache_write_1h || 0;
	}
	const stamps = turns.map(t => t.ts);
	return {
		active_s: clipActive(stamps, gapS),
		elapsed_s: elapsed(stamps),
		main,
		sidechain: side,
	};
}

module.exports = { slugFor, readTurns, summarise };
