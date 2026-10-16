"use strict";
/** Time management v2 (UCI layer). Pure functions, no search.ts dependency.
 *  hard limit: enforced by a main-thread timer through the shared stop flag (precise, not 4096-node polling).
 *  soft limit: checked after each completed iteration (info callback); scaled by best-move stability and score drop. */
Object.defineProperty(exports, "__esModule", { value: true });
exports.SoftController = void 0;
exports.effectiveOverhead = effectiveOverhead;
exports.computeBudget = computeBudget;
/** tm-forge-1726: without movestogo, soft = usable/22 + 0.75*inc, hard = min(0.6*usable, 5*soft).
 *  (Replaces the old movestogo=28 assumption; explicit movestogo keeps the old formula.) */
const FORGE_DIV = 22;
const FORGE_HARD_FRAC = 0.6;
const FORGE_HARD_MULT = 5;
/** Node-fraction scaling applies from this completed depth on. */
const NODE_TM_MIN_DEPTH = 6;
/** Wall time between the soft-stop decision and bestmove reaching the GUI (measured, see permove log). */
const STOP_LATENCY_MS = 10;
/** Overhead per move: UCI option plus extra allowance at short time controls (process scheduling, pipe latency). */
function effectiveOverhead(time, moveOverhead) {
    const mo = Math.max(0, moveOverhead);
    if (time < 1500)
        return mo + 40;
    if (time < 5000)
        return mo + 25;
    if (time < 15000)
        return mo + 10;
    return mo;
}
function computeBudget(inp) {
    const time = Math.max(0, inp.time ?? 0);
    const inc = Math.max(0, inp.inc ?? 0);
    const ovh = effectiveOverhead(time, inp.moveOverhead);
    const mtgGiven = inp.movestogo !== undefined && inp.movestogo > 0;
    const usable = Math.max(0, time - ovh);
    let soft;
    let hard;
    if (mtgGiven) {
        // unchanged movestogo handling
        const mtg = Math.min(inp.movestogo, 60);
        soft = usable / mtg + inc * 0.75;
        // fraction of the clock we allow ourselves on hard: ~40%, rises as the control nears (last moves before time control)
        const frac = mtg <= 2 ? (mtg === 1 ? 0.8 : 0.55) : 0.4;
        hard = Math.min(soft * 3.2, usable * frac);
    }
    else {
        soft = usable / FORGE_DIV + inc * 0.75;
        hard = Math.min(usable * FORGE_HARD_FRAC, soft * FORGE_HARD_MULT);
    }
    // never spend more than the clock minus overhead (incl. the increment we get back only after moving)
    const ceiling = Math.max(0, usable - 5);
    soft = Math.min(soft, hard * 0.8, ceiling);
    hard = Math.min(hard, ceiling);
    // safe floors, but never exceeding what is left
    const floor = Math.min(15, Math.max(1, Math.floor(usable * 0.5)));
    if (hard < floor)
        hard = floor;
    if (soft < floor * 0.6)
        soft = floor * 0.6;
    if (soft > hard)
        soft = hard;
    return { soft: Math.floor(soft), hard: Math.floor(hard) };
}
/** Per-search dynamic soft-limit state. Feed it each completed iteration. */
class SoftController {
    constructor(budget) {
        this.budget = budget;
        this.prevMove = '';
        this.stable = 0;
        this.prevScore = 0;
        this.dropBonus = 1;
    }
    /** returns true if the search should stop now (after this completed iteration). */
    /** bestFrac = rootMoveNodes[best] / sum(rootMoveNodes) for this search (undefined if unavailable). */
    onIteration(depth, score, bestUci, elapsed, bestFrac) {
        if (bestUci === this.prevMove)
            this.stable++;
        else {
            this.stable = 0;
        }
        if (depth > 1 && score < this.prevScore - 25)
            this.dropBonus = Math.min(1.6, this.dropBonus + 0.25);
        else
            this.dropBonus = Math.max(1, this.dropBonus - 0.1);
        this.prevMove = bestUci;
        this.prevScore = score;
        // tm-forge-1726 v2: no "always reach depth 4" floor. At bullet clocks (soft ~25-50 ms) depth 4 alone
        // cost 30-60 ms and every move overran soft (see research/tm_forge_1726_permove.log). Shallow iterations
        // now use the same next-iteration prediction with neutral stability (stable counts mean little there).
        const stabFactor = depth < 4 ? 1.0 : [1.35, 1.15, 1.0, 0.9, 0.8, 0.72][Math.min(this.stable, 5)];
        // tm-forge-1726: node-fraction scaling (best move took most of the root effort -> stop earlier).
        // Kept alongside stability/drop: stability tracks PV changes across iterations, node fraction tracks
        // effort split inside them; Forge/SF-style engines combine both. Product is still capped below hard.
        let nodeFactor = 1;
        if (depth >= NODE_TM_MIN_DEPTH && bestFrac !== undefined && Number.isFinite(bestFrac)) {
            nodeFactor = Math.min(1.4, Math.max(0.6, 1.55 - bestFrac));
        }
        const target = Math.min(this.budget.hard * 0.9, this.budget.soft * nodeFactor * stabFactor * this.dropBonus);
        // next iteration typically costs ~2x: stop if we would not finish it within target
        // + fixed post-iteration latency (abort, worker message, bestmove) measured ~10-17 ms wall
        // Shallow iterations (depth < 4) are cheap relative to the fixed latency, so only stop once the target
        // itself is reached; deeper ones keep the ~2x next-iteration prediction.
        return elapsed + STOP_LATENCY_MS >= target * (depth < 4 ? 1.0 : 0.55);
    }
}
exports.SoftController = SoftController;
//# sourceMappingURL=timeman.js.map
