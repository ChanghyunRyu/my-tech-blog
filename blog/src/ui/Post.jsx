import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import posts from '../posts.js'

// HTML 이스케이프 헬퍼 함수
const escapeHtml = (str) => {
  if (typeof str !== 'string') {
    str = String(str || '');
  }
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return str.replace(/[&<>"']/g, (m) => map[m]);
};

// markdown-it 인스턴스 생성 (컴포넌트 외부에서 한 번만 생성)
const createMarkdownRenderer = () => {
  const md = new MarkdownIt({
    html: true,
    linkify: true,
    typographer: true,
    breaks: false, // 줄바꿈을 <br>로 변환하지 않음
    highlight: function (str, lang) {
      // 입력 검증
      if (str == null) {
        return '<pre class="hljs"><code></code></pre>';
      }
      
      if (typeof str !== 'string') {
        str = String(str);
      }
      
      // 언어가 지정되고 highlight.js가 지원하는 경우
      if (lang && typeof lang === 'string' && hljs.getLanguage(lang)) {
        try {
          const highlighted = hljs.highlight(str, { 
            language: lang, 
            ignoreIllegals: true 
          }).value;
          return '<pre class="hljs"><code class="language-' + escapeHtml(lang) + '">' + highlighted + '</code></pre>';
        } catch (err) {
          console.warn('Highlight error for language', lang, ':', err);
          // 에러 발생 시 이스케이프된 텍스트 반환
          return '<pre class="hljs"><code>' + escapeHtml(str) + '</code></pre>';
        }
      }
      
      // 언어가 없거나 인식하지 못한 경우 - 이스케이프만 수행
      return '<pre class="hljs"><code>' + escapeHtml(str) + '</code></pre>';
    }
  });
  
  return md;
};

const md = createMarkdownRenderer();

export default function Post() {
  const { slug } = useParams()
  const meta = posts.find(p => p.slug === slug)
  const [html, setHtml] = useState('<p>Loading...</p>')

  useEffect(() => {
    async function load() {
      if (!meta) {
        setHtml('<p>Post metadata not found.</p>')
        return
      }
      
      try {
        const folder = meta.folder || 'tech-blog-review'
        // BASE_URL은 이미 /my-tech-blog/를 포함하므로 posts/로 시작
        const url = `${import.meta.env.BASE_URL}posts/${folder}/${slug}.md`
        
        console.log('Fetching post from:', url)
        
        const res = await fetch(url)
        
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`)
        }
        
        let text = await res.text()
        
        // 문자열이 아닌 경우 처리
        if (typeof text !== 'string') {
          text = String(text || '')
        }
        
        // 빈 문자열 체크
        if (!text || text.trim().length === 0) {
          throw new Error('Post content is empty')
        }
        
        // ~~~ 코드 블록을 ```로 변환 (일부 마크다운에서 사용하는 문법)
        // 더 안전한 정규식 사용 - replace 호출 전에 문자열 확인
        if (typeof text === 'string' && text.replace) {
          text = text.replace(/^~~~(\w*)\r?\n/gm, '```$1\n')
          text = text.replace(/^~~~\s*$/gm, '```')
        } else {
          // replace가 없는 경우 (이론적으로 발생하지 않아야 하지만 안전장치)
          console.warn('Text is not a valid string for replace operation')
          text = String(text)
        }
        
        // markdown-it으로 파싱
        try {
          // 최종 검증: text가 유효한 문자열인지 확인
          if (typeof text !== 'string') {
            throw new Error(`Invalid text type: ${typeof text}. Expected string.`)
          }
          
          if (!text || text.length === 0) {
            throw new Error('Text is empty after processing')
          }
          
          // markdown-it 렌더링
          const html = md.render(text)
          
          if (!html || typeof html !== 'string') {
            throw new Error(`Markdown rendering returned invalid result: ${typeof html}`)
          }
          
          setHtml(html)
        } catch (renderError) {
          console.error('Markdown rendering error:', renderError)
          console.error('Text type:', typeof text)
          console.error('Text length:', text?.length)
          console.error('Text preview:', text?.substring(0, 100))
          throw new Error(`Markdown parsing failed: ${renderError.message}`)
        }
      } catch (e) {
        console.error('Error loading post:', e)
        const errorMessage = e instanceof Error ? e.message : String(e)
        setHtml(`<div style="padding: 20px; border: 1px solid #dc2626; border-radius: 6px; background-color: #fef2f2;">
          <p style="color: #dc2626; font-weight: 600; margin: 0 0 8px 0;">Post not found</p>
          <p style="color: #991b1b; margin: 0; font-size: 14px;">Error: ${errorMessage}</p>
          <p style="color: #991b1b; margin: 8px 0 0 0; font-size: 12px;">Please check the browser console for more details.</p>
        </div>`)
      }
    }
    
    load()
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
        .markdown-body pre.hljs {
          padding: 16px;
          overflow: auto;
          background-color: #f6f8fa;
          border: 1px solid #d0d7de;
        }
        .markdown-body pre code {
          display: block;
          padding: 0;
          margin: 0;
          overflow: visible;
          line-height: inherit;
          word-wrap: normal;
          background-color: transparent;
          border: 0;
          font-size: 100%;
        }
        .markdown-body pre.hljs code {
          display: block;
          padding: 0;
          margin: 0;
          word-break: normal;
          white-space: pre;
          background: transparent;
          color: inherit;
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
        .markdown-body strong {
          font-weight: 600;
        }
        .markdown-body em {
          font-style: italic;
        }
      `}</style>
    </article>
  )
}