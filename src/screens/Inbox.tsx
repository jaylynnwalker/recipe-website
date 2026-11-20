import type { InboxRecord } from '../api'
import { RecipeCreationOptions } from '../components/RecipeCreationOptions'

export function Inbox({ items, onManual, onImportUrl, onImportPhotos, onReview, onRetry, onAiExtract, onDelete }: {
  items: InboxRecord[]
  onManual: () => void
  onImportUrl: (url: string) => Promise<void>
  onImportPhotos: (files: File[]) => Promise<void>
  onReview: (item: InboxRecord) => void
  onRetry: (item: InboxRecord) => Promise<void>
  onAiExtract: (item: InboxRecord) => Promise<void>
  onDelete: (item: InboxRecord) => Promise<void>
}) {
  return <div className="page"><header className="page-header"><div><p className="eyebrow">Capture something delicious</p><h1>Recipe Inbox</h1><p>Save it now, review the details when you’re ready.</p></div></header>
    <RecipeCreationOptions onManual={onManual} onImportUrl={onImportUrl} onImportPhotos={onImportPhotos} />
    <section className="queue"><div className="section-heading"><div><p className="eyebrow">Saved for review</p><h2>Inbox Queue</h2></div><span className="queue-count">{items.length} items</span></div>
      {items.length ? items.map((item) => <article key={item.id}><div className="queue-thumb">{item.sourceType === 'photo' ? (item.assets[0] ? <img src={item.assets[0].url} alt="First uploaded recipe page" /> : '▧') : '↗'}</div><div><span className={`queue-status ${statusClass(item.status)}`}>{item.status}</span><h3>{item.title}</h3><p>{item.sourceType === 'photo' ? `${item.assets.length} original photo${item.assets.length === 1 ? '' : 's'}` : item.sourceUrl}</p>{item.duplicateRecipeId && <small className="duplicate-warning">Potential duplicate in your recipe library</small>}{item.errorMessage && <small className="import-message">{item.errorMessage}</small>}</div><div className="queue-actions">{item.status !== 'Saved' && <button className="secondary" onClick={() => onReview(item)}>{item.status === 'Failed' ? 'Enter manually' : 'Review'}</button>}{item.status !== 'Saved' && <button className="secondary" onClick={() => void onAiExtract(item)}>Extract with AI</button>}{item.status === 'Failed' && item.sourceUrl && <button className="secondary" onClick={() => void onRetry(item)}>Retry without AI</button>}<button className="remove" onClick={() => void onDelete(item)}>Delete</button></div></article>) : <div className="empty-state"><span>▤</span><h2>Your inbox is empty</h2><p>Save a link or recipe photos to begin.</p></div>}
    </section>
  </div>
}

function statusClass(status: InboxRecord['status']) { return status === 'Failed' ? 'failed' : status === 'Saved' ? 'saved' : status === 'Ready for Review' ? 'review' : 'pending' }
