export const meta = {
  name: 'forge-deepres-phase2',
  description: 'Forge deep research phase 2: one cross-track critic (brief coverage matrix + check of the INTERIM report against the cards) and one independent second vote on the top cards; both write only their own note files',
  phases: [
    { title: 'Check', detail: 'critic and second vote in parallel; findings written to notes/CRITIC.md and notes/TOP_SECOND_VOTE.md as they go' },
  ],
}

const ROOT = args.root
const PY = args.python

const SCHEMA = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: { type: 'object', properties: {
      where: { type: 'string' }, claim: { type: 'string' }, verdict: { type: 'string' }, fix: { type: 'string' } },
      required: ['where', 'verdict'] } },
    uncovered_questions: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
  },
  required: ['findings', 'summary'],
}

const COMMON = `You work for the Forge deep-research job. FIRST read ${ROOT}/WORKER_RULES.md completely (binding: licence and reading rules - never open source files of GPL / AGPL / unlicensed repos, Stockfish and nnue-pytorch source never; no vendor or model-company names; no Forge Elo claims; temporary files only under F:/odr/work/<your folder>/). Work from ${ROOT}. Tools: ${PY} -I -B tools/licence_at.py | tools/card_lint.py | tools/mine_commits.py | tools/tried_gates.py, bash tools/forge_has.sh; WebFetch / WebSearch via ToolSearch ("select:WebSearch,WebFetch"); gh api for GitHub pages. Run \`date +%H:%M\` at your start and stop ${args.minutes} minutes later (or at 07:40 PC clock). You do NOT edit any card, any notes file of a track, STATUS.md, FINAL_REPORT.md, RESUME.md or LICENCES.md: you write only YOUR file (named below), one line per finding as you go, and the coordinator applies the fixes.`

const criticPrompt = COMMON + `
Your file: notes/CRITIC.md. Your role: the cross-track critic.
Part A - coverage matrix. The owner's brief (relayed to you verbatim in the first message) lists named questions per track (T2-card-1, T1, T2, T4, T5, T6, T7, T12). For EVERY named question write one row: track | question | answered where (card id or notes file + line) | answer in one line | or NOT COVERED with the reason. Examples that may be uncovered: T4 history gravity, staged move picker, SEE caching, lazy legality, patches that passed STC and failed LTC and why, terms that scale with TC; T5 weight permutation, TT prefetch placement, accumulator refresh caches, lazy updates, 64 B vs 2 MB alignment, int8 vs int16 L1, AVX2 vs AVX-512; T2 in-check filter, |eval| caps, ply limits, WDL skew, relabel by a stronger teacher, distillation, pipeline histories of 2 engines, the Leela one-liner, the WAC300 card; T1 king-bucket maps, output buckets, pairwise multiplication, data size / L1 size / nps per feature set, the side-by-side recipe table; T12 every listed item. Read the cards and notes to answer; you may answer a small uncovered question yourself from ONE source (one search, one fetch, licence rules apply) and mark it 'answered by the critic'.
Part B - report check. Check every number and claim in FINAL_REPORT.md sections 0-6 (INTERIM) against the card or note it comes from (the card files are the reference). List every mismatch, every number with no source in the cards, every place where the report contradicts a verifier's correction (notes/T<nn>/VERIFY.md), and cross-track contradictions (gate rate, v2 control, Threads, data premise, card ids or titles).
Hand back the findings (where | claim | verdict OK / MISMATCH / UNSOURCED / CONTRADICTION / NOT COVERED | fix), the list of uncovered questions, and a summary.`

const votePrompt = COMMON + `
Your file: notes/TOP_SECOND_VOTE.md. Your role: an independent second vote on the report's top cards. The track verifiers already checked these once (notes/T<nn>/VERIFY.md); do not trust them - re-check from the sources. Cards: ${args.top.join(', ')} (files in cards/T<nn>/).
For each card: (1) re-open the cited source(s) and confirm the quoted numbers (Elo +- error, games, TC, bounds / LLR, engine, commit or PR link; for fishtest-style logs recompute Elo from W/L/D); (2) re-run the card's forge_has.sh grep and read the cited lock lines (lock source path in WORKER_RULES.md; our own code may be read in full) to confirm that Forge lacks the idea or has it OFF, and that the card's proposed change sits where it says; (3) judge whether the OFF-by-default design really keeps the lock's bench pins (option default OFF = identical code path / node counts); (4) flag any constant that looks copied from another engine without an own start value and range; (5) give your own verdict: KEEP / KEEP-WITH-FIX / DOWNGRADE / DROP with one line of reason.
Hand back the findings (where = card id | claim | verdict | fix), and a summary with the per-card verdicts.`

const results = await parallel([
  () => agent(criticPrompt, { label: 'critic', phase: 'Check', schema: SCHEMA }),
  () => agent(votePrompt, { label: 'second-vote', phase: 'Check', schema: SCHEMA }),
])
return { critic: results[0], vote: results[1] }
