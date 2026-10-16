import { Board } from '../board/board';
import { SearchLimits, SearchInfo } from './search';
import { Move } from '../board/types';
export interface SmpResult {
    best: Move | null;
    nodes: number;
    depth: number;
    score: number;
    pv: string[];
}
export declare function hashMbToEntries(mb: number): number;
/** hashmb: apply UCI Hash to the shared SMP table and every worker's local table. Call between searches. */
export declare function setHashMb(mb: number): void;
export declare function clearSharedTT(): Promise<void>;
/** ttkeep: clear each worker's persistent local TT (ucinewgame). Message order guarantees it lands before the next job. */
export declare function clearWorkerTTs(): void;
export declare function abortSmpSearch(): void;
export declare function setPoolNNUE(use: boolean, file: string | null): void;
export declare function queryPoolNNUE(): Promise<string[]>;
/** Ensure at least `n` warm workers (all search threads, including main). */
export declare function ensurePool(n: number): Promise<void>;
export declare function shutdownPool(): Promise<void>;
/**
 * Lazy SMP: ALL threads (including main/thread 0) run in warm workers.
 * UCI stays on the Node event loop so `stop` can set the SAB flag / postMessage.
 * Thread 0 posts info; helpers share TT and diversify mildly.
 */
export declare function searchLazySmp(board: Board, limits: SearchLimits, threads: number, onInfo?: (info: SearchInfo) => void): Promise<SmpResult>;

