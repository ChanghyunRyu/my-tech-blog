import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import posts from '../posts.js'

// marked 설정: 코드 블록에 구문 강조 적용
const renderer = new marked.Renderer()
renderer.code = (code, language) => {
  const validLanguage = hljs.getLanguage(language || '') ? language : 'plaintext'
  const highlighted = hljs.highlight(code, { language: validLanguage }).value
  return `<pre><code class="hljs language-${validLanguage}">${highlighted}</code></pre>`
}

marked.setOptions({
  renderer,
  breaks: true, // 줄바꿈을 <br>로 변환
  gfm: true, // GitHub Flavored Markdown 활성화
})

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
    <article style={{ lineHeight: 1.7 }}>
      <h2 style={{ marginBottom: 4 }}>{meta.title}</h2>
      <div style={{ color: '#777', marginBottom: 16 }}>{meta.date} · {meta.tags.join(', ')}</div>
      <div 
        dangerouslySetInnerHTML={{ __html: html }}
        style={{
          color: '#24292f',
          fontSize: '16px'
        }}
        className="markdown-body"
      />
      <style>{`
        .markdown-body {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        }
        .markdown-body h1,
        .markdown-body h2,
        .markdown-body h3,
        .markdown-body h4,
        .markdown-body h5,
        .markdown-body h6 {
          margin-top: 24px;
          margin-bottom: 16px;
          font-weight: 600;
          line-height: 1.25;
        }
        .markdown-body h1 {
          font-size: 2em;
          border-bottom: 1px solid #d0d7de;
          padding-bottom: 0.3em;
        }
        .markdown-body h2 {
          font-size: 1.5em;
          border-bottom: 1px solid #d0d7de;
          padding-bottom: 0.3em;
        }
        .markdown-body h3 {
          font-size: 1.25em;
        }
        .markdown-body p {
          margin-bottom: 16px;
        }
        .markdown-body ul,
        .markdown-body ol {
          margin-bottom: 16px;
          padding-left: 2em;
        }
        .markdown-body li {
          margin-bottom: 4px;
        }
        .markdown-body code {
          padding: 0.2em 0.4em;
          margin: 0;
          font-size: 85%;
          background-color: rgba(175, 184, 193, 0.2);
          border-radius: 6px;
          font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
        }
        .markdown-body pre {
          padding: 16px;
          overflow: auto;
          font-size: 85%;
          line-height: 1.45;
          background-color: #f6f8fa;
          border-radius: 6px;
          margin-bottom: 16px;
          border: 1px solid #d0d7de;
        }
        .markdown-body pre code {
          display: inline;
          max-width: auto;
          padding: 0;
          margin: 0;
          overflow: visible;
          line-height: inherit;
          word-wrap: normal;
          background-color: transparent;
          border: 0;
        }
        .markdown-body pre > code {
          display: block;
          padding: 0;
          margin: 0;
          word-break: normal;
          white-space: pre;
          background: transparent;
        }
        .markdown-body blockquote {
          padding: 0 1em;
          color: #656d76;
          border-left: 0.25em solid #d0d7de;
          margin: 0 0 16px 0;
        }
        .markdown-body hr {
          height: 0.25em;
          padding: 0;
          margin: 24px 0;
          background-color: #d0d7de;
          border: 0;
        }
        .markdown-body table {
          border-spacing: 0;
          border-collapse: collapse;
          display: block;
          width: max-content;
          max-width: 100%;
          overflow: auto;
          margin-bottom: 16px;
        }
        .markdown-body table th,
        .markdown-body table td {
          padding: 6px 13px;
          border: 1px solid #d0d7de;
        }
        .markdown-body table th {
          font-weight: 600;
          background-color: #f6f8fa;
        }
        .markdown-body table tr {
          background-color: #ffffff;
          border-top: 1px solid #c6cbd1;
        }
        .markdown-body table tr:nth-child(2n) {
          background-color: #f6f8fa;
        }
      `}</style>
    </article>
  )
}