import type { RecipeSuggestion } from '../inspiration'
import { Icon } from './Icons'
import { RecipeImage } from './RecipeCard'

export function InspirationCard({ suggestion, onOpen, onAddToDeck, isOnDeck }: { suggestion: RecipeSuggestion; onOpen: () => void; onAddToDeck: () => void; isOnDeck: boolean }) {
  const { recipe, reason } = suggestion
  return <article className="inspiration-card">
    <button className="inspiration-open" onClick={onOpen} aria-label={`Open ${recipe.title}`}>
      <div className="inspiration-image"><RecipeImage recipe={recipe} /><span className="suggestion-reason">{reason}</span></div>
      <span className="recipe-card-copy"><strong>{recipe.title}</strong><span><Icon name="clock" size={15} /> {recipe.prepMinutes + recipe.cookMinutes} min · {recipe.cuisine}</span></span>
    </button>
    <button className="inspiration-deck" onClick={onAddToDeck} disabled={isOnDeck}>{isOnDeck ? 'On deck' : '+ Add to Deck'}</button>
  </article>
}
