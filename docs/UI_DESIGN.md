# Our Kitchen — UI Design Specification

**Status:** Approved visual direction; detailed interactions subject to implementation testing  
**Version:** 1.0  
**Scope:** Responsive household recipe website

## 1. Design goals

- Warm, approachable cookbook feel without a crowded interface.
- Mobile-first: optimized for quick use while shopping and cooking; responsive on desktop.
- Prioritize finding a recipe, choosing a meal, cooking, and shopping.
- Keep layouts calm, legible, and consistent across screens.
- Do not depend on professional food photography: personal photos and tasteful placeholders must work equally well.

## 2. Visual language

### Palette

The **original light sage-and-cream mockup** is the visual source of truth. Do **not** adopt the later burgundy/forest-green botanical redesign.

| Token | Proposed color | Usage |
| --- | --- | --- |
| Cream | `#F9F6EE` | Primary page background |
| Sage | `#8A9B6A` | Primary actions and selected states |
| Olive | `#5E6F45` | Stronger accents, active navigation |
| Brown | `#7A4E3A` | Subtle warm accent, sparingly |
| Warm tan | `#D9C3A5` | Secondary surfaces and details |
| Text | `#252821` | Main text (provisional accessibility adjustment) |
| White | `#FFFFFF` | Cards, input surfaces |

Use restrained color: light backgrounds, soft borders, limited accent use, no heavy textures or ornamental overlays. Ensure accessible contrast, even if this requires slightly darkening text or button colors.

### Typography

- **Playfair Display** or similar understated serif for the *Our Kitchen* wordmark and occasional editorial headings.
- **Inter** or equivalent clear sans-serif for navigation, forms, recipe titles, ingredients, and instructions.
- Avoid decorative serif styling for dense functional content.

### Components

- Softly rounded cards and inputs, subtle outlines/shadows, consistent spacing.
- Compact, consistently cropped recipe thumbnails.
- Green primary buttons; neutral outlined secondary buttons.
- Minimal icons with text labels for navigation.
- Large touch targets (at least ~44 × 44 CSS pixels) and readable cooking text.

## 3. Navigation

### Mobile

Persistent five-item bottom navigation:

1. **Home**
2. **Recipes**
3. **Deck** (opens **Meals on Deck**)
4. **Groceries**
5. **Inbox**

Selecting a primary destination immediately closes transient recipe detail, edit, creation, and import-review views. The highlighted navigation item and displayed page stay synchronized while loaded household data remains in memory.

Use a simple selected state in sage/olive. Do not introduce a separate tab for every feature. **Help Me Pick** is a prominent action on Home and can also be accessed when adding a meal.

### Desktop

Light cream left sidebar with **Our Kitchen** branding and navigation: Home, Recipes, Meals on Deck, Grocery List, Recipe Inbox. Main content uses generous whitespace and a wider content column. Desktop is an adaptation of the same visual system, not a different theme.

## 4. Screen specifications

### 4.1 Home — mobile

Order of content:

1. Small **Our Kitchen** wordmark.
2. Search recipes field.
3. Prominent **Help Me Pick** button.
4. **Meals on Deck** summary card (count of meals; opens lineup).
5. **Recipe Ideas** with two or a few compact photo cards.
6. Bottom navigation.

Keep filters and large collections off Home. It should function as a launch point, not a dashboard packed with information.

### 4.2 Home — desktop

Match the **first approved light sage-and-cream mockup**, including the original lower section:

- Cream left navigation sidebar.
- **Welcome Back** heading, search field, and Help Me Pick action.
- **Meals on Deck** horizontal row of compact recipe-photo cards, **without weekday/date labels**.
- **Recipe Ideas** horizontal row of **photo recipe cards** beneath it.

**Important:** Do **not** replace the desktop **Recipe Ideas** photo-card section with large icon-only tiles labeled All Recipes / Our Rotation / Want to Try / Favorites. That was a deviation in later mockups. Those categories belong in the Recipe Library filtering/navigation, not in place of the original Home recipe cards.

#### A Little Inspiration

