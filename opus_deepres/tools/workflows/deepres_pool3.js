export const meta = {
  name: 'forge-deepres-pool3',
  description: 'Forge deep research after the usage reset: ONE workflow, at most 3 workers (owner cap), fable / opus-max only, every agent claims and releases a slot on the crew WORKER_BOARD.md; fixed non-overlapping queue, a Fable verifier after each research task, nothing new after 07:20',
  phases: [
    { title: 'Work', detail: 'fixer, new card, second vote, specs, optional research' },
    { title: 'Verify', detail: 'Fable 5.1 skeptic after each research task', model: 'fable' },
  ],
}

const ROOT = args.root
const PY = args.python
const T_STOP = 9 * 60 + 20   // 07:20 as minutes after 22:00

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
const NOTE_SCHEMA = {
  type: 'object',
  properties: {
    files: { type: 'array', items: { type: 'string' } },
    items: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' }, clock: CLOCK,
  },
  required: ['summary', 'clock'],
}

const HEAD = `FIRST read ${ROOT}/WORKER_RULES.md completely (with its "Round 2" section, the crew's gate decision and the board rule) and ${ROOT}/cards/TEMPLATE.md; both are binding (licence and reading rules: never open a source file of a GPL / AGPL / unlicensed repo, Stockfish and nnue-pytorch source never; caps; save-as-you-go; no vendor or model-company names; no Forge Elo claims, label estimates UNPROVEN). Work from ${ROOT} (cd there). Tools: ${PY} -I -B tools/mine_commits.py | tools/licence_at.py | tools/card_lint.py | tools/tried_gates.py | tools/board.py, bash tools/forge_has.sh. Web: ToolSearch("select:WebSearch,WebFetch") only when needed; prefer gh api for GitHub pages. Usage is very low: be economical - few fetches, short notes, no re-reading of files you already have.`

function board(t, label) {
  return `BOARD (crew rule, owner cap of 3 workers): read D:/grok-pc-data/dwqww/WORKER_BOARD.md, then as your FIRST command run \`${PY} -I -B tools/board.py start ${t.slot} "${label}" "${t.key}"\`, and as your LAST command (after your files are written) run \`${PY} -I -B tools/board.py done ${t.slot} "${label}" "${t.key}" "<your main result path>"\`. Write nothing else on D:.`
}

function researchPrompt(t) {
  return `You are a research worker of the Forge deep-research job, sub-track ${t.key} (${t.title}). ${HEAD}
${board(t, 'research:' + t.key)}
Scratch only under F:/odr/work/${t.key}/. Run \`date +%H:%M\` at your start; stop researching ${t.minutes || 40} minutes later or at 07:30 PC clock (whichever comes first), then finish, lint cards/${t.key}/*.md, release your board slot and hand back.
Before writing any card, check ALL existing cards (ls cards/*/), notes/*/TABLE.md, notes/*/DIFF.md, notes/CRITIC2.md and notes/TRIED_GATES.md: no duplicates.
Outputs: cards/${t.key}/*.md (ids ${t.key}-NN-short-name; at most ${t.max_cards || 4} cards), notes/${t.key}/sources.md, notes/${t.key}/licences.md, notes/${t.key}/TABLE.md. Every card states crew hours and uses the crew's gate route (Threads=1, SPRT [0,5] normalized Elo, alpha = beta = 0.05, pentanomial, cap 3,000; capped = UNPROVEN / no decision, one extension if positive).
BRIEF:
${t.brief}
Hand back (structured, with clock): cards (id, title, status, source number with conditions, Forge estimate UNPROVEN, effort, gate route, path), deliverables, dead ends, PENDING items.`
}

