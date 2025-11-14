import React from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import App from './ui/App.jsx'
import Home from './ui/Home.jsx'
import Post from './ui/Post.jsx'
import NotFound from './ui/NotFound.jsx'

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Home /> },
      { path: 'post/:slug', element: <Post /> },
      { path: '*', element: <NotFound /> }
    ]
  }
], {
  // GitHub Pages SPA 404 support handled by 404.html fallback (added below)
  basename: '/my-tech-blog/'
})

const root = createRoot(document.getElementById('root'))
root.render(<RouterProvider router={router} />)