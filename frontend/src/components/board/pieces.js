/**
 * The playing piece, drawn in a 40 x 54 box (base at the bottom): a list of
 * SVG shapes filled with the player's colour (see BoardPawn.vue). Everyone
 * plays a pawn; players choose its colour in the lobby.
 */
const BASE = { tag: 'rect', attrs: { x: 5, y: 41, width: 30, height: 7, rx: 3.5 } }

export const PIECES = ['pawn']

export const PIECE_LABELS = { pawn: 'Pawn' }

export const PIECE_SHAPES = {
  pawn: [
    BASE,
    { tag: 'path', attrs: { d: 'M14.5 24 h11 c0 6 2.2 11.5 6.5 17 h-24 c4.3-5.5 6.5-11 6.5-17z' } },
    { tag: 'ellipse', attrs: { cx: 20, cy: 23, rx: 9.5, ry: 3.2 } },
    { tag: 'circle', attrs: { cx: 20, cy: 12, r: 8.5 } }
  ]
}
