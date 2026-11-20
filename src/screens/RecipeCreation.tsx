import { RecipeCreationOptions } from '../components/RecipeCreationOptions'

export function RecipeCreation({ onBack, onManual, onImportUrl, onImportPhotos }: { onBack: () => void; onManual: () => void; onImportUrl: (url: string) => Promise<void>; onImportPhotos: (files: File[]) => Promise<void> }) {
  return <div className="page"><button className="back-button" onClick={onBack}>← Back to recipes</button><header className="page-header"><div><p className="eyebrow">Your collection</p><h1>New Recipe</h1><p>Start from scratch, a link, or recipe photos. Imported details are always reviewed before saving.</p></div></header><RecipeCreationOptions onManual={onManual} onImportUrl={onImportUrl} onImportPhotos={onImportPhotos} photoExtractsWithAi /></div>
}
