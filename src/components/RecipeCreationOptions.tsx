import { useState, type FormEvent } from 'react'

export function RecipeCreationOptions({ onManual, onImportUrl, onImportPhotos, photoExtractsWithAi = false }: {
  onManual: () => void
  onImportUrl: (url: string) => Promise<void>
  onImportPhotos: (files: File[]) => Promise<void>
  photoExtractsWithAi?: boolean
}) {
  const [url, setUrl] = useState('')
  const [photos, setPhotos] = useState<File[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submitUrl = async (event: FormEvent) => { event.preventDefault(); if (!url.trim()) return; setBusy(true); setError(''); try { await onImportUrl(url.trim()); setUrl('') } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to import URL') } finally { setBusy(false) } }
  const submitPhotos = async (event: FormEvent) => { event.preventDefault(); if (!photos.length) return; setBusy(true); setError(''); try { await onImportPhotos(photos); setPhotos([]) } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to import photos') } finally { setBusy(false) } }
  return <>{error && <p className="data-error" role="alert">{error}</p>}<div className="creation-grid">
    <section className="creation-panel"><span>＋</span><div><h2>Enter Manually</h2><p>Write a household recipe directly in the editor.</p><button className="primary" type="button" onClick={onManual}>Start a blank recipe</button></div></section>
    <form className="creation-panel" onSubmit={submitUrl}><span>↗</span><div><h2>Import from URL</h2><p>Recipe website, YouTube, Instagram, or Facebook link.</p><label>Recipe URL<input type="url" required placeholder="https://…" value={url} onChange={(event) => setUrl(event.target.value)} /></label><button className="primary" disabled={busy}>Save & extract</button></div></form>
    <form className="creation-panel" onSubmit={submitPhotos}><span>▧</span><div><h2>Import from Photos</h2><p>One or more cookbook pages or handwritten cards. Originals are preserved.</p><label>Recipe photos<input type="file" required multiple accept="image/jpeg,image/png,image/webp" onChange={(event) => setPhotos(Array.from(event.target.files ?? []))} /></label><button className="primary" disabled={busy || !photos.length}>{photoExtractsWithAi ? 'Upload & extract with AI' : `Save ${photos.length || ''} photo${photos.length === 1 ? '' : 's'}`}</button></div></form>
  </div></>
}
