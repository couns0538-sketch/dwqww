export const meta = {
  name: 'forge-deepres-pool2',
  description: 'Forge deep research, one dynamic workflow (fresh run, nothing re-run): 10 workers (5 after 04:55, none started after 07:20) on a queue of licence-gated research sub-tracks, a Fable verifier queued after each, a planner that refills the queue BEFORE it runs dry, and a late critic plus ranking draft',
  phases: [
    { title: 'Research', detail: 'seeded and planned sub-tracks; cards + notes written as they go' },
    { title: 'Verify', detail: 'Fable 5.1 skeptic after each research task', model: 'fable' },
    { title: 'Plan', detail: 'planner refills the queue when fewer than 3 research tasks wait' },
    { title: 'Late', detail: 'cross-track critic (Fable) and ranking draft', model: 'fable' },
  ],
}

const ROOT = args.root
const PY = args.python
const T_FIVE = 6 * 60 + 55       // 04:55 as minutes after 22:00
const T_LATE = 8 * 60            // 06:00
const T_PLAN_END = 8 * 60 + 30   // 06:30
const T_STOP = 9 * 60 + 20       // 07:20

function minutesOf(hhmm) {
  const m = /(\d{1,2}):(\d{2})/.exec(hhmm || '')
  if (!m) return null
  const h = Number(m[1]), mi = Number(m[2])
  let t = h * 60 + mi
  if (h < 12) t += 24 * 60
  return t - 22 * 60
}
let latest = minutesOf(args.start_clock) || 0
function seeClock(r) {
  const t = r && minutesOf(r.clock)
  if (t !== null && t !== undefined && t > latest && t < 12 * 60) latest = t
}
function poolSize() { return latest >= T_FIVE ? 5 : 10 }
function stopNew() { return latest >= T_STOP }

const CLOCK = { type: 'string', description: 'output of `date +%H:%M` run just before you hand back' }
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
    summary: { type: 'string' }, clock: CLOCK,
  },
  required: ['cards', 'summary', 'clock'],
}
const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    checked: { type: 'integer' }, confirmed: { type: 'integer' },
    corrected: { type: 'array', items: { type: 'string' } },
    unverifiable: { type: 'array', items: { type: 'string' } },
    violations: { type: 'array', items: { type: 'string' } },
    lint_clean: { type: 'boolean' }, summary: { type: 'string' }, clock: CLOCK,
  },
  required: ['checked', 'summary', 'clock'],
}
const PLAN_SCHEMA = {
  type: 'object',
  properties: {
    tracks: { type: 'array', items: { type: 'object', properties: {
      key: { type: 'string' }, title: { type: 'string' }, brief: { type: 'string' } }, required: ['key', 'title', 'brief'] } },
    summary: { type: 'string' }, clock: CLOCK,
  },
  required: ['tracks', 'summary', 'clock'],
}
const NOTE_SCHEMA = {
  type: 'object',
  properties: {
    files: { type: 'array', items: { type: 'string' } },
    items: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' }, clock: CLOCK,
  },
  required: ['summary', 'clock'],
}

const HEAD = `FIRST read ${ROOT}/WORKER_RULES.md completely (with its "Round 2" section) and ${ROOT}/cards/TEMPLATE.md; both are binding (licence and reading rules: never open a source file of a GPL / AGPL / unlicensed repo, Stockfish and nnue-pytorch source never; caps; save-as-you-go; no vendor or model-company names; no Forge Elo claims, label estimates UNPROVEN). Work from ${ROOT} (cd there). Tools: ${PY} -I -B tools/mine_commits.py | tools/licence_at.py | tools/card_lint.py | tools/tried_gates.py, bash tools/forge_has.sh. Web: ToolSearch("select:WebSearch,WebFetch") when needed; prefer gh api for GitHub pages; one web search per question.`

const DEDUP = `Before writing any card, check ALL existing cards (ls cards/*/ and read the titles), notes/*/TABLE.md, notes/*/DIFF.md and notes/TRIED_GATES.md, and our own prior code named there (packa, packb ReSearchAdjust / FiftyDamp, E3 options, Sf26Bundle, CorrHistPlus, SingularV2): no duplicate cards; better evidence for an existing card goes to your notes as "evidence for <card id>".`

