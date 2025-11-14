# My Tech Blog

이 저장소는 개인 기술 블로그와 향후 실험/프로젝트를 함께 관리하기 위한 공간입니다.  
`blog/` 디렉터리에는 GitHub Pages로 배포되는 React + Vite 기반 블로그가 들어 있습니다.

## 디렉터리 구조
- `blog/` — 블로그 앱 (React + Vite)
  - `src/` — 컴포넌트 및 라우터
  - `public/posts/` — 배포되는 Markdown 원문
  - `dist/` — Vite 빌드 결과 (GitHub Actions에서 생성)
- 기타 상위 디렉터리 — 앞으로 추가할 실험/프로젝트를 위한 공간

## 로컬 개발
```bash
cd blog
npm install
npm run dev
```
개발 서버는 기본적으로 `http://localhost:5173` 에서 실행됩니다.

## 포스트 추가
1. Markdown 파일을 `blog/public/posts/*.md` 에 작성합니다.
2. `blog/src/posts.js` 에 메타데이터(슬러그/제목/태그/요약 등)를 추가합니다.

## 배포
메인 브랜치에 `blog/` 관련 변경사항을 push 하면 `.github/workflows/deploy.yml` GitHub Actions가 실행되어 `blog/` 안에서 빌드 후 Pages로 배포합니다.

필요 시 `blog/vite.config.js`, `blog/src/main.jsx` 등에서 `base`/`basename` 값을 조정하여 커스텀 도메인이나 리포지토리 경로를 맞출 수 있습니다.