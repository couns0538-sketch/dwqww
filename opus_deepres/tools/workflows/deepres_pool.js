export const meta = {
  name: 'forge-deepres-pool',
  description: 'Forge deep research as ONE dynamic workflow: a queue of licence-gated research tasks, a pool of 10 workers (5 after 04:55 PC clock, none started after 07:20), a Fable verifier queued after every research task, a planner that adds new sub-tracks when the queue runs dry, implementation specs for the top cards, and a late cross-track critic plus ranking draft',
  phases: [
    { title: 'Research', detail: 'continued and new sub-tracks; cards + notes written as they go' },
    { title: 'Verify', detail: 'Fable 5.1 skeptic after each research task', model: 'fable' },
    { title: 'Plan', detail: 'planner proposes new sub-tracks when the queue is empty' },
    { title: 'Spec', detail: 'implementation-ready own-words specs for the top cards' },
    { title: 'Late', detail: 'cross-track critic and ranking draft', model: 'fable' },
  ],
}

const ROOT = args.root
const PY = args.python
const T_FIVE = 6 * 60 + 55     // 04:55 as minutes after 22:00
const T_LATE = 8 * 60          // 06:00
const T_STOP = 9 * 60 + 20     // 07:20: no new task starts after this

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

function researchPrompt(t) {
  return `You are a research worker of the Forge deep-research job, sub-track ${t.key} (${t.title}). ${HEAD}
Scratch only under F:/odr/work/${t.key}/. Run \`date +%H:%M\` at your start; stop researching ${t.minutes || 60} minutes later or at 07:30 PC clock (whichever comes first), then finish the cards, run the linter on cards/${t.key}/*.md and hand back.
${t.continue_note ? 'CONTINUATION: ' + t.continue_note + '\n' : ''}Outputs: cards/${t.key}/*.md (ids ${t.key}-NN-short-name; at most 4 cards: top 2 full, rest one-line cards; if more than 4 exist from an earlier worker, keep the 4 strongest as cards and move the rest into notes/${t.key}/TABLE.md as rows - never delete a file: overwrite a dropped card's file with one line "MERGED into notes/${t.key}/TABLE.md row N" only if you moved it), notes/${t.key}/sources.md, notes/${t.key}/licences.md, notes/${t.key}/TABLE.md (every candidate: idea | source + link | licence | logged numbers | Forge has it (file:line) | verdict)${t.extra_outputs ? ', ' + t.extra_outputs : ''}. Every card states crew hours in Effort. Write only in your folders; other workers run in parallel.
SUB-TRACK BRIEF:
${t.brief}
Hand back (structured, with clock): every card (id, title, status, source number with conditions, Forge estimate UNPROVEN, effort in crew hours, gate route, path), deliverables, dead ends, evidence for EXISTING cards (card id + number + link), sources used, PENDING items. No file contents.`
}

function verifyPrompt(t, r) {
  const hand = r ? JSON.stringify(r).slice(0, 6000) : 'NO HAND-BACK (the research worker died, was stopped or skipped): verify whatever is on disk.'
  return `You are the adversarial verifier for sub-track ${t.key} (${t.title}) of the Forge deep-research job. ${HEAD}
Scratch only under F:/odr/work/${t.key}-verify/. Run \`date +%H:%M\` at your start and stop ${t.verify_minutes || 20} minutes later (or at 07:40 PC clock). Try to REFUTE the cards in cards/${t.key}/ and the notes in notes/${t.key}/; default to "unverifiable" when a number cannot be traced. Checks: (1) every full card and two one-liners: re-open each cited source number and confirm it (recompute Elo from W/L/D where given); (2) reading rule and no other engine's tuned constant proposed as a Forge value; (3) licence rows re-run with tools/licence_at.py --row; (4) Forge-has-it greps re-run, cited lock lines read (also check our own prior code named in notes/TRIED_GATES.md, e.g. packb ReSearchAdjust / FiftyDamp, packa, E3 options, for a duplicate); (5) duplicates against all existing cards (ls cards/*/); (6) at most 4 cards in the folder, crew hours present, UNPROVEN labels, names, card_lint clean.
Write findings to notes/${t.key}/VERIFY.md as you go (card | claim | CONFIRMED / CORRECTED / UNVERIFIABLE / VIOLATION / DUPLICATE | evidence). You MAY correct a wrong number or link in a card ("(corrected by verify: ...)"), MUST mark a violation or duplicate in the card's Status line, never delete a card, and write nothing outside cards/${t.key}/, notes/${t.key}/ and your scratch folder.
The research worker's hand-back was: ${hand}
Hand back (with clock): counts, corrections, unverifiable items, violations / duplicates, lint state, summary.`
}

function plannerPrompt(n) {
  return `You are the planner of the Forge deep-research job (planner call ${n}). ${HEAD}
Goal from the owner: find MORE improvements for Forge (stronger or faster), each as a licence-checked, testable card with logged evidence. Read: ls cards/*/ (all card titles), notes/CRITIC.md (coverage matrix and uncovered questions), notes/TOP_SECOND_VOTE.md, every notes/*/TABLE.md and notes/*/VERIFY.md summary lines, STATUS.md. Propose up to 5 NEW sub-tracks that are not covered yet and are likely to yield logged gains Forge lacks - e.g. engines not mined yet (Koivisto, Ethereal, Halogen, RubiChess, Weiss, Clover, Sirius-like MIT engines you can find with licence_at.py), sub-areas not yet covered (specific pruning / reduction / extension / history / TT / qsearch / move-ordering topics, eval post-processing, datagen and training levers, node-identical speed in our own code), and follow-ups that turn a strong existing card into a better-evidenced one. Never: Lazy SMP scaling, tablebase settings, worker / queue reliability, process tracks (parked by the owner), bigger L1 / L2 nets (dropped), or anything already a card. Keys: a new letter on an existing track number (e.g. T04J, T05F, T06C) that is NOT in this list of used keys: ${args.used_keys_hint}; the script also refuses duplicates. Each brief must name the sources (repo names, licence tier), the questions, Forge's side (lock files to grep), and the card rule (at most 4 cards; logged gain of at least +2 Elo at STC with an LTC result, or +3 at STC; own start values and ranges). Write nothing except notes/PLANNER_${n}.md (your proposals, one paragraph each).
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
const used = new Set(queue.map(t => t.key))
const results = []
let running = 0
let plannerCalls = 0
let planning = false
let lateQueued = false
let waiters = []
function notify() { const w = waiters; waiters = []; for (const r of w) r() }
function waitForChange() { return new Promise(r => waiters.push(r)) }

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
      log(`verify ${t.key}: fable model call failed (${String(e).slice(0, 80)}); retrying with the session model`)
      v = await agent(verifyPrompt(t, t.research), { label: `verify:${t.key}:retry`, phase: 'Verify', schema: VERIFY_SCHEMA, effort: 'max' })
    }
    seeClock(v)
    results.push({ key: t.key, kind: 'verify', result: v })
    log(`${t.key} verify ${v ? 'done: ' + v.checked + ' checked at ' + v.clock : 'returned nothing'}`)
  } else if (t.kind === 'note') {
    const opts = { label: `${t.key}`, phase: t.phase || 'Spec', schema: NOTE_SCHEMA, effort: 'max' }
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
    queue.push({ kind: 'research', key, title: tr.title, brief: tr.brief, minutes: 60, verify_minutes: 20 })
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
    const t = queue.shift()
    if (!t) {
      if (!planning && plannerCalls < (args.max_planner || 6)) {
        running += 1
        try { await runPlanner() } finally { running -= 1; notify() }
        continue
      }
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