function researchPrompt(t) {
  return `You are a research worker of the Forge deep-research job, sub-track ${t.key} (${t.title}). ${HEAD}
Scratch only under F:/odr/work/${t.key}/. Run \`date +%H:%M\` at your start; stop researching ${t.minutes || 55} minutes later or at 07:30 PC clock (whichever comes first), then finish the cards, run the linter on cards/${t.key}/*.md and hand back.
${DEDUP}
Outputs: cards/${t.key}/*.md (ids ${t.key}-NN-short-name; at most 4 cards: top 2 full, rest one-line cards; a duplicate you discover becomes a one-line merge marker file "MERGED into notes/${t.key}/TABLE.md row N"), notes/${t.key}/sources.md, notes/${t.key}/licences.md, notes/${t.key}/TABLE.md (every candidate: idea | source + link | licence | logged numbers | Forge has it (file:line) | verdict). Every card states crew hours in Effort. Write only in your folders; other workers run in parallel.
SUB-TRACK BRIEF:
${t.brief}
Hand back (structured, with clock): every card (id, title, status, source number with conditions, Forge estimate UNPROVEN, effort in crew hours, gate route, path), deliverables, dead ends, evidence for EXISTING cards (card id + number + link), sources used, PENDING items. No file contents.`
}

function verifyPrompt(t, r) {
  const hand = r ? JSON.stringify(r).slice(0, 6000) : 'NO HAND-BACK in this run: verify whatever is on disk.'
  return `You are the adversarial verifier for sub-track ${t.key} (${t.title}) of the Forge deep-research job. ${HEAD}
Scratch only under F:/odr/work/${t.key}-verify/. Run \`date +%H:%M\` at your start and stop ${t.verify_minutes || 20} minutes later (or at 07:40 PC clock).
${t.continue_note ? 'CONTINUATION: ' + t.continue_note + '\n' : ''}Try to REFUTE the cards in cards/${t.key}/ and the notes in notes/${t.key}/; default to "unverifiable" when a number cannot be traced. Checks: (1) every full card and two one-liners: re-open each cited source number and confirm it (recompute Elo from W/L/D where given); (2) reading rule and no other engine's tuned constant proposed as a Forge value; (3) licence rows re-run with tools/licence_at.py --row; (4) Forge-has-it greps re-run, cited lock lines read, our own prior code checked for a duplicate (notes/TRIED_GATES.md: packa, packb, E3, Sf26Bundle, CorrHistPlus, SingularV2); (5) duplicates against all existing cards (ls cards/*/); (6) at most 4 cards, crew hours present, UNPROVEN labels, names, card_lint clean.
Write findings to notes/${t.key}/VERIFY.md as you go (card | claim | CONFIRMED / CORRECTED / UNVERIFIABLE / VIOLATION / DUPLICATE | evidence). You MAY correct a wrong number or link in a card ("(corrected by verify: ...)"), MUST mark a violation or duplicate in the card's Status line, never delete a card, and write nothing outside cards/${t.key}/, notes/${t.key}/ and your scratch folder.
The research worker's hand-back was: ${hand}
Hand back (with clock): counts, corrections, unverifiable items, violations / duplicates, lint state, summary.`
}

function plannerPrompt(n) {
  return `You are the planner of the Forge deep-research job (planner call ${n}). ${HEAD}
Goal from the owner: find MORE improvements for Forge (stronger or faster), each as a licence-checked, testable card with logged evidence. Read: ls cards/*/ (all card titles), notes/CRITIC.md (coverage matrix, uncovered questions), notes/TOP_SECOND_VOTE.md, every notes/*/TABLE.md, notes/*/DIFF.md and the summary lines of notes/*/VERIFY.md, notes/PLANNER_*.md (earlier proposals - do not repeat them), STATUS.md. Propose up to 8 NEW sub-tracks not covered yet that are likely to yield logged gains Forge lacks: engines or sources not mined yet (check with tools/licence_at.py; MIT source readable, GPL / AGPL / unlicensed text and logs only), narrower sub-areas inside search (a specific pruning / reduction / extension / history / TT / qsearch / move-ordering family), eval post-processing, datagen and training levers, node-identical speed in our own code, and follow-ups that give a strong existing card better evidence. Never: Lazy SMP scaling, tablebase settings, worker / queue reliability, process tracks (parked by the owner), bigger L1 / L2 nets (dropped), time management (capped at 2 cards), or anything already a card. Keys: a new capital letter on an existing track number (pattern T<2 digits><letter>) NOT in this list: ${args.used_keys_hint}, and not in any notes/PLANNER_*.md; the script also refuses duplicates. Each brief: sources (repo names + licence tier), questions, Forge's side (lock files to grep), the card rule (at most 4 cards; logged gain of at least +2 Elo at STC with an LTC result, or +3 at STC; own start values and ranges). Write nothing except notes/PLANNER_${n}.md (one paragraph per proposal).
Hand back (with clock): tracks [{key, title, brief}], summary.`
}

function notePrompt(t) {
  return `You work for the Forge deep-research job: ${t.title}. ${HEAD}
Scratch only under F:/odr/work/${t.key}/. Run \`date +%H:%M\` at your start and stop ${t.minutes || 40} minutes later (or at 07:40 PC clock). You never edit the engine; you only read and write the files named in your task.
TASK:
${t.brief}
Hand back (with clock): the files you wrote, the main items (one line each), summary.`
}

