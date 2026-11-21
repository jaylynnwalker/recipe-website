import { useState } from 'react'
import type { InboxRecord } from '../api'
import { RecipeCreationOptions } from '../components/RecipeCreationOptions'

export function Inbox({ items, onManual, onImportUrl, onImportPhotos, onReview, onRetry, onAiExtract, onDelete }: {
  items: InboxRecord[]; onManual: () => void; onImportUrl: (url: string) => Promise<void>; onImportPhotos: (files: File[]) => Promise<void>
  onReview: (item: InboxRecord) => void; onRetry: (item: InboxRecord) => Promise<void>; onAiExtract: (item: InboxRecord) => Promise<void>; onDelete: (item: InboxRecord) => Promise<void>
}) {
  const [extractingId, setExtractingId] = useState<string | null>(null)
  const [extractionError, setExtractionError] = useState('')
  const extract = async (item: InboxRecord) => {
    setExtractingId(item.id); setExtractionError('')
    try { await onAiExtract(item) }
    catch (cause) { setExtractionError(cause instanceof Error ? cause.message : 'We could not extract this recipe. Please try again or enter it manually.') }
    finally { setExtractingId(null) }
  }
  return <div className="page"><header className="page-header"><div><p className="eyebrow">Capture something delicious</p><h1>Recipe Inbox</h1><p>Save it now, review the details when you’re ready.</p></div></header>
    <RecipeCreationOptions onManual={onManual} onImportUrl={onImportUrl} onImportPhotos={onImportPhotos} photoExtractsWithAi />
    <section className="queue"><div className="section-heading"><div><p className="eyebrow">Saved for review</p><h2>Inbox Queue</h2></div><span className="queue-count">{items.length} items</span></div>
      {extractionError && <p className="data-error" role="alert">{extractionError}</p>}
      {items.length ? items.map((item) => <article key={item.id} aria-busy={extractingId === item.id}><div className="queue-thumb">{item.sourceType === 'photo' ? (item.assets[0] ? <img src={item.assets[0].url} alt="First uploaded recipe page" /> : '▧') : '↗'}</div><div><span className={`queue-status ${statusClass(item.status)}`}>{item.status}</span><h3>{item.title}</h3><p>{item.sourceType === 'photo' ? `${item.assets.length} original photo${item.assets.length === 1 ? '' : 's'}` : item.sourceUrl}</p>{item.duplicateRecipeId && <small className="duplicate-warning">Potential duplicate in your recipe library</small>}{item.errorMessage && <small className="import-message">{item.errorMessage}</small>}</div><div className="queue-actions">{item.status !== 'Saved' && <button className="secondary" onClick={() => onReview(item)}>{item.status === 'Failed' ? 'Enter manually' : 'Review'}</button>}{item.status !== 'Saved' && <button className="secondary" disabled={extractingId !== null} onClick={() => void extract(item)}>{extractingId === item.id ? 'Extracting…' : 'Extract with AI'}</button>}{item.status === 'Failed' && item.sourceUrl && <button className="secondary" disabled={extractingId !== null} onClick={() => void onRetry(item)}>Retry without AI</button>}<button className="remove" disabled={extractingId === item.id} onClick={() => void onDelete(item)}>Delete</button></div></article>) : <div className="empty-state"><span>▤</span><h2>Your inbox is empty</h2><p>Save a link or recipe photos to begin.</p></div>}
    </section>
  </div>
}

function statusClass(status: InboxRecord['status']) { return status === 'Failed' ? 'failed' : status === 'Saved' ? 'saved' : status === 'Ready for Review' ? 'review' : 'pending' }
