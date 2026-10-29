// (v64) Body Run's online part, bundled on its own (fb.js) and loaded by the game only when wanted: Google sign-in
// (Firebase Auth, a pop-up) and each mini-game's best score of all players (Firestore Lite, collection 'best', one
// document a game: { score, name, uid, at }; the rules let a signed-in player write only their own, only higher).
// Built: npx esbuild fb_src.js --bundle --format=esm --minify --outfile=fb.js
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, onAuthStateChanged, signOut } from 'firebase/auth';
import { getFirestore, collection, doc, getDoc, getDocs, setDoc, serverTimestamp } from 'firebase/firestore/lite';

let auth = null, db = null;
const who = (u) => (u ? { uid: u.uid, name: ((u.displayName || '').trim() || 'Player').slice(0, 24) } : null);

export function init(cfg, onUser) {
  const app = initializeApp(cfg);
  auth = getAuth(app); db = getFirestore(app);
  onAuthStateChanged(auth, (u) => onUser(who(u)));
}
export async function login() {
  const p = new GoogleAuthProvider(); p.setCustomParameters({ prompt: 'select_account' });
  const r = await signInWithPopup(auth, p); return who(r.user);
}
export async function logout() { await signOut(auth); }
export async function bests() {
  const out = {}; const s = await getDocs(collection(db, 'best'));
  s.forEach((d) => { const v = d.data(); out[d.id] = { score: v.score | 0, name: String(v.name || '') }; });
  return out;
}
export async function best(key) { const d = await getDoc(doc(db, 'best', key)); if (!d.exists()) return null; const v = d.data(); return { score: v.score | 0, name: String(v.name || '') }; }
export async function submit(key, score, name) {
  const u = auth.currentUser; if (!u) throw new Error('not signed in');
  await setDoc(doc(db, 'best', key), { score: Math.round(score), name: String(name).slice(0, 24), uid: u.uid, at: serverTimestamp() });
}
