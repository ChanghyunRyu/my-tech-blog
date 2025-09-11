import React from 'react'
import { Outlet, NavLink } from 'react-router-dom'

export default function App() {
  return (
    <div style={{ fontFamily: 'ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell' }}>
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 20px', borderBottom: '1px solid #eee', position: 'sticky', top: 0, background: 'white', zIndex: 10 }}>
        <h1 style={{ margin: 0, fontSize: 18 }}>My Tech Notes</h1>
        <nav style={{ display: 'flex', gap: 12 }}>
          <NavLink to="/" style={({isActive}) => ({ textDecoration: 'none', color: isActive ? '#111' : '#666' })}>Home</NavLink>
          <a href="https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>" rel="noreferrer" target="_blank" style={{ textDecoration: 'none', color: '#666' }}>GitHub</a>
        </nav>
      </header>

      <main style={{ maxWidth: 860, margin: '24px auto', padding: '0 20px' }}>
        <Outlet />
      </main>

      <footer style={{ maxWidth: 860, margin: '32px auto', padding: '12px 20px', color: '#888', borderTop: '1px solid #eee' }}>
        Built with React + Vite · Deployed on GitHub Pages
      </footer>
    </div>
  )
}