import { useMemo, useState } from 'react'

const API_BASE = 'http://localhost:8000'

function imageUrl(metadata) {
  if (metadata?.type !== 'image' || !metadata.filename) return null
  const safePath = metadata.filename.split('/').map(encodeURIComponent).join('/')
  return `${API_BASE}/data/images/${safePath}`
}

function ResultCard({ result }) {
  const metadata = result.metadata || {}
  const url = imageUrl(metadata)
  const preview = metadata.content || metadata.caption || 'No preview available.'

  return (
    <article className="result-card">
      {url && <img className="result-image" src={url} alt={metadata.title || metadata.filename} />}
      <div>
        <div className="result-top">
          <strong>{metadata.title || result.id}</strong>
          <span>{metadata.type || 'unknown'}</span>
        </div>
        <p>{preview.slice(0, 220)}{preview.length > 220 ? '...' : ''}</p>
        <small>Score: {Number(result.score).toFixed(3)} | Source: {metadata.source || metadata.filename || result.id}</small>
      </div>
    </article>
  )
}

function getAnswerSource(answer, answerMeta) {
  if (answerMeta.mode === 'retrieval_fallback') {
    return {
      label: 'Retrieved data only',
      detail: 'Groq was not available, so this answer was built directly from your indexed results.',
      tone: 'warning',
    }
  }

  if (answer.startsWith('I could not find this in the indexed documents.')) {
    return {
      label: 'Outside indexed data',
      detail: 'This was not found in your retrieved documents, so Groq gave a general answer.',
      tone: 'notice',
    }
  }

  return {
    label: 'Aarav RAG + Groq',
    detail: 'Groq generated this answer using your retrieved FAISS context.',
    tone: 'success',
  }
}

