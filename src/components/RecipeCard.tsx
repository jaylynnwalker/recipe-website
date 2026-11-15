import type { Recipe } from '../types'
import { Icon } from './Icons'

export function RecipeImage({ recipe, className = '' }: { recipe: Recipe; className?: string }) {
  if (recipe.image) return <img className={className} src={recipe.image} alt={recipe.imageAlt} />
  return <div className={`image-placeholder ${className}`} role="img" aria-label={recipe.imageAlt}><span>✦</span><small>Family recipe</small></div>
}

export function RecipeCard({ recipe, onOpen, compact = false }: { recipe: Recipe; onOpen: () => void; compact?: boolean }) {
  return <button className={`recipe-card ${compact ? 'compact' : ''}`} onClick={onOpen}>
    <RecipeImage recipe={recipe} />
    <span className="recipe-card-copy">
      <strong>{recipe.title}</strong>
      <span><Icon name="clock" size={15} /> {recipe.prepMinutes + recipe.cookMinutes} min · {recipe.cuisine}</span>
    </span>
  </button>
}