- Populate Recipe Ideas only from recipes already saved in the household library; do not fetch or generate recipes for this section.
- Show a rotating, duplicate-free mix of up to three compact photo cards: a **Forgotten Favorite** from Our Rotation that has not been cooked recently, an unmade **Want to Try**, and another **Rediscover** selection from the library when candidates are available.
- Each card includes a small reason label, opens its Recipe Detail screen, and offers a secondary **Add to Deck** action without requiring the detail screen.
- A quiet **Fresh ideas** control requests another selection. The client may also rotate the selection periodically while the Home screen remains open.
- Cooking-history metadata is the eventual source for suggestion classification. Missing history may be treated as unmade for Want to Try recipes; the interface should not imply exact history when records are unavailable.

### 4.3 Recipe Library

- Search at top.
- Compact status filters: **All**, **Our Rotation**, **Want to Try**; **Archived** available through an additional filter/menu.
- Additional filtering for cuisine, protein sources, categories, ingredients, time, and tags, without crowding the default view.
- Compact recipe rows on mobile: thumbnail, title, optional favorite indicator.
- On desktop, use an appropriately spaced list/grid of recipe cards consistent with the same design system.
- Missing-photo recipes use a tasteful illustrated or neutral category placeholder, not a broken or empty image.

### 4.4 Recipe Detail

- Recipe photo/header, title, status/cuisine tags, yield amount/unit, preparation/cooking time, optional resting/chilling time, and a calculated total.
- **Three tabs: Ingredients / Instructions / Notes.** Tabs prevent repeatedly scrolling past ingredients to reach instructions.
- Ingredients tab: checkable ingredients; servings stepper scales primary and alternative quantities while preserving package-size details.
- Instructions tab: numbered, readable steps; technique tips shown **within the relevant step**.
- Notes tab: optional personal notes and source attribution; does not replace inline cooking tips.
- Persistent or easy-to-reach **Cook Mode** action.
- Recipe can be edited directly; no separate version-history UI required.
- A compact **Made this** action records a cooking-history event and updates the displayed count without leaving the detail screen.
- Source link and video embed where available/appropriate.
- Imported descriptions are concise one- or two-sentence summaries without source-site commentary; cuisine, multiple categories, and tags remain editable during review.

### 4.5 Cook Mode

- Optional focused, step-by-step view with large text and obvious Previous/Next controls.
- Ingredient access without losing the current instruction step.
- Inline tips visible with their step.
- Keep screen awake when technically supported and permitted; otherwise provide clear expectations.
- Avoid visually dense decoration during cooking.

### 4.6 Meals on Deck

**Name is always “Meals on Deck,” not “Dinner Lineup” or “This Week.”**

- Flexible list of chosen meals, each showing thumbnail, name, and servings.
- **No weekdays, calendar dates, or mandatory weekly boundary.**
- Add/remove meals; adjust servings; reorder if useful.
- Mark a meal **Cooked**; record it in cooking history.
- Completed meals remain visible until removed or cleared with **Clear completed**; unfinished meals are retained.
- Uncooked meals remain until manually removed, completed, or carried over during a manual reset.
- Help Me Pick can add meals directly to the deck.
- Grocery list is generated from the deck, but **not automatically regenerated** on every change.

### 4.7 Grocery List

- Group items by category (e.g., Produce, Meat & Protein, Pantry).
- Checkbox to mark purchased items.
- Editable quantities, additions, and removals.
- Shared state visible to both logged-in household members.
- **Update Grocery List** action explicitly reviews and applies changes from Meals on Deck.
- The review identifies generated additions, quantity updates, and removals before the user applies the new snapshot.
- Preserve manual additions, checked items, and exclusions when reconciling changes.
- Exclude the editable shared pantry-staples list by default, with ability to add individual staples back.
- Do not use a date-specific “This Week” framing; use **Current List** or similar neutral label.

### 4.8 Recipe Inbox / Add Recipe

