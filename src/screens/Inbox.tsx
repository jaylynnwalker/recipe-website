import { useState, type FormEvent } from 'react'
import type { InboxRecord } from '../api'

export function Inbox({ items, onImportUrl, onImportPhotos, onReview, onRetry, onAiExtract, onDelete }: {
  items: InboxRecord[]
  onImportUrl: (url: string) => Promise<void>
  onImportPhotos: (files: File[]) => Promise<void>
  onReview: (item: InboxRecord) => void
  onRetry: (item: InboxRecord) => Promise<void>
  onAiExtract: (item: InboxRecord) => Promise<void>
  onDelete: (item: InboxRecord) => Promise<void>
}) {
  const [url, setUrl] = useState('')
  const [photos, setPhotos] = useState<File[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submitUrl = async (event: FormEvent) => { event.preventDefault(); if (!url.trim()) return; setBusy(true); setError(''); try { await onImportUrl(url.trim()); setUrl('') } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to import URL') } finally { setBusy(false) } }
  const submitPhotos = async (event: FormEvent) => { event.preventDefault(); if (!photos.length) return; setBusy(true); setError(''); try { await onImportPhotos(photos); setPhotos([]) } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save photos') } finally { setBusy(false) } }

  return <div className="page"><header className="page-header"><div><p className="eyebrow">Capture something delicious</p><h1>Recipe Inbox</h1><p>Save it now, review the details when you’re ready.</p></div></header>
    {error && <p className="data-error" role="alert">{error}</p>}
    <div className="import-grid">
      <form className="import-panel" onSubmit={submitUrl}><span>↗</span><div><h2>From a Link</h2><p>Recipe page or public YouTube URL</p><label>Recipe URL<input type="url" required placeholder="https://…" value={url} onChange={(event) => setUrl(event.target.value)} /></label><button className="primary" disabled={busy}>Save & extract</button></div></form>
      <form className="import-panel" onSubmit={submitPhotos}><span>▧</span><div><h2>From Photos</h2><p>One or more cookbook pages or handwritten cards. Photos are saved for manual transcription; AI reading is not enabled.</p><label>Recipe photos<input type="file" required multiple accept="image/jpeg,image/png,image/webp" onChange={(event) => setPhotos(Array.from(event.target.files ?? []))} /></label><button className="primary" disabled={busy || !photos.length}>Save {photos.length || ''} photo{photos.length === 1 ? '' : 's'}</button></div></form>
    </div>
    <section className="queue"><div className="section-heading"><div><p className="eyebrow">Saved for review</p><h2>Inbox Queue</h2></div><span className="queue-count">{items.length} items</span></div>
      {items.length ? items.map((item) => <article key={item.id}><div className="queue-thumb">{item.sourceType === 'photo' ? (item.assets[0] ? <img src={item.assets[0].url} alt="First uploaded recipe page" /> : '▧') : '↗'}</div><div><span className={`queue-status ${statusClass(item.status)}`}>{item.status}</span><h3>{item.title}</h3><p>{item.sourceType === 'photo' ? `${item.assets.length} original photo${item.assets.length === 1 ? '' : 's'}` : item.sourceUrl}</p>{item.duplicateRecipeId && <small className="duplicate-warning">Potential duplicate in your recipe library</small>}{item.errorMessage && <small className="import-message">{item.errorMessage}</small>}</div><div className="queue-actions">{item.status !== 'Saved' && <button className="secondary" onClick={() => onReview(item)}>{item.status === 'Failed' ? 'Enter manually' : 'Review'}</button>}{item.status !== 'Saved' && <button className="secondary" onClick={() => void onAiExtract(item)}>Extract with AI</button>}{item.status === 'Failed' && item.sourceUrl && <button className="secondary" onClick={() => void onRetry(item)}>Retry without AI</button>}<button className="remove" onClick={() => void onDelete(item)}>Delete</button></div></article>) : <div className="empty-state"><span>▤</span><h2>Your inbox is empty</h2><p>Save a link or recipe photos to begin.</p></div>}
    </section>
  </div>
}

function statusClass(status: InboxRecord['status']) { return status === 'Failed' ? 'failed' : status === 'Saved' ? 'saved' : status === 'Ready for Review' ? 'review' : 'pending' }
