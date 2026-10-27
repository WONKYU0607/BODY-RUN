# v42: every place long enough to take about 30 s on the first lap (no boosts): the speed then (170 + 0.6/s of running,
# up to 900; it does not climb during the mini-games), in the water 30% under the speed you came in at; the rhythm
# stage's slow walk through the right atrium added to it. Prints the new lengths (per look), rounded to 50
import json, sys
D = json.load(open('/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/places.json'))
P, S2 = D['PLACES'], D['STAGE2']
V0, ACC, VMAX, RUN = 170.0, 0.6, 900.0, 30.0
def dist(vt, T, pen=0.0):                    # running T s from vt
    d, t, dt = 0.0, 0.0, 0.01
    while t < T: d += (min(VMAX, V0 + ACC * (vt + t)) - pen) * dt; t += dt
    return d
vt, pen, out = 0.0, 0.0, []
for k, p in enumerate(P):
    if k == S2: pen = 0.3 * min(VMAX, V0 + ACC * vt)
    L = dist(vt, RUN, pen)
    if p[0] == 'ra': L += 2300                # the rhythm stage walks ~2300 of it slowly (up to 60/s for ~38 s)
    looks = p[3:]; tot = sum(l[1] for l in looks)
    new = [[l[0], int(round(L * l[1] / tot / 50.0)) * 50] for l in looks]
    out.append([p[0], new, round(min(VMAX, V0 + ACC * vt)), round(L)])
    vt += RUN
json.dump(out, open('/tmp/claude-0/-home-claude/3a779e8a-891a-5a91-a306-4a5325e0d53e/scratchpad/placelen.json', 'w'))
s1 = sum(sum(l[1] for l in o[1]) for o in out[:S2]); s2 = sum(sum(l[1] for l in o[1]) for o in out[S2:])
for o in out: print(o[0], o[2], o[1])
print('stage 1', s1, 'stage 2', s2, 'lap', s1 + s2, 'old lap', sum(sum(l[1] for l in p[3:]) for p in P))
