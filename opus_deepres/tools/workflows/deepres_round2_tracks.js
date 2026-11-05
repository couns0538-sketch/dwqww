export const meta = {
  name: 'forge-deepres-round2a',
  description: 'Forge deep research round 2A: eight new licence-gated sub-tracks (GPL/AGPL search logs, MIT feature diffs, HCE and movegen speed), one worker each at max effort, then one Fable verifier each',
  phases: [
    { title: 'Research', detail: 'eight sub-tracks in parallel; cards + notes written under F:/odr/wt/opus_deepres as they go' },
    { title: 'Verify', detail: 'one Fable 5.1 skeptic per sub-track re-checks numbers, links, licences, reading rule, Forge greps', model: 'fable' },
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
    evidence_for_existing: { type: 'array', items: { type: 'string' } },
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
  return `You are a research worker of the Forge deep-research job, sub-track ${t.key} (${t.title}).
FIRST read ${ROOT}/WORKER_RULES.md (including its "Round 2" section) and ${ROOT}/cards/TEMPLATE.md completely; they are binding (licence and reading rules, caps, save-as-you-go, names, output folders, scratch only under F:/odr/work/${t.key}/). Work from ${ROOT} (cd there). Tools: ${PY} -I -B tools/mine_commits.py | tools/licence_at.py | tools/card_lint.py | tools/tried_gates.py, and bash tools/forge_has.sh. Web: load WebSearch / WebFetch with ToolSearch ("select:WebSearch,WebFetch") when needed; prefer gh api for GitHub (commits, PRs: gh api repos/OWNER/REPO/pulls/N --jq '.title,.body'; gh search prs --repo OWNER/REPO "words" --limit 20), WebSearch in standard mode, one search per question.
Run \`date +%H:%M\` at your start. Stop researching ${t.minutes} minutes after your start (or at 07:30 PC clock, whichever comes first), then finish the cards, run the linter, and hand back. Write your card files the moment the first source for them is read and append to notes/${t.key}/sources.md after every source.
Your outputs: cards/${t.key}/*.md (ids ${t.key}-NN-short-name; at most 4 cards: top 2 full, rest one-line cards), notes/${t.key}/sources.md, notes/${t.key}/licences.md, notes/${t.key}/TABLE.md (every candidate you looked at: idea | source + link | licence | logged numbers | Forge has it (file:line) | verdict)${t.extra_outputs ? ', ' + t.extra_outputs : ''}. Other workers are researching other sub-tracks right now: never write into their folders.

SUB-TRACK BRIEF (coordinator, from the owner's request for more Forge improvements):
${t.brief}

Hand back (structured): every card you wrote (id, title, status, the source's number with conditions, Forge estimate UNPROVEN, effort, gate route, path), the deliverable files, dead ends (one line each), evidence you found for EXISTING cards (card id + number + link), number of sources used, and what is still PENDING. No file contents in the hand-back.`
}

function verifyPrompt(t, r) {
  const hand = r ? JSON.stringify(r).slice(0, 6000) : 'NO HAND-BACK (the research worker died or was skipped): verify whatever is on disk.'
  return `You are the adversarial verifier for sub-track ${t.key} (${t.title}) of the Forge deep-research job.
FIRST read ${ROOT}/WORKER_RULES.md (binding: licence and reading rules, names, no Forge Elo claims; scratch only under F:/odr/work/${t.key}-verify/). Work from ${ROOT}. Tools: ${PY} -I -B tools/licence_at.py | tools/card_lint.py | tools/mine_commits.py, bash tools/forge_has.sh; WebFetch / WebSearch via ToolSearch ("select:WebSearch,WebFetch"); gh api for GitHub pages.
Run \`date +%H:%M\` at your start and stop ${t.verify_minutes} minutes later (or at 07:40 PC clock). Try to REFUTE the cards in cards/${t.key}/ and the notes in notes/${t.key}/. Default to "unverifiable" when a number cannot be traced to the cited page.
Checks, in this order: (1) for every full card and two one-liners re-open each cited source number (Elo +- error, games, TC, LLR / bounds, engine, link; recompute Elo from W/L/D where given) and confirm it; (2) reading rule: no reliance on a SOURCE FILE of a GPL / AGPL / unlicensed repo (README, docs, commit pages, PR text and test logs are fine; Stockfish and nnue-pytorch source never), no pasted or paraphrased code, no other engine's tuned constant proposed as a Forge value; (3) licence rows: re-run tools/licence_at.py --row for each cited repo; (4) "Forge has it": re-run the grep, read the cited lock lines (our code may be read in full) and confirm the idea is missing or OFF and that the proposed change sits where the card says; (5) duplicates: compare with the existing cards (ls cards/*/) - a duplicate must be marked in its Status line; (6) UNPROVEN labels, no vendor names, tools/card_lint.py clean.
Write findings to notes/${t.key}/VERIFY.md as you go (card | claim | CONFIRMED / CORRECTED / UNVERIFIABLE / VIOLATION / DUPLICATE | evidence). You MAY correct a wrong number or link in a card (add "(corrected by verify: ...)") and you MUST mark a violation or duplicate in the card's Status line; never delete a card. Write nothing outside cards/${t.key}/, notes/${t.key}/ and your scratch folder.
The research worker's hand-back was: ${hand}
Hand back: counts checked / confirmed, corrections, unverifiable items, violations / duplicates, whether the linter is clean, and a one-paragraph summary.`
}

const out = await pipeline(
  args.tracks,
  t => agent(researchPrompt(t), { label: `research:${t.key}`, phase: 'Research', schema: RESEARCH_SCHEMA, effort: 'max' }),
  (r, t) => agent(verifyPrompt(t, r), { label: `verify:${t.key}`, phase: 'Verify', schema: VERIFY_SCHEMA, model: 'fable', effort: 'max' })
    .then(v => ({ key: t.key, research: r, verify: v })),
)
return out
