import { useEffect, useRef, useState } from 'react'
import { fetchCities, fetchForeignBorn, fetchMapStats } from './api/cities'
import { sendChat } from './api/chat'
import './App.css'
import PerCapitaComparison from './components/PerCapitaComparison'
import CityProfile from './components/CityProfile'
import CountryOrigins from './components/CountryOrigins'
import MapView from './components/MapView'


export default function App() {
  const [activeTab, setActiveTab] = useState('Overview')
  const [cities, setCities] = useState([])
  const [selectedCities, setSelectedCities] = useState([])
  const [foreignBorn, setForeignBorn] = useState([])
  const [mapStats, setMapStats] = useState([])
  const [loading, setLoading] = useState(true)
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatOpen, setChatOpen] = useState(false)
  const [chatMinimized, setChatMinimized] = useState(false)
  const [chatPos, setChatPos] = useState(() => ({ top: 48, left: window.innerWidth - 24 - 380 }))
  const dragRef = useRef(null)
  const reopenRef = useRef(null)
  const didDragRef = useRef(false)
  const chatEndRef = useRef(null)

  const makeDragHandler = (ref) => (e) => {
    e.preventDefault()
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const offsetX = e.clientX - rect.left
    const offsetY = e.clientY - rect.top
    didDragRef.current = false

    const onMove = (mv) => {
      didDragRef.current = true
      setChatPos({ top: mv.clientY - offsetY, left: mv.clientX - offsetX })
    }
    const onUp = () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }

  const handleDragStart = makeDragHandler(dragRef)
  const handleReopenDragStart = makeDragHandler(reopenRef)

  useEffect(() => {
    fetchCities().then(data => {
      setCities(data)
      setLoading(false)
    })
  }, [])

  useEffect(() => {
    fetchMapStats().then(setMapStats)
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages, chatLoading])

  useEffect(() => {
    if (selectedCities.length === 0) {
      fetchForeignBorn().then(setForeignBorn)
    } else {
      Promise.all(selectedCities.map(c => fetchForeignBorn({ city: c })))
        .then(results => setForeignBorn(results.flat()))
    }
  }, [selectedCities])

  const toggleCity = (city) => {
    setSelectedCities(prev =>
      prev.includes(city) ? prev.filter(c => c !== city) : [...prev, city]
    )
  }

  const sorted = [...foreignBorn].sort((a, b) => b.fb_pct - a.fb_pct)

  if (loading) return <div className="loading">Loading...</div>

  return (
    <div className="app">
      <header className="header">
        <h1>Gateway Cities: Foreign-Born Population</h1>
        <p>ACS 5-year estimates (2020–2024 period) · Massachusetts</p>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <h3>Filter Cities</h3>
          <div className="city-type-group">
            <p className="type-label gateway">● Gateway Cities</p>
            <p className="type-label comparison">● Comparison Cities</p>
            <p className="type-label benchmark">● Benchmark</p>
          </div>
          <div className="city-list">
            {cities.map(c => (
              <button
                key={c.city}
                className={`city-btn ${c.city_type} ${selectedCities.includes(c.city) ? 'active' : ''}`}
                onClick={() => toggleCity(c.city)}
              >
                {c.city}
              </button>
            ))}
          </div>
          {selectedCities.length > 0 && (
            <button className="clear-btn" onClick={() => setSelectedCities([])}>
              Clear selection
            </button>
          )}
        </aside>

        <main className="main">
          <div className="tabs">
            {['Overview', 'Per Capita Comparison', 'City Profile', 'Origins', 'Map'].map(tab => (
              <button
                key={tab}
                className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </button>
            ))}
          </div>

          {activeTab === 'Overview' && (
            <>
              <div className="overview-header">
                <div>
                  <h2>
                    Foreign-Born % of Population
                    {selectedCities.length > 0 ? ` — ${selectedCities.join(', ')}` : ' — All Cities'}
                  </h2>
                  <p className="source-note">
                    Source: American Community Survey 5-year estimates, most recent period
                  </p>
                </div>
                <button
                  className="download-btn"
                  onClick={() => {
                    const csvHeader = ['city', 'city_type', 'fb_pct'].join(',')
                    const rows = sorted.map(d =>
                      [d.city, d.city_type, d.fb_pct?.toFixed(3) ?? ''].join(',')
                    )
                    const blob = new Blob([csvHeader + '\n' + rows.join('\n')], { type: 'text/csv' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = 'foreign_born_overview.csv'
                    a.click()
                    URL.revokeObjectURL(url)
                  }}
                >
                  Download CSV
                </button>
              </div>

              <div className="bar-chart">
                {sorted.map(d => (
                  <div key={d.city} className="bar-row">
                    <span className="bar-label">{d.city}</span>
                    <div className="bar-track">
                      <div
                        className={`bar-fill ${d.city_type}`}
                        style={{ width: `${Math.min(d.fb_pct, 60) / 60 * 100}%` }}
                      />
                    </div>
                    <span className="bar-value">{d.fb_pct?.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </>
          )}

          {activeTab === 'Per Capita Comparison' && (
            <PerCapitaComparison
              selectedCities={selectedCities}
              allCities={cities}
            />
          )}

          {activeTab === 'City Profile' && (
            <CityProfile
              selectedCities={selectedCities}
            />
          )}

          {activeTab === 'Origins' && (
            <CountryOrigins selectedCities={selectedCities} />
          )}

          {activeTab === 'Map' && (
            <>
              <h2>Gateway Cities Map</h2>
              <p style={{ marginBottom: '12px', color: '#888', fontSize: '0.9rem' }}>
                Loaded map rows: {mapStats.length}
              </p>
              <MapView
                stats={mapStats}
                selectedCities={selectedCities}
                onCityClick={toggleCity}
              />
            </>
          )}
        </main>
      </div>

      {/* Floating chat window */}
      {chatOpen && (
        <div
          ref={dragRef}
          className={`chat-float-panel ${chatMinimized ? 'minimized' : ''}`}
          style={{ top: chatPos.top, left: chatPos.left, right: 'auto' }}
        >
          <div className="chat-float-header" onMouseDown={handleDragStart}>
            <div className="chat-float-title">
              <span className="chat-float-icon">💬</span>
              <span>ACS Assistant</span>
            </div>
            <div className="chat-float-controls">
              <button
                className="chat-ctrl-btn"
                title={chatMinimized ? 'Expand' : 'Minimize'}
                onClick={() => setChatMinimized(v => !v)}
              >
                {chatMinimized ? '▲' : '▼'}
              </button>
              <button
                className="chat-ctrl-btn"
                title="Close"
                onClick={() => { setChatOpen(false); setChatMinimized(false) }}
              >
                ✕
              </button>
            </div>
          </div>

          {!chatMinimized && (
            <>
              <div className="chat-messages">
                {chatMessages.length === 0 && (
                  <div className="chat-welcome">
                    <p>Ask anything about Massachusetts gateway cities.</p>
                    <p className="chat-welcome-hint">e.g. "What share of Boston residents are foreign-born?" or "Compare Lowell and Worcester."</p>
                  </div>
                )}
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`chat-bubble ${msg.role}`}>
                    <span className="chat-bubble-text">{msg.content}</span>
                  </div>
                ))}
                {chatLoading && (
                  <div className="chat-bubble assistant">
                    <span className="chat-typing">
                      <span className="chat-typing-dot" />
                      <span className="chat-typing-dot" />
                      <span className="chat-typing-dot" />
                    </span>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              <div className="chat-input-wrap">
                <textarea
                  className="chat-input"
                  rows={1}
                  placeholder="Ask a question…"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      if (chatInput.trim() && !chatLoading) {
                        const q = chatInput.trim()
                        setChatMessages((prev) => [...prev, { role: 'user', content: q }])
                        setChatInput('')
                        setChatLoading(true)
                        sendChat(q)
                          .then((data) => {
                            setChatMessages((prev) => [...prev, { role: 'assistant', content: data.answer || '' }])
                          })
                          .catch(() => {
                            setChatMessages((prev) => [...prev, { role: 'assistant', content: 'Chat request failed. Make sure the backend is running.' }])
                          })
                          .finally(() => setChatLoading(false))
                      }
                    }
                  }}
                />
                <button
                  className="chat-send-btn"
                  disabled={chatLoading || !chatInput.trim()}
                  onClick={async () => {
                    const q = chatInput.trim()
                    if (!q) return
                    setChatMessages((prev) => [...prev, { role: 'user', content: q }])
                    setChatInput('')
                    setChatLoading(true)
                    try {
                      const data = await sendChat(q)
                      setChatMessages((prev) => [...prev, { role: 'assistant', content: data.answer || '' }])
                    } catch (err) {
                      setChatMessages((prev) => [...prev, { role: 'assistant', content: 'Chat request failed. Make sure the backend is running.' }])
                    } finally {
                      setChatLoading(false)
                    }
                  }}
                >
                  ➤
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Reopen button shown when chat is closed */}
      {!chatOpen && (
        <button
          ref={reopenRef}
          className="chat-reopen-btn"
          style={{ top: chatPos.top, left: chatPos.left, right: 'auto' }}
          onMouseDown={handleReopenDragStart}
          onClick={() => { if (!didDragRef.current) { setChatOpen(true); setChatMinimized(false) } }}
          title="Open ACS Assistant"
        >
          <span className="chat-reopen-icon">💬</span>
          <span className="chat-reopen-label">ACS Assistant</span>
        </button>
      )}
    </div>
  )
}
