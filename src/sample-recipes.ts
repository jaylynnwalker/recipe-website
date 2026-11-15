import type { Recipe } from './types'

export const recipes: Recipe[] = [
  {
    id: 'lemon-chicken', title: 'Lemon Herb Chicken', description: 'A bright, cozy skillet dinner with crisp-edged potatoes and a lemony pan sauce.', status: 'Our Rotation', cuisine: 'Mediterranean', tags: ['Chicken', 'One Pan', 'Weeknight'], prepMinutes: 15, cookMinutes: 35, baseServings: 4,
    image: 'https://images.unsplash.com/photo-1532550907401-a500c9a57435?auto=format&fit=crop&w=900&q=80', imageAlt: 'Roasted lemon herb chicken with potatoes',
    ingredients: [{ quantity: 1.5, unit: 'lb', name: 'boneless chicken thighs' }, { quantity: 1, unit: 'lb', name: 'baby potatoes', note: 'halved' }, { quantity: 1, name: 'lemon', note: 'zested and juiced' }, { quantity: 2, unit: 'tbsp', name: 'olive oil' }, { quantity: 3, unit: 'cloves', name: 'garlic', note: 'minced' }, { quantity: 1, unit: 'tsp', name: 'dried oregano' }, { quantity: null, name: 'salt and black pepper', note: 'to taste' }],
    steps: [{ instruction: 'Heat the oven to 425°F. Toss the potatoes with half the olive oil, salt, and pepper in a large oven-safe skillet.' }, { instruction: 'Season the chicken with oregano, salt, and pepper. Nestle it among the potatoes and roast for 25 minutes.', tip: 'Leave room between the chicken pieces so the edges brown instead of steam.' }, { instruction: 'Mix the remaining oil with garlic, lemon zest, and juice. Spoon over the chicken, then roast until golden and cooked through, about 10 minutes more.' }, { instruction: 'Rest for 5 minutes and spoon the pan juices over everything before serving.', tip: 'A short rest keeps the chicken juicy and gives the sauce time to settle.' }],
    notes: 'Excellent with a simple cucumber salad. Add red pepper flakes when we want a little heat.', source: { label: 'Adapted from the family recipe binder' },
  },
  {
    id: 'tomato-pasta', title: 'Creamy Tomato Pasta', description: 'Silky tomato sauce, basil, and parmesan for an easy comfort-food dinner.', status: 'Our Rotation', cuisine: 'Italian', tags: ['Vegetarian', 'Pasta', 'Quick'], prepMinutes: 10, cookMinutes: 20, baseServings: 4,
    image: 'https://images.unsplash.com/photo-1473093295043-cdd812d0e601?auto=format&fit=crop&w=900&q=80', imageAlt: 'Creamy tomato pasta in a shallow bowl',
    ingredients: [{ quantity: 12, unit: 'oz', name: 'rigatoni' }, { quantity: 1, unit: 'can', name: 'crushed tomatoes' }, { quantity: .5, unit: 'cup', name: 'heavy cream' }, { quantity: .5, unit: 'cup', name: 'parmesan', note: 'finely grated' }, { quantity: .25, unit: 'cup', name: 'fresh basil' }],
    steps: [{ instruction: 'Boil the rigatoni in well-salted water until just shy of al dente.' }, { instruction: 'Simmer the tomatoes until slightly reduced, then stir in the cream.', tip: 'Keep the heat low after adding cream so the sauce stays silky.' }, { instruction: 'Toss in the pasta with parmesan and a splash of pasta water. Finish with basil.' }],
    notes: 'Spinach is an easy addition. Fold it in just before the pasta.', source: { label: 'House favorite' },
  },
  {
    id: 'salmon-bowls', title: 'Ginger Salmon Bowls', description: 'Glazed salmon with crunchy vegetables, rice, and a ginger-sesame drizzle.', status: 'Want to Try', cuisine: 'Asian-inspired', tags: ['Seafood', 'Bowls', '30 Minutes'], prepMinutes: 15, cookMinutes: 15, baseServings: 2,
    image: 'https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=80', imageAlt: 'Colorful rice bowl with vegetables',
    ingredients: [{ quantity: 12, unit: 'oz', name: 'salmon' }, { quantity: 2, unit: 'cups', name: 'cooked rice' }, { quantity: 1, unit: 'cup', name: 'shredded cabbage' }, { quantity: 1, unit: 'tbsp', name: 'fresh ginger', note: 'grated' }, { quantity: 2, unit: 'tbsp', name: 'soy sauce' }],
    steps: [{ instruction: 'Whisk ginger and soy sauce. Brush half over the salmon.' }, { instruction: 'Broil the salmon until caramelized and just cooked through, 7–9 minutes.' }, { instruction: 'Divide rice and cabbage between bowls. Add salmon and drizzle with the remaining sauce.' }],
    notes: 'Try with cucumber and avocado. Untested household recipe.', source: { label: 'Recipe clipping' },
  },
  {
    id: 'beef-stew', title: 'Sunday Beef Stew', description: 'Slow-simmered beef, carrots, and potatoes in a rich savory broth.', status: 'Our Rotation', cuisine: 'American', tags: ['Beef', 'Slow Cooked', 'Comfort Food'], prepMinutes: 25, cookMinutes: 150, baseServings: 6, image: null, imageAlt: 'Neutral illustrated recipe placeholder',
    ingredients: [{ quantity: 2, unit: 'lb', name: 'beef chuck', note: 'cubed' }, { quantity: 3, name: 'carrots', note: 'sliced' }, { quantity: 1.5, unit: 'lb', name: 'gold potatoes', note: 'cubed' }, { quantity: 4, unit: 'cups', name: 'beef broth' }],
    steps: [{ instruction: 'Brown the beef in batches in a heavy pot.' }, { instruction: 'Add broth and simmer gently for 90 minutes.' }, { instruction: 'Add carrots and potatoes; cook until tender, about 45 minutes.', tip: 'Keep the simmer gentle so the beef stays tender.' }],
    notes: 'Even better the next day.', source: { label: 'Grandma’s recipe card' },
  },
]
