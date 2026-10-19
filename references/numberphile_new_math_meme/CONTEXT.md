# YouTube Uvy5Cs9FDLg — "A New Math Meme" (Numberphile, with Matt Parker and Brady Haran)

Saved 2026-10-19 for Cody. Files here: `transcript.txt` (plain), `transcript.json` (with timings), `oembed.json`. Transcript = YouTube's auto-generated English captions (462 lines, about 16 minutes), so digits and numbers are sometimes garbled; the structure is reliable.

## What the video is
Matt Parker found a math meme: the digits of 262144 stacked as a power tower `2^6^2^1^4^4`, square-rooted, give 262144 back. Why it works, in his account (checked: 2^18 = 262144):
- Evaluate from the top: `4^4 = 256`, then `1^256 = 1`. The **1 is a blocker**: everything above it is neutralised, so the tower collapses to `√(2^(6^2)) = √(2^36) = 2^18 = 262144`.
- General recipe: choose a base `b` and exponent `k` so that `b^k` begins with the digits of `b`; the following digits of the number are a power `n` that a root can cancel; the digit after is a **blocker** (1, or 0, since `x^0 = 1`); every digit after the blocker is a free ride.
- He wrote Python and searched over 300 billion (b, k) combinations, found longer ones, and compared them for "meme quality":
  - `3162278^6^7966335^0^8952` under a square root (a 0 as blocker; check on the first part: `3162278^6` is 1.0000006…e39 and its square root `3162278^3` starts with 3162278).
  - `2^56` under a 7th root (`2^8 = 256`).
  - `247^4 + 8^2^…^0^80…` under a square root, introducing a `+`.
  - A 154 428-digit example (`2673…`, 11th root) with a 0 blocker that he never computed in full — "biggest implied root sign ever used", about a mile long.
  - His favourite: `7^82 + 2^3^0^7^2^8^4^9` under a sixth root `= 678223072849` (digits as spoken; not checked).
- The 0 is "grossly overpowered": it makes everything to its right free and lets it absorb digits on its left, which is why Brady prefers the version without it.

## Context I could find
- I could not find the origin of the meme. Matt Parker says in the video that he could not either and asks for "internet archaeologists". A web search for the title returned nothing relevant.
- The video's stated authority is his own search code; no paper or database is cited. The "new paper" lines are on-screen cuts to each candidate.

## Possible link to the current work (my reading, unverified)
- Both are cases where a leading digit string is chosen so the tail does not matter, which resembles how a Horner address ignores all but the leading digits once the seed is exact. Not established; offered only because it was the closest thing in the transcript.
- No part of the video mentions anything about the semantic engine, the zeta zeros or lensing. If you had a specific reason for saving it, tell me and I'll look at that.
