import React, { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import posts from '../posts.js'

const POSTS_PER_PAGE = 5

export default function Home() {
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)

  // 카테고리별 필터링
  const filteredPosts = useMemo(() => {
    const filtered = selectedCategory === 'all' 
      ? posts 
      : posts.filter(p => p.category === selectedCategory)
    
    // 날짜순 정렬 (최신순)
    return filtered.sort((a, b) => new Date(b.date) - new Date(a.date))
  }, [selectedCategory])

  // 페이지네이션
  const totalPages = Math.ceil(filteredPosts.length / POSTS_PER_PAGE)
  const currentPosts = filteredPosts.slice(
    (currentPage - 1) * POSTS_PER_PAGE,
    currentPage * POSTS_PER_PAGE
  )

  // 카테고리 변경 시 페이지를 1로 리셋
  const handleCategoryChange = (category) => {
    setSelectedCategory(category)
    setCurrentPage(1)
  }

  const getCategoryLabel = (category) => {
    switch (category) {
      case 'daily': return '기술 블로그'
      case 'weekly': return 'IT 서적'
      default: return '전체'
    }
  }

  const getCategoryColor = (category) => {
    switch (category) {
      case 'daily': return '#2563eb'
      case 'weekly': return '#dc2626'
      default: return '#666'
    }
  }

  return (
    <div>
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ margin: '8px 0 4px' }}>Daily/Weekly Notes</h2>
        <p style={{ color: '#666' }}>읽은 기술 블로그와 IT 서적을 정리한 내용입니다.</p>
      </section>

      {/* 카테고리 필터 */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {['all', 'daily', 'weekly'].map(category => (
            <button
              key={category}
              onClick={() => handleCategoryChange(category)}
              style={{
                padding: '6px 12px',
                border: selectedCategory === category ? '2px solid #2563eb' : '1px solid #ddd',
                borderRadius: 20,
                background: selectedCategory === category ? '#f0f9ff' : 'white',
                color: selectedCategory === category ? '#2563eb' : '#666',
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: selectedCategory === category ? '600' : '400'
              }}
            >
              {getCategoryLabel(category)} ({category === 'all' ? posts.length : posts.filter(p => p.category === category).length})
            </button>
          ))}
        </div>
      </div>

      {/* 글 목록 */}
      <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: 12 }}>
        {currentPosts.map(p => (
          <li key={p.slug} style={{ border: '1px solid #eee', borderRadius: 12, padding: '14px 16px' }}>
            <Link to={`/post/${p.slug}`} style={{ color: '#111', textDecoration: 'none' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <h3 style={{ margin: 0, fontSize: 18, flex: 1 }}>{p.title}</h3>
                <span style={{
                  padding: '2px 8px',
                  borderRadius: 12,
                  fontSize: 12,
                  fontWeight: '500',
                  backgroundColor: getCategoryColor(p.category) + '20',
                  color: getCategoryColor(p.category)
                }}>
                  {getCategoryLabel(p.category)}
                </span>
              </div>
              <div style={{ fontSize: 13, color: '#777' }}>{p.date} · {p.tags.join(', ')}</div>
              <p style={{ marginTop: 8, color: '#444' }}>{p.summary}</p>
            </Link>
          </li>
        ))}
      </ul>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div style={{ 
          marginTop: 32, 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          gap: 8 
        }}>
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            style={{
              padding: '8px 12px',
              border: '1px solid #ddd',
              borderRadius: 6,
              background: currentPage === 1 ? '#f5f5f5' : 'white',
              color: currentPage === 1 ? '#999' : '#333',
              cursor: currentPage === 1 ? 'not-allowed' : 'pointer'
            }}
          >
            이전
          </button>
          
          <span style={{ margin: '0 16px', color: '#666' }}>
            {currentPage} / {totalPages}
          </span>
          
          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            style={{
              padding: '8px 12px',
              border: '1px solid #ddd',
              borderRadius: 6,
              background: currentPage === totalPages ? '#f5f5f5' : 'white',
              color: currentPage === totalPages ? '#999' : '#333',
              cursor: currentPage === totalPages ? 'not-allowed' : 'pointer'
            }}
          >
            다음
          </button>
        </div>
      )}

      {/* 글이 없을 때 */}
      {currentPosts.length === 0 && (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px 20px', 
          color: '#666' 
        }}>
          {getCategoryLabel(selectedCategory)} 카테고리에 글이 없습니다.
        </div>
      )}
    </div>
  )
}