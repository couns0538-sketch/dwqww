export const meta = {
  name: 'forge-deepres-extra',
  description: 'Forge deep research optional tracks T6 (eval post-processing), T7 (time management), T12 (testing / tuning / proofs): licence-gated workers write cards to disk, then one verifier per track',
  phases: [
    { title: 'Research', detail: 'T6, T7, T12 in parallel; cards + notes written under F:/odr/wt/opus_deepres as they go' },
    { title: 'Verify', detail: 'one skeptic per track re-checks quoted numbers, links, licences, reading rule and Forge greps' },
  ],
}

const ROOT = args.root
const PY = args.python

const RESEARCH_SCHEMA = {
  type: 'object',
  properties: {
    cards: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' }, title: { type: 'string' }, status: { type: 'string' },
      source_number: { type: 'string' }, forge_estimate: { type: 'string' }, effort: { type: 'string' },
      gate_route: { type: 'string' }, path: { type: 'string' } }, required: ['id', 'title', 'status', 'path'] } },
    deliverables: { type: 'array', items: { type: 'string' } },
    dead_ends: { type: 'array', items: { type: 'string' } },
    sources_used: { type: 'integer' },
    pending: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
  },
  required: ['cards', 'summary'],
}

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    checked: { type: 'integer' }, confirmed: { type: 'integer' },
    corrected: { type: 'array', items: { type: 'string' } },
    unverifiable: { type: 'array', items: { type: 'string' } },
    violations: { type: 'array', items: { type: 'string' } },
    lint_clean: { type: 'boolean' },
    summary: { type: 'string' },
  },
  required: ['checked', 'summary'],
}

function researchPrompt(t) {
  return `You are a research worker of the Forge deep-research job, track ${t.key} (${t.title}).
FIRST read ${ROOT}/WORKER_RULES.md and ${ROOT}/cards/TEMPLATE.md completely; they are binding (licence and reading rules, caps, save-as-you-go, names, output folders). Work from ${ROOT} (cd there). Tools: ${PY} -I -B tools/mine_commits.py | tools/licence_at.py | tools/card_lint.py | tools/tried_gates.py, and bash tools/forge_has.sh. Web: load WebSearch / WebFetch with ToolSearch ("select:WebSearch,WebFetch") when you need them; prefer gh api for GitHub (commits, PRs: gh api repos/OWNER/REPO/pulls/N --jq '.title,.body'; gh search prs --repo OWNER/REPO "words" --limit 20), WebSearch in standard mode, one search per question.
Run \`date +%H:%M\` at your start. Stop researching ${t.minutes} minutes after your start (or at 07:30 PC clock, whichever comes first), then finish the cards, run the linter, and hand back. Write your card files the moment the first source for them is read and append to notes/${t.key}/sources.md after every source.
Your outputs: cards/${t.key}/*.md (ids ${t.key}-NN-short-name), notes/${t.key}/sources.md, notes/${t.key}/licences.md${t.extra_outputs ? ', ' + t.extra_outputs : ''}. Other tracks (T01, T02, T04, T05) are being researched by other workers right now: do not write into their folders.

TRACK BRIEF (from the owner):
${t.brief}

Hand back (structured): every card you wrote (id, title, status COMPLETE/PARTIAL, the source's number with conditions, Forge estimate UNPROVEN, effort, gate route, path), the deliverable files you wrote, dead ends (one line each), number of sources used, and what is still PENDING. Do not include file contents in the hand-back.`
}

function verifyPrompt(t, r) {
  const hand = r ? JSON.stringify(r).slice(0, 6000) : 'NO HAND-BACK (the research worker died or was skipped): verify whatever is on disk.'
  return `You are the adversarial verifier for track ${t.key} (${t.title}) of the Forge deep-research job.
FIRST read ${ROOT}/WORKER_RULES.md (binding: licence and reading rules, names, no Forge Elo claims). Work from ${ROOT}. Tools: ${PY} -I -B tools/licence_at.py | tools/card_lint.py | tools/mine_commits.py, bash tools/forge_has.sh; WebFetch / WebSearch via ToolSearch ("select:WebSearch,WebFetch"); gh api for GitHub pages.
Run \`date +%H:%M\` at your start and stop ${t.verify_minutes} minutes later (or at 07:40 PC clock). Your job is to try to REFUTE the cards in cards/${t.key}/ and the deliverables in notes/${t.key}/. Default to "unverifiable" when a number cannot be traced to the cited page.
Checks, in this order:
1. For the top 3 full cards (by expected gain): re-open every cited source number (Elo +- error, games, TC, LLR/bounds, engine, link) and confirm it matches the source; for one-line cards spot-check 2. For our own local records (gate results, skills, reports) re-read the cited file and line.
2. Reading rule: no card or note may rely on a SOURCE FILE of a GPL / AGPL / unlicensed repo (links to /blob/ or raw files of such repos under src/ etc. are violations; README, docs, wiki, changelog, commit pages, PR text and test logs are fine; Stockfish and nnue-pytorch source must not be read at all). Also no pasted or paraphrased code from such sources, and no other engine's tuned constants proposed as Forge values.
3. Licence rows in notes/${t.key}/licences.md: re-run tools/licence_at.py --row for each repo cited in the cards and compare.
4. "Forge has it": re-run the card's forge_has.sh grep and confirm the cited file:line.
5. Every Forge-side estimate is labelled UNPROVEN; no vendor / model-company names; run tools/card_lint.py on cards/${t.key}/*.md.
Write your findings to notes/${t.key}/VERIFY.md as you go (one line per check: card | claim | CONFIRMED / CORRECTED / UNVERIFIABLE / VIOLATION | evidence link). You MAY correct a wrong number or link directly in a card (add "(corrected by verify: ...)" next to it) and you MUST mark a reading-rule violation in the card's Status line; never delete a card. Write nothing outside cards/${t.key}/ and notes/${t.key}/.
The research worker's hand-back was: ${hand}
Hand back: counts checked / confirmed, the corrections, the unverifiable items, the violations, whether the linter is clean, and a one-paragraph summary.`
}

const out = await pipeline(
  args.tracks,
  t => agent(researchPrompt(t), { label: `research:${t.key}`, phase: 'Research', schema: RESEARCH_SCHEMA }),
  (r, t) => agent(verifyPrompt(t, r), { label: `verify:${t.key}`, phase: 'Verify', schema: VERIFY_SCHEMA })
    .then(v => ({ key: t.key, research: r, verify: v })),
)
return out
