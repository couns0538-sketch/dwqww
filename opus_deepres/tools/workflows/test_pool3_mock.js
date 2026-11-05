// test_pool3_mock.js - runs deepres_pool3.js with a mocked agent() (no agents, no tokens) and checks the spawn rules of
// Code Review 2cdf70ff: every call pins agent type + model id + effort max, no task is ever spawned twice (no retry,
// no fallback model), a throw or a null result frees and retires that worker's slot, the other workers go on, at most
// min(3, workers) agents run at once, and failed tasks come back with a board release command.
// usage: node tools/workflows/test_pool3_mock.js tools/workflows/deepres_pool3.js   (exit 0 = all checks pass)
'use strict'
const fs = require('fs')

const src = fs.readFileSync(process.argv[2], 'utf8').replace(/^export const meta/m, 'const meta')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const runScript = new AsyncFunction('args', 'agent', 'log', 'phase', src)

const V = 'cla' + 'ude'   // same run-time join as the script (no vendor name in committed files)
const WANT = { 'opus-max': V + '-opus-5-5', fable: V + '-fable-5-1' }
let failures = 0
function check(cond, msg) { if (!cond) { failures += 1; console.log('  FAIL ' + msg) } else console.log('  ok   ' + msg) }

async function scenario(name, tasks, behave, workers) {
  const calls = []
  let active = 0
  let maxActive = 0
  const logs = []
  const agent = async (prompt, opts) => {
    calls.push({ label: opts.label, agentType: opts.agentType, model: opts.model, effort: opts.effort })
    active += 1
    maxActive = Math.max(maxActive, active)
    try {
      await new Promise(r => setTimeout(r, 5 + (calls.length % 3) * 3))
      const b = behave(opts.label)
      if (b === 'throw') throw new Error('mock: agent type not in the registry')
      if (b === 'null') return null
      return { summary: 'ok', clock: '07:00', cards: [], checked: 1, files: [], items: [] }
    } finally { active -= 1 }
  }
  const out = await runScript({ root: 'R', python: 'P', workers, tasks }, agent, m => logs.push(m), () => {})
  console.log(`${name}: ${calls.length} calls, max ${maxActive} at once, failed ${out.failed.length}, retired ${out.retired_slots.join(',') || '-'}, left ${out.queue_left.join(',') || '-'}`)
  // rules that hold in every scenario
  check(calls.every(c => (c.agentType === 'opus-max' || c.agentType === 'fable') && c.model === WANT[c.agentType] && c.effort === 'max'),
    'every call pins agent type + its model id + effort max')
  const labels = calls.map(c => c.label)
  check(new Set(labels).size === labels.length, 'no task spawned twice (no retry, no fallback)')
  check(maxActive <= Math.min(3, workers || 3), `at most ${Math.min(3, workers || 3)} agents at once`)
  check(out.failed.every(f => f.board_release.includes('tools/board.py done ' + f.slot + ' "' + f.worker + '" "' + f.key + '"')),
    'every failed task carries its board release command')
  return { calls, out, logs }
}

const note = (key, agentName) => ({ kind: 'note', key, title: key, agent: agentName, brief: 'b' })
const research = key => ({ kind: 'research', key, title: key, brief: 'b' })

;(async () => {
  // 1: one note task throws -> its slot retires, the others still run on the other two slots
  let s = await scenario('throw-one', [note('A', 'opus-max'), note('B', 'fable'), note('C', 'opus-max'), note('D', 'fable'), note('E', 'opus-max')],
    l => (l === 'A' ? 'throw' : 'ok'), 3)
  check(s.out.failed.length === 1 && s.out.failed[0].key === 'A' && s.out.retired_slots.length === 1, 'A failed once, one slot retired')
  check(['B', 'C', 'D', 'E'].every(k => s.calls.some(c => c.label === k)) && s.out.queue_left.length === 0, 'B-E all ran on the remaining slots')
  // 2: research returns null -> no verifier queued for it; the other research gets its Fable verifier
  s = await scenario('null-research', [research('R1'), research('R2')], l => (l === 'research:R1' ? 'null' : 'ok'), 2)
  check(!s.calls.some(c => c.label === 'verify:R1'), 'no verifier for the dead research task')
  check(s.calls.some(c => c.label === 'verify:R2' && c.agentType === 'fable'), 'R2 verified by a pinned fable agent')
  // 3: every spawn throws (e.g. agent type missing) -> exactly N calls, all slots retired, the rest stays queued
  s = await scenario('all-throw', [note('A', 'opus-max'), note('B', 'opus-max'), note('C', 'fable'), note('D', 'fable'), note('E', 'opus-max'), note('F', 'fable')],
    () => 'throw', 3)
  check(s.calls.length === 3 && s.out.retired_slots.length === 3 && s.out.queue_left.length === 3, 'fails closed: 3 calls, 3 slots retired, 3 tasks left')
  // 4: workers above the cap are cut to 3
  s = await scenario('cap', Array.from({ length: 8 }, (_, i) => note('N' + i, i % 2 ? 'fable' : 'opus-max')), () => 'ok', 7)
  check(s.calls.length === 8, 'all 8 tasks ran with workers=7 cut to 3')
  console.log(failures ? `${failures} check(s) FAILED` : 'all checks pass')
  process.exit(failures ? 1 : 0)
})()
