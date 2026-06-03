import { useState } from 'react'

const API_BASE = 'http://localhost:8000'

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [text, setText] = useState('')
  const [textTitle, setTextTitle] = useState('')
  const [imageFile, setImageFile] = useState(null)
  const [imageTitle, setImageTitle] = useState('')
  const [status, setStatus] = useState('Ready')

  const handleQuery = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setStatus('Searching...')
    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 5 }),
      })
      const data = await response.json()
      setResults(data.results || [])
      setStatus('Search complete')
    } catch (error) {
      setStatus('Error searching')
      console.error(error)
    }
  }

  const handleTextIngest = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    setStatus('Indexing text...')
    try {
      await fetch(`${API_BASE}/ingest/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text, title: textTitle || 'Text document' }),
      })
      setText('')
      setTextTitle('')
      setStatus('Text indexed')
    } catch (error) {
      setStatus('Error indexing text')
      console.error(error)
    }
  }

  const handleImageIngest = async (e) => {
    e.preventDefault()
    if (!imageFile) return
    setStatus('Indexing image...')
    const form = new FormData()
    form.append('file', imageFile)
    form.append('title', imageTitle || imageFile.name)
    try {
      await fetch(`${API_BASE}/ingest/image`, {
        method: 'POST',
        body: form,
      })
      setImageFile(null)
      setImageTitle('')
      setStatus('Image indexed')
      document.getElementById('image-file-input').value = ''
    } catch (error) {
      setStatus('Error indexing image')
      console.error(error)
    }
  }

  return (
    <div className="app-shell">
      <header>
        <h1>AI-Powered Search Engine</h1>
        <p>Index text and image documents, then ask a question.</p>
      </header>

      <section className="panel">
        <h2>Search</h2>
        <form onSubmit={handleQuery}>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask something..."
            rows={3}
          />
          <button type="submit">Search</button>
        </form>
        <div className="results">
          {results.length === 0 ? <p>No results yet.</p> : (
            <ul>
              {results.map((result) => (
                <li key={result.id}>
                  <strong>{result.metadata.title || result.id}</strong>
                  <p>type: {result.metadata.type || 'unknown'}</p>
                  <p>score: {result.score.toFixed(4)}</p>
                  {result.metadata.content && <p>{result.metadata.content.slice(0, 200)}...</p>}
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="panel split">
        <div>
          <h2>Index text</h2>
          <form onSubmit={handleTextIngest}>
            <input
              value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)}
              placeholder="Document title"
            />
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste document text here"
              rows={5}
            />
            <button type="submit">Add text</button>
          </form>
        </div>

        <div>
          <h2>Index image</h2>
          <form onSubmit={handleImageIngest}>
            <input
              id="image-file-input"
              type="file"
              accept="image/*"
              onChange={(e) => setImageFile(e.target.files?.[0] || null)}
            />
            <input
              value={imageTitle}
              onChange={(e) => setImageTitle(e.target.value)}
              placeholder="Image title or caption"
            />
            <button type="submit">Add image</button>
          </form>
        </div>
      </section>

      <footer>{status}</footer>
    </div>
  )
}

export default App