- The Recipe Library **Add recipe** action offers the same three paths as the Inbox: manual entry, URL import, or one/more recipe photos. All imported paths lead to the shared review editor before saving.
- The manual editor supports title/description, searchable multi-select protein sources, ingredients with a primary measurement, optional alternative measurements, separate package-size details, ordered instructions with inline tips, times, servings, cuisine/categories/tags, status, source, notes, and an optional photo.
- Ingredient units use a searchable, create-capable selector backed by one canonical cooking-unit vocabulary. Blank and custom units remain valid; known abbreviations and plurals normalize consistently for imports and grocery aggregation.
- Recipe Detail reuses the same editor with existing values prefilled. Deletion requires explicit confirmation and returns to the refreshed library.

- Three primary actions: **Enter Manually**, **Import from URL**, and **Import from Photos**.
- Cuisine uses a searchable, create-capable single-value control. Categories and tags use searchable, create-capable multi-value controls. Existing household values are offered and equivalent capitalization, spacing, hyphen, and underscore variants are normalized to the established spelling.
- Link import supports structured recipe pages plus publicly accessible metadata from YouTube, Instagram, and Facebook. Restricted or incomplete social content remains reviewable/manual rather than being inferred.
- Photo import supports one or multiple cookbook pages, handwritten cards, and phone photos.
- New submissions are saved immediately to a review queue even if extraction fails.
- Photo submissions open the review editor immediately and automatically start the existing AI extraction flow; progress, success, and failure remain visible without navigating back to Inbox.
- Show queue items with thumbnail/source and status: Pending, Processing, Ready for Review, Failed, Saved.
- Failed URL imports offer both **Retry** and manual entry. Potential matches in the saved library display a duplicate warning before review.
- Photo imports clearly state that originals are preserved. **Extract with AI** processes ordered multi-page images only on request; failures retain the originals and allow retry or manual transcription.
- Review screen shows extracted title, ingredients, instructions, tags, and source details for correction before saving.
- If an imported source has no yield, the review form leaves Yield amount blank and asks the reviewer to enter it before saving without discarding other extracted fields.
- Review includes **Extract with AI** for photo and URL sources. Re-extraction confirms before replacing unsaved edits, retains the original source, and leaves current fields untouched when extraction fails.
- URL imports show a locally stored extracted cover image when available. Reviewers can replace it with an upload or remove it without affecting the recipe text or source URL.
- AI extraction shows a persistent **Extracting…** state, prevents duplicate submissions, reports friendly failures, and opens successful results directly in the review editor.
- Extracted ingredient names and instruction steps begin with a capital letter for readability; formatting preserves all remaining source capitalization rather than applying title case.
- After a successful save, the completed Inbox record is retained for source/history purposes but immediately disappears from the active queue and its count. Failed or incomplete saves remain available for correction and retry.
- Preserve original uploaded photos and optional cookbook title/page number.
- Check for likely duplicates before final save.

### 4.9 Help Me Pick / What Can I Make?

- Calm, focused interface, not a large chatbot feed by default.
- Offer options drawn from Our Rotation, forgotten favorites, Want to Try, and optionally AI-generated dishes.
- Optional constraints: available ingredients, time, and desired type of meal.
- Distinguish saved-library suggestions from newly generated recipes.
- Allow adding a suggestion to Meals on Deck; generated recipes are only saved after explicit approval.

#### What Can I Make? ingredient selection

- Open from the recipe-discovery actions without adding another persistent navigation tab.
- Let users add and individually remove ingredients they have available.
- Show a compact summary of the household's Pantry Staples and include them by default through an explicit checkbox.
- **Find Recipes** shows saved-library matches first, using normal compact recipe cards.
- Generated ideas appear in a separate, clearly labeled **Not saved** section. Each must be reviewed and corrected in the recipe editor before it can be saved to Want to Try.
- Never imply that a generated idea is a tested or saved household recipe.

### 4.10 Household Settings — Pantry Staples

- Household Settings is accessible from the household/profile area rather than adding a sixth primary navigation item.
- Pantry Staples are displayed as compact removable ingredient chips, with a simple input for adding another staple.
- Explain that staples are shared, normally excluded from generated grocery lists, and treated as available for What Can I Make suggestions.
- On mobile, keep management in a single calm card with touch-friendly add/remove controls.
- In the Grocery List, show a subtle excluded-staples summary. Users can review excluded staples and explicitly add individual items back to the current grocery snapshot.
- Adding a staple back does not alter the Pantry Staples setting or automatically regenerate the grocery list.

