# GitHub Pages — React Blog Minimal

A minimal React + Vite blog scaffold ready for GitHub Pages.

## Quick Start
1) Replace placeholders in files:
   - `package.json` -> `"homepage": "https://<YOUR_GITHUB_USERNAME>.github.io/<YOUR_REPO_NAME>/"`
   - `vite.config.js` -> `base: '/<YOUR_REPO_NAME>/'`
   - `src/main.jsx` -> `basename: '/<YOUR_REPO_NAME>'`
   - `src/ui/App.jsx` GitHub repo link

2) Install
```bash
npm i
npm run dev
```

3) Add a post
- Create `posts/my-new-post.md`
- Append metadata in `src/posts.js`:
  ```js
  { slug: 'my-new-post', title: 'My New Post', date: '2025-09-11', tags: ['AI'], summary: 'Short summary...' }
  ```

4) Deploy to GitHub Pages (gh-pages branch)
```bash
npm run deploy
```
Then in GitHub repo → Settings → Pages → "Branch: gh-pages / root".

## Notes
- This template uses SPA routing with a `404.html` redirect hack suitable for GitHub Pages.
- For custom domains, configure `base` and add a `CNAME` file in the project root.