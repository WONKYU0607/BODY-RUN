# Body Run

몸속을 달리는 가로 러너 게임 (웹).

- `public/` — 배포되는 사이트. `index.html`(게임 코드·사운드·매니페스트를 한 파일에 담은 페이지)과 `assets/`(그림 WebP)
- `game/` — 게임 소스: `game.js`, `sound.js`, `index.html`(뼈대), `manifest.json`(그림 배치표), `assemble.py`(한 페이지로 조립)
- `art/` — 그림을 만드는 파이썬 스크립트와 원본 시트(`src/`)

Vercel은 `public/`을 그대로 올립니다(`vercel.json`).