### 4.11 AI usage and cooking assistance

- Household Settings shows the current calendar month, estimated AI spend, active reservations, configured model, $8 warning, and $10 application budget.
- Recipe Detail and Cook Mode include a compact optional question field for substitutions, techniques, adaptations, and current-recipe questions. Responses never edit the saved recipe.
- AI-unavailable, invalid-response, and budget-exhausted states use ordinary inline error feedback and leave the rest of the application usable.

## 5. Photography and image handling

- User photos are welcome; no requirement for styled or professional images.
- Consistent thumbnail aspect ratios, cropping, and subtle card backgrounds create cohesion.
- Permit replacing/cropping a recipe cover photo.
- Use source images only when available and appropriate to reuse.
- For missing photos, use consistent neutral or illustrated placeholders; do not generate AI food images automatically.
- Preserve uploaded cookbook page images separately from the recipe cover photo.

## 6. Responsive behavior

| Element | Mobile | Desktop |
| --- | --- | --- |
| Navigation | Fixed bottom bar | Left sidebar |
| Home ideas | Small photo cards | Horizontal photo-card row |
| Recipe library | Compact list | Wider list or card grid |
| Recipe detail | Single column, tabbed | Wider reading column, same tabs |
| Meals on Deck | Vertical list | Spacious cards/list, still no dates |
| Grocery list | Touch-first checklist | Wider grouped checklist |
| Inbox | Stacked import actions | Spacious side-by-side layout if useful |
| Household settings | Single-column staple chips and add form | Focused settings card in the main content column |
| What Can I Make? | Stacked ingredient entry, pantry summary, and results | Wider saved-recipe row with a separate ideas section |

Avoid horizontal overflow and tiny text. Preserve the same wording, palette, and component shapes across screen sizes.

## 7. UI states and feedback

Design explicit states for:

- Empty recipe library, empty deck, and empty grocery list.
- Recipe without a photo.
- Import in progress, extraction failure, and review required.
- Duplicate recipe warning.
- Offline/network error and unsaved edits.
- Successful save, cooking completion, and grocery-list reconciliation.
- Loading and AI processing without blocking unrelated navigation.

## 8. Accessibility

- Keyboard-accessible controls, visible focus, and labeled icons.
- Sufficient text and button contrast (target WCAG AA).
- Touch targets around 44 CSS pixels or larger.
- Support browser text scaling and reduced motion.
- Do not convey status using color alone.
- Recipe steps and ingredient amounts must remain readable at typical phone viewing distance.

## 9. Confirmed decisions vs. open details

### Confirmed

- Original **light sage-and-cream** visual direction.
- Simplified, uncluttered mobile Home.
- Mobile bottom navigation and desktop sidebar.
- **Meals on Deck** with no calendar/week assignments.
- **Ingredients / Instructions / Notes** tabs.
- Compact recipe thumbnails; personal photos and placeholders supported.
- Desktop Home **Recipe Ideas must be photo cards**, matching the original first mockup.
- Import links and cookbook/handwritten photos via Inbox.

### To refine during implementation

- Exact fonts, accessible color shades, and spacing tokens.
- Detailed layout of Help Me Pick, Cook Mode, and import-review screens (not fully mocked yet).
- Advanced filter presentation and recipe image crop controls.
- Precise desktop layout for individual secondary screens.

## 10. Acceptance checklist

- [ ] Mobile Home feels visually simple and shows search, Help Me Pick, Meals on Deck, and Recipe Ideas.
- [ ] Desktop Home uses the original photo-card **Recipe Ideas** row, not category icon tiles.
- [ ] All screens use the light sage/cream theme, not burgundy-heavy styling.
- [ ] “Meals on Deck” appears consistently, with no weekdays or weekly reset assumption.
- [ ] Recipe Detail has separate Ingredients, Instructions, and Notes tabs.
- [ ] Users can add cookbook photos, review extraction, and retain originals.
- [ ] Recipe thumbnails work with ordinary phone photos or placeholders.
- [ ] Grocery list is explicitly updated from Meals on Deck, not silently overwritten.
- [ ] Mobile and desktop navigation, labels, and visual components are consistent.
