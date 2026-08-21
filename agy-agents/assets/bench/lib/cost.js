'use strict';
//
// Notional USD. Neither tool is billed per token under these subscriptions, so
// this is a comparison denominator, not a bill — every view that shows it must
// say so. An unknown model prices to null rather than zero: a model we have no
// rate for is not a model that was free, and a silent zero would flatter
// whichever side happened to be unrecognised.

const fs = require('fs');

function loadPrices(file) {
	return JSON.parse(fs.readFileSync(file, 'utf8'));
}

// Longest match, not first match. Key order in a JSON file is authoring order,
// and both vendors ship dated and effort-suffixed ids constantly — this skill's
// own default is gemini-3.7-flash-high, which matches nothing exactly — so a
// broad family key sitting above a specific one would decide what a run is
// billed at by where somebody happened to type it.
function rateFor(id, table) {
	if (table[id]) return table[id];
	let best = null;
	for (const k of Object.keys(table)) {
		if (!id.startsWith(k)) continue;
		if (!best || k.length > best.length) best = k;
	}
	return best ? table[best] : null;
}

// Thinking tokens are billed as output and are already inside output_tokens at
// both vendors, so they are not charged again here. That is 39% of this
// project's output tokens, which is the size of the mistake if the unused
// parameter below is ever read as an oversight and "fixed".
//
// No rounding. One token of opus-5 input is $0.000005; rounded here it is $0,
// and a thousand small runs sum to nothing. Rounding is something a view does
// once, to a number it is about to print.
function priceOf(model, tokens, prices) {
	const table = (prices && prices.models) || {};
	const id = String(model);
	const rate = rateFor(id, table);

	const m = 1e6;
	const t = tokens || {};
	// The hour-long portion is a subset of the total, and is clamped to it: the
	// vendor's own breakdown has been seen to exceed its own total by a few
	// thousand tokens, and a negative five-minute remainder would credit the
	// difference back.
	const cw = Math.max(0, t.cache_write || 0);
	const cw1h = Math.min(cw, Math.max(0, t.cache_write_1h || 0));
	const spent = (t.in || 0) + (t.out || 0) + (t.cache_read || 0) + cw;

	if (!rate) {
		// Zero tokens at an unknown rate is still zero — arithmetic, not a
		// guess. Claude Code writes 28 such turns per project under the model
		// id "<synthetic>", its own interrupts and errors, every count zero. A
		// null there would poison a total that nothing was missing from. null
		// stays reserved for tokens that nobody has a rate for.
		return spent === 0
			? { usd: 0, priced: true, model: id, source: 'no tokens spent' }
			: { usd: null, priced: false, model: id, source: null };
	}

	const usd =
		((t.in || 0) / m) * (rate.in || 0) +
		((t.out || 0) / m) * (rate.out || 0) +
		((t.cache_read || 0) / m) * (rate.cache_read || 0) +
		((cw - cw1h) / m) * (rate.cache_write || 0) +
		(cw1h / m) * (rate.cache_write_1h || rate.cache_write || 0);

	return { usd, priced: true, model: id, source: rate.source || null };
}

module.exports = { loadPrices, priceOf };