function App() {
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [answerMeta, setAnswerMeta] = useState({ mode: '', warning: '' })
  const [results, setResults] = useState([])
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState('')
  const [imageMessage, setImageMessage] = useState('')
  const [history, setHistory] = useState([])
  const [status, setStatus] = useState('Ready')

  const imageResults = useMemo(
    () => results.filter((result) => result.metadata?.type === 'image'),
    [results],
  )
  const answerSource = answer ? getAnswerSource(answer, answerMeta) : null

  const addHistory = (label, type) => {
    setHistory((items) => [{ label, type, time: new Date().toLocaleTimeString() }, ...items].slice(0, 6))
  }

  const handleAsk = async (event) => {
    event.preventDefault()
    if (!query.trim()) return

    setStatus('Searching your RAG...')
    setAnswer('')
    setAnswerMeta({ mode: '', warning: '' })
    setImageMessage('')

    try {
      const response = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 5 }),
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Backend request failed')
      }

      setAnswer(data.answer || 'No answer returned.')
      setAnswerMeta({ mode: data.mode || '', warning: data.warning || '' })
      setResults(data.sources || [])
      addHistory(query, 'Text query')
      setStatus(data.mode === 'retrieval_fallback' ? 'Retrieved answer ready' : 'Groq answer ready')
    } catch (error) {
      setStatus(error.message || 'Backend or Groq error')
      console.error(error)
    }
  }

  const handleImageChange = (event) => {
    const file = event.target.files?.[0]
    setImageFile(file || null)
    setImagePreview(file ? URL.createObjectURL(file) : '')
  }

  const handleImageSearch = async () => {
    if (!imageFile) return

    setStatus('Finding related images...')
    setAnswer('')
    setAnswerMeta({ mode: '', warning: '' })
    setImageMessage('')

    const form = new FormData()
    form.append('file', imageFile)
    form.append('top_k', '5')

    try {
      const response = await fetch(`${API_BASE}/query/image`, {
        method: 'POST',
        body: form,
      })
      const data = await response.json()

      setResults(data.results || [])
      addHistory(imageFile.name, 'Image query')
      setImageMessage(data.message || '')
      setStatus(data.message ? 'No confident image match' : 'Related images found')
    } catch (error) {
      setStatus('Image search error')
      console.error(error)
    }
  }

  const handleClear = () => {
    setQuery('')
    setAnswer('')
    setAnswerMeta({ mode: '', warning: '' })
    setResults([])
    setImageFile(null)
    setImagePreview('')
    setImageMessage('')
    setStatus('Ready')
    const input = document.getElementById('image-query')
    if (input) input.value = ''
  }

  const handleClearHistory = () => {
    setHistory([])
  }

  const handleDeleteHistoryItem = (itemIndex) => {
    setHistory((items) => items.filter((_, index) => index !== itemIndex))
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Multimodal RAG Demo</p>
          <h1>AI POWERED RAG Search Engine </h1>
          <p className="subtitle">
            Ask questions from your indexed text and search related images with CLIP, FAISS, and Groq.
          </p>
        </div>
        <div className="status-pill">{status}</div>
      </section>

      <section className="workspace">
        <div className="main-panel">
          <form className="ask-box" onSubmit={handleAsk}>
            <label htmlFor="query">Ask anything from your data</label>
            <textarea
              id="query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Example: What is RAG? What is the secret project code?"
              rows={4}
            />
            <div className="actions">
              <button type="submit">Search</button>
              <button type="button" className="secondary" onClick={handleClear}>Clear</button>
            </div>
          </form>

          <div className="upload-box">
            <div>
              <label htmlFor="image-query">Upload image query</label>
              <p>Upload an image to find visually related indexed images.</p>
            </div>
            <input id="image-query" type="file" accept="image/*" onChange={handleImageChange} />
            {imagePreview && <img className="preview-image" src={imagePreview} alt="Uploaded preview" />}
            <button type="button" onClick={handleImageSearch} disabled={!imageFile}>Find Related Images</button>
          </div>

          {answer && (
            <section className="answer-panel">
              <div className="answer-header">
                <h2>Answer</h2>
                {answerSource && <span className={`source-badge ${answerSource.tone}`}>{answerSource.label}</span>}
              </div>
              {answerSource && <p className="answer-source">{answerSource.detail}</p>}
              {answerMeta.warning && <p className="answer-warning">{answerMeta.warning}</p>}
              <p>{answer}</p>
            </section>
          )}

          <section className="results-panel">
            <div className="section-heading">
              <h2>Sources</h2>
              <span>{results.length} results</span>
            </div>
            {imageMessage ? (
              <p className="empty match-warning">{imageMessage}</p>
            ) : results.length === 0 ? (
              <p className="empty">No results yet. Ask a question or upload an image.</p>
            ) : (
              <div className="result-list">
                {results.map((result) => <ResultCard key={result.id} result={result} />)}
              </div>
            )}
          </section>
        </div>

        <aside className="side-panel">
          <h2>Related Images</h2>
          {imageMessage ? (
            <p className="empty match-warning">{imageMessage}</p>
          ) : imageResults.length === 0 ? (
            <p className="empty">Image matches will appear here.</p>
          ) : (
            <div className="image-grid">
              {imageResults.map((result) => {
                const metadata = result.metadata || {}
                return (
                  <div className="image-tile" key={result.id}>
                    <img src={imageUrl(metadata)} alt={metadata.title || metadata.filename} />
                    <span>{metadata.title || metadata.filename}</span>
                  </div>
                )
              })}
            </div>
          )}

          <div className="side-heading">
            <h2>History</h2>
            {history.length > 0 && (
              <button type="button" className="tiny-button" onClick={handleClearHistory}>Clear</button>
            )}
          </div>
          {history.length === 0 ? (
            <p className="empty">Your recent searches will show here.</p>
          ) : (
            <ul className="history-list">
              {history.map((item, index) => (
                <li key={`${item.label}-${index}`}>
                  <div>
                    <strong>{item.label}</strong>
                    <span>{item.type} | {item.time}</span>
                  </div>
                  <button
                    type="button"
                    className="delete-history-button"
                    onClick={() => handleDeleteHistoryItem(index)}
                    aria-label={`Delete ${item.label} from history`}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>
      </section>
    </main>
  )
}

export default App
