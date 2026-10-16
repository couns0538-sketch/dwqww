import { Board } from '../board/board';
export declare function hiddenSize(): number;
export declare let resolvedDefaultPath: string;
export declare function resetAccumulators(): void;
/** Load a net; on any failure the previous net is dropped (HCE fallback) and lastError is set. */
export declare function loadNet(file: string): boolean;
export declare function setUseNNUE(on: boolean): void;
export declare function nnueActive(): boolean;
export declare function nnueInfo(): string;
/** Make slot d (= board.undoStack.length) current, incrementally where possible. Returns d. */
export declare function updateAccumulator(board: Board): number;
/** Side-to-move-relative eval in centipawns. */
export declare function nnueEvaluate(board: Board): number;
/** Testing: full-refresh eval vs incremental slot, returns true if accumulators match. */
export declare function checkAccumulator(board: Board): boolean;

