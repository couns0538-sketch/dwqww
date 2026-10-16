/** Static Exchange Evaluation */
import { Board } from '../board/board';
/** SEE for move from→to. Returns net material for side to move. */
export declare function see(board: Board, from: number, to: number, promo?: number): number;
/** Classic iterative SEE with reusable gain buffer */
export declare function seeClassic(board: Board, from: number, to: number, promo?: number): number;
/** True if SEE >= threshold (avoids full fold when possible via early reject). */
export declare function seeGe(board: Board, from: number, to: number, threshold: number, promo?: number): boolean;