function verifyPrompt(t, r) {
  const hand = r ? JSON.stringify(r).slice(0, 5000) : 'NO HAND-BACK: verify whatever is on disk.'
  return `You are the adversarial verifier for sub-track ${t.key} (${t.title}) of the Forge deep-research job. ${HEAD}
${board(t, 'verify:' + t.key)}
Scratch only under F:/odr/work/${t.key}-verify/. Run \`date +%H:%M\` at your start and stop ${t.verify_minutes || 15} minutes later (or at 07:40 PC clock). Try to REFUTE the cards in cards/${t.key}/: re-open each cited source number (recompute Elo from W/L/D), check the reading rule and that no other engine's tuned constant is proposed as a Forge value, re-run the licence rows and the Forge-has-it greps, check duplicates against all cards, run tools/card_lint.py. Write findings to notes/${t.key}/VERIFY.md as you go; you may correct a number in a card ("(corrected by verify: ...)") and must mark a violation or duplicate in its Status line; never delete a card; write nothing outside cards/${t.key}/, notes/${t.key}/, your scratch folder and your board slot.
The research hand-back: ${hand}
Hand back (with clock): counts, corrections, unverifiable items, violations / duplicates, lint state, summary.`
}

function notePrompt(t) {
  return `You work for the Forge deep-research job: ${t.title}. ${HEAD}
${board(t, t.key)}
Scratch only under F:/odr/work/${t.key}/. Run \`date +%H:%M\` at your start and stop ${t.minutes || 35} minutes later (or at 07:40 PC clock). You never edit the engine; you only read and write the files named in your task.
TASK:
${t.brief}
Hand back (with clock): the files you wrote, the main items (one line each), summary.`
}

const queue = (args.tasks || []).slice()
const results = []
let running = 0
let waiters = []
function notify() { const w = waiters; waiters = []; for (const r of w) r() }
function waitForChange() { return new Promise(r => waiters.push(r)) }

async function runOne(t) {
  if (t.kind === 'research') {
    const r = await agent(researchPrompt(t), { label: `research:${t.key}`, phase: 'Work', schema: RESEARCH_SCHEMA, effort: 'max' })
    seeClock(r)
    results.push({ key: t.key, kind: 'research', result: r })
    log(`${t.key} research ${r ? (r.cards || []).length + ' cards at ' + r.clock : 'returned nothing'}`)
    if (!stopNew()) { queue.unshift({ kind: 'verify', key: t.key, title: t.title, verify_minutes: t.verify_minutes, research: r }); notify() }
  } else if (t.kind === 'verify') {
    let v = null
    try {
      v = await agent(verifyPrompt(t, t.research), { label: `verify:${t.key}`, phase: 'Verify', schema: VERIFY_SCHEMA, model: 'fable', effort: 'max' })
    } catch (e) {
      v = await agent(verifyPrompt(t, t.research), { label: `verify:${t.key}:retry`, phase: 'Verify', schema: VERIFY_SCHEMA, effort: 'max' })
    }
    seeClock(v)
    results.push({ key: t.key, kind: 'verify', result: v })
    log(`${t.key} verify ${v ? v.checked + ' checked at ' + v.clock : 'returned nothing'}`)
  } else {
    const opts = { label: t.key, phase: 'Work', schema: NOTE_SCHEMA, effort: 'max' }
    if (t.model) opts.model = t.model
    let r = null
    try { r = await agent(notePrompt(t), opts) } catch (e) { delete opts.model; r = await agent(notePrompt(t), opts) }
    seeClock(r)
    results.push({ key: t.key, kind: 'note', result: r })
    log(`${t.key} done at ${r ? r.clock : '?'}`)
  }
}

async function worker(id) {
  while (true) {
    if (stopNew()) { notify(); return }
    const t = queue.shift()
    if (!t) {
      if (running === 0) { notify(); return }
      await waitForChange()
      continue
    }
    t.slot = `S${id + 1}`
    running += 1
    try { await runOne(t) } catch (e) { log(`task ${t.kind}:${t.key} failed: ${String(e).slice(0, 120)}`) } finally { running -= 1; notify() }
  }
}

const N = Math.min(3, args.workers || 3)   // owner cap: never more than 3
const ws = []
for (let i = 0; i < N; i++) ws.push(worker(i))
await Promise.all(ws)
return { results, final_clock_minutes_after_22: latest, queue_left: queue.map(t => `${t.kind}:${t.key}`) }