const queue = (args.tasks || []).slice()
const used = new Set((args.used_keys_hint || '').split(/\s+/).filter(Boolean).concat(queue.map(t => t.key)))
const results = []
let running = 0
let plannerCalls = 0
let planning = false
let lateQueued = false
let waiters = []
function notify() { const w = waiters; waiters = []; for (const r of w) r() }
function waitForChange() { return new Promise(r => waiters.push(r)) }
function researchQueued() { return queue.filter(q => q.kind === 'research').length }

async function runOne(t) {
  if (t.kind === 'research') {
    const r = await agent(researchPrompt(t), { label: `research:${t.key}`, phase: 'Research', schema: RESEARCH_SCHEMA, effort: 'max' })
    seeClock(r)
    results.push({ key: t.key, kind: 'research', result: r })
    log(`${t.key} research ${r ? 'handed back ' + (r.cards || []).length + ' cards at ' + r.clock : 'returned nothing'}`)
    if (!stopNew()) { queue.unshift({ kind: 'verify', key: t.key, title: t.title, verify_minutes: t.verify_minutes, research: r }); notify() }
  } else if (t.kind === 'verify') {
    let v = null
    try {
      v = await agent(verifyPrompt(t, t.research), { label: `verify:${t.key}`, phase: 'Verify', schema: VERIFY_SCHEMA, model: 'fable', effort: 'max' })
    } catch (e) {
      log(`verify ${t.key}: fable call failed (${String(e).slice(0, 80)}); retrying with the session model`)
      v = await agent(verifyPrompt(t, t.research), { label: `verify:${t.key}:retry`, phase: 'Verify', schema: VERIFY_SCHEMA, effort: 'max' })
    }
    seeClock(v)
    results.push({ key: t.key, kind: 'verify', result: v })
    log(`${t.key} verify ${v ? 'done: ' + v.checked + ' checked at ' + v.clock : 'returned nothing'}`)
  } else if (t.kind === 'note') {
    const opts = { label: `${t.key}`, phase: t.phase || 'Late', schema: NOTE_SCHEMA, effort: 'max' }
    if (t.model) opts.model = t.model
    let r = null
    try { r = await agent(notePrompt(t), opts) } catch (e) { delete opts.model; r = await agent(notePrompt(t), opts) }
    seeClock(r)
    results.push({ key: t.key, kind: 'note', result: r })
    log(`${t.key} done at ${r ? r.clock : '?'}`)
  }
}

async function runPlanner() {
  planning = true
  plannerCalls += 1
  const p = await agent(plannerPrompt(plannerCalls), { label: `planner:${plannerCalls}`, phase: 'Plan', schema: PLAN_SCHEMA, effort: 'max' })
  seeClock(p)
  let added = 0
  for (const tr of (p && p.tracks) || []) {
    const key = String(tr.key || '').trim()
    if (!/^T\d{2}[A-Z]$/.test(key) || used.has(key)) continue
    used.add(key)
    queue.push({ kind: 'research', key, title: tr.title, brief: tr.brief, minutes: 55, verify_minutes: 20 })
    added += 1
  }
  results.push({ key: `planner:${plannerCalls}`, kind: 'plan', result: p })
  log(`planner ${plannerCalls}: ${added} new sub-tracks queued (clock ${p ? p.clock : '?'})`)
  planning = false
  notify()
  return added
}

async function worker(id) {
  while (true) {
    if (stopNew() || id >= poolSize()) { notify(); return }
    if (!lateQueued && latest >= T_LATE) {
      lateQueued = true
      for (const lt of (args.late || []).slice().reverse()) queue.unshift(Object.assign({ kind: 'note' }, lt))
      notify()
    }
    if (!planning && plannerCalls < (args.max_planner || 12) && researchQueued() < 3 && latest < T_PLAN_END) {
      running += 1
      try { await runPlanner() } finally { running -= 1; notify() }
      continue
    }
    const t = queue.shift()
    if (!t) {
      if (running === 0 && !planning) {
        if (!lateQueued && (args.late || []).length) {
          lateQueued = true
          for (const lt of args.late) queue.push(Object.assign({ kind: 'note' }, lt))
          notify()
          continue
        }
        notify()
        return
      }
      await waitForChange()
      continue
    }
    running += 1
    try { await runOne(t) } catch (e) { log(`task ${t.kind}:${t.key} failed: ${String(e).slice(0, 120)}`) } finally { running -= 1; notify() }
  }
}

const workers = []
for (let i = 0; i < 10; i++) workers.push(worker(i))
await Promise.all(workers)
return { results, planner_calls: plannerCalls, final_clock_minutes_after_22: latest, queue_left: queue.map(t => `${t.kind}:${t.key}`) }
