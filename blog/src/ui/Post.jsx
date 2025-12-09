import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { marked } from 'marked'
import posts from '../posts.js'

export default function Post() {
  const { slug } = useParams()
  const meta = posts.find(p => p.slug === slug)
  const [html, setHtml] = useState('<p>Loading...</p>')

  useEffect(() => {
    async function load() {
      try {
        const folder = meta?.folder || 'tech-blog-review'
        const res = await fetch(`${import.meta.env.BASE_URL}posts/${folder}/${slug}.md`)
        const text = await res.text()
        setHtml(marked.parse(text))
      } catch (e) {
        setHtml('<p>Post not found.</p>')
      }
    }
    if (meta) {
      load()
    }
  }, [slug, meta])

  if (!meta) return <p>Post not found.</p>

  return (
    <article>
      <h2 style={{ marginBottom: 4 }}>{meta.title}</h2>
      <div style={{ color: '#777', marginBottom: 16 }}>{meta.date} · {meta.tags.join(', ')}</div>
      <div dangerouslySetInnerHTML={{ __html: html }} />
    </article>
  )
}