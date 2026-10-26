// The songs of the two mini-games, five each, at the length of one go (about 35 s): the first three of each are cuts
// of the longer songs (intro, verse, build, chorus, the lift a step higher, the ending), the last two the epic ones.
// Each has `tune` (the notes the stage is laid out on) and `game`: { first: the first note's step, last: the final
// hit's step, build: [from, to) steps of the build (the rhythm stage spins there) }.
window.GameSongs = (() => {
  'use strict';
  const L = SongLib, RH = SongsRH.all, ORB = Songs.all, E = SongsEpic;
  const crash = (bar) => ({ step: bar * 16, k: 'c', v: 1 });
  const game = (song, segs, add, g, tuneOf) => {
    const c = L.cut(song, segs, add);
    c.tune = c.moveNotes(tuneOf(song)); c.game = g; delete c.moveNotes;
    return c;
  };
  // rhythm
  const cellRock = () => game(RH[0](), [[0, 1], [3, 4], [4, 8], [14, 16], [16, 24], [28, 31], [35, 38]], [],
    { first: 16, last: 20 * 16, build: [6 * 16, 8 * 16] }, (s) => s.ch.lead.notes);
  const plasmaFunk = () => game(RH[1](), [[0, 2], [2, 6], [12, 14], [14, 18], [30, 34], [34, 36]],
    [...[8, 10, 12, 13, 14, 15].map((i) => ({ step: 11 * 16 + i, k: 's', v: i < 12 ? 0.6 : 1 })), crash(12)],
    { first: 32, last: 16 * 16, build: [6 * 16, 8 * 16] }, (s) => s.ch.lead.notes);
  const neuroEurobeat = () => game(RH[2](), [[0, 1], [3, 4], [4, 8], [14, 16], [16, 24], [28, 32], [36, 38]], [],
    { first: 16, last: 20 * 16, build: [6 * 16, 8 * 16] }, (s) => [...s.ch.brass.notes.filter((n) => n.step < 4 * 16), ...s.ch.lead.notes]);
  // orbit
  const heartbeatRush = () => game(ORB[0](), [[0, 2], [2, 6], [10, 18], [22, 28]], [crash(14)], { first: 32, last: 18 * 16 }, (s) => s.ch.lead.notes);
  const bubbleParade = () => game(ORB[1](), [[0, 2], [2, 6], [10, 18], [22, 28]], [crash(14)], { first: 32, last: 18 * 16 }, (s) => s.ch.lead.notes);
  const neonSynapse = () => game(ORB[2](), [[0, 2], [2, 6], [10, 18], [24, 28]], [crash(14)], { first: 32, last: 16 * 16 }, (s) => s.ch.lead.notes);
  return { rh: [cellRock, plasmaFunk, neuroEurobeat, ...E.rh], orb: [heartbeatRush, bubbleParade, neonSynapse, ...E.orb] };
})();
