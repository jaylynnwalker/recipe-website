# Requirements

## 1. Purpose

Build a private, mobile-first household recipe website that becomes the single place to find and cook recipes previously scattered across websites, YouTube, cookbooks, family recipes, and AI suggestions. The primary goal is to rediscover dishes the household already enjoys and simplify choosing 2–3 dinners at a time.

## 2. Product principles

- **One source of truth:** Saved recipes are readable and editable inside the app; preserve source attribution and original links.
- **Low friction:** Saving a link or photograph must be quick, even if extraction is incomplete.
- **Mobile first:** Primarily used on phones; responsive on computers.
- **Shared household:** Two household members can contribute to one library, dinner lineup, and grocery list.
- **Simple and inexpensive:** Prefer deterministic features over AI where possible; avoid unnecessary integrations and recurring fees.
- **Private by default:** Require authenticated access, including when accessed remotely.
- **No rigid scheduling:** Dinner lineup is not assigned to calendar days.

## 3. Users and access

- Two individual household accounts with access to the same content.
- Both users may add, edit, archive, and browse recipes; edit the dinner lineup, pantry staples, and grocery list.
- Access from home and remotely via secure HTTPS is desired.
- Offline functionality is **not required**.
- No public recipe publishing or social features in the initial scope.

## 4. Functional requirements

Priority: **P0** = initial usable release; **P1** = next iteration; **P2** = optional later. Priority reflects proposed delivery order, not removal from the product vision.

### 4.1 Recipe library and discovery

| ID | Priority | Requirement |
|---|---|---|
| REC-01 | P0 | Store recipes with title, optional photo, description, cuisine(s), meal type, protein/category tags, prep/cook time, base servings, ingredients, ordered steps, and source metadata. |
| REC-02 | P0 | Search saved recipes by title, ingredients, cuisine, and tags without requiring AI. |
| REC-03 | P0 | Browse and filter by cuisine, protein, time, rotation status, and Want to Try. |
| REC-04 | P0 | Support statuses **Want to Try**, **Our Rotation**, and **Archived**. |
| REC-05 | P0 | Show compact recipe thumbnails and lists; prioritize scanability over large imagery. |
| REC-06 | P0 | Allow editing ingredients, quantities, steps, tips, classifications, and photos directly. Maintain **one editable recipe**, not parallel original/custom versions. |
| REC-07 | P0 | Store original URL, video URL, or cookbook title/page where applicable. |
| REC-08 | P1 | Track last-cooked date and cooking count using a lightweight “Made this” action. |
| REC-09 | P1 | Show forgotten favorites, recently added recipes, and rotation suggestions. |
| REC-10 | P1 | Warn about potential duplicates, particularly matching source URLs. |
| REC-11 | P2 | Support custom collections (e.g., Holiday Meals, Grilling). |
| REC-12 | P1 | Export recipe data in a portable format. |

### 4.2 Recipe details and cooking

| ID | Priority | Requirement |
|---|---|---|
| COOK-01 | P0 | Provide both a full-recipe view and optional step-by-step cooking mode. |
| COOK-02 | P0 | Show ingredients with checkboxes and adjust measured quantities for a selected serving count. |
| COOK-03 | P0 | Display optional tips **inside their associated cooking steps**, in both modes. |
| COOK-04 | P0 | Allow editing a step or tip without maintaining a separate notes/version system. |
| COOK-05 | P1 | Show embedded source videos where supported and provide a link to the original source. |
| COOK-06 | P1 | Add a recipe’s ingredients to the shared grocery list using the selected servings. |
| COOK-07 | P2 | Provide a print-friendly view and optional screen-awake behavior where supported. |

### 4.3 Recipe import and inbox

| ID | Priority | Requirement |
|---|---|---|
| IMP-01 | P0 | Save a URL, image, or manually entered recipe into a **Recipe Inbox** before full processing. |
| IMP-02 | P0 | Import standard recipe webpages by extracting structured recipe information where available. |
| IMP-03 | P0 | Review and correct extracted fields before publishing to the recipe library. |
| IMP-04 | P0 | Preserve the original source and keep failed/partial imports in the inbox for later correction. |
| IMP-05 | P1 | Accept multiple photographs of cookbook pages or handwritten recipe cards; extract text and structure using image-capable AI. |
| IMP-06 | P1 | Support YouTube links using available descriptions/transcripts; clearly flag unavailable or incomplete instructions. |
| IMP-07 | P1 | Suggest cuisine/tags automatically when possible; allow corrections. |
| IMP-08 | P1 | Upload multiple cookbook photos and process separate recipes into individual inbox entries. |
| IMP-09 | P2 | Explore phone share-sheet integration and additional platforms (e.g., Instagram/TikTok), subject to access limitations. |

**Import rule:** Never invent missing quantities or instructions silently. Flag uncertain fields and require user review. Retain uploaded source images where appropriate. Respect source access restrictions and attribution.

### 4.4 Dinner lineup and meal selection

| ID | Priority | Requirement |
|---|---|---|
| MEAL-01 | P0 | Maintain a shared, unordered dinner lineup, typically containing **2–3 recipes**. |
| MEAL-02 | P0 | Allow independent serving counts per planned recipe, including extra portions for leftovers. |
| MEAL-03 | P0 | Add, remove, and mark meals cooked without assigning dates. |
| MEAL-04 | P0 | Keep completed and incomplete meals visible until a user explicitly starts a new lineup. |
| MEAL-05 | P1 | Offer to carry over uncooked meals when starting a new lineup. |
| MEAL-06 | P1 | “Help Me Pick” suggests recipes from Our Rotation, forgotten favorites, Want to Try, or a mix. |
| MEAL-07 | P1 | Filter suggestions by time, cuisine, and ingredients; offer new AI-generated ideas on request. |

### 4.5 Shared grocery list and pantry staples

| ID | Priority | Requirement |
|---|---|---|
| GROC-01 | P0 | Generate one grocery list from the current dinner lineup using each recipe’s selected servings. |
| GROC-02 | P0 | Merge matching ingredients and compatible units where safe; flag incompatible or ambiguous quantities for review. |
| GROC-03 | P0 | Maintain a **fixed, editable, shared pantry staples list** (e.g., garlic, oil, spices). |
| GROC-04 | P0 | Exclude staples by default but permit adding any staple back to the list. |
| GROC-05 | P0 | Allow users to mark other items “already have,” separately from “purchased.” |
| GROC-06 | P0 | Allow manual additions, quantity edits, removals, and purchased checkboxes. |
| GROC-07 | P0 | Synchronize changes between household accounts. |
| GROC-08 | P0 | Grocery generation/refresh happens **only on explicit user action**, never automatically when the lineup changes. |
| GROC-09 | P0 | On refresh, preview proposed changes and preserve manually added items and shopping decisions. |
| GROC-10 | P1 | Group shopping items by aisle/category (produce, meat, dairy, pantry, etc.). |

WhatsApp sharing is **not in initial scope** because the grocery list will be available remotely in the website.

### 4.6 AI capabilities

| ID | Priority | Requirement |
|---|---|---|
| AI-01 | P1 | “What Can I Make?” accepts ingredients on hand and proposes matching saved recipes and possible new dishes. |
| AI-02 | P1 | Suggest substitutions and recipe adaptations for missing ingredients. |
| AI-03 | P1 | Generate a new recipe from a natural-language prompt; allow saving it to Want to Try. |
| AI-04 | P1 | Answer cooking questions with the current recipe as context. |
| AI-05 | P1 | Use image-capable AI for cookbook/handwritten recipe extraction when requested. |
| AI-06 | P0 | Ordinary browsing, filtering, scaling, and grocery calculations must not require paid AI calls. |
| AI-07 | P1 | Clearly distinguish AI-generated or untested recipes from established household favorites. |
| AI-08 | P1 | Require confirmation before AI suggestions overwrite saved recipe content. |

## 5. UX and visual requirements

- Style: **Warm Cookbook** — cream background, muted olive/sage greens, restrained warm brown accents, serif headings, readable sans-serif body text.
- Mobile-first responsive design; desktop is secondary.
- Compact, consistently sized recipe photos; avoid visually crowded screens.
- Homepage: prominent search, Help Me Pick, What Can I Make, dinner lineup shortcut, and a small number of suggestions.
- Recipe Library: detailed filters and browsing; keep the homepage simple.
- Simple bottom navigation on mobile; accessible controls and legible text.
- Dedicated pages for Recipe Library, Recipe Detail/Cooking, Recipe Inbox/Add, Dinner Lineup, Grocery List, and Help Me Pick.

## 6. Nonfunctional requirements

- **Privacy/security:** authenticated household access; encrypted remote connections; no public database exposure; protected AI credentials.
- **Scale:** target hundreds of recipes initially, with room for 1,000+.
- **Reliability:** preserve drafts and failed imports; safe recovery after server restarts.
- **Data portability:** export recipe records and retain access to uploaded photos.
- **Backups:** automated backups with a copy stored separately from the live server.
- **Cost:** prefer free/self-hosted components; AI billed only when explicitly used.
- **Availability:** home server/internet outages may temporarily make the website unavailable; offline mode is not required.

## 7. Key user journeys and acceptance criteria

1. **Capture from web:** A user pastes a recipe URL, sees an inbox entry immediately, reviews extracted fields, and saves a complete editable recipe.
2. **Capture from cookbook:** A user uploads one or more page photos, reviews extracted ingredients/steps, corrects errors, and saves the recipe with source attribution.
3. **Find an old favorite:** A user searches by dish, cuisine, or ingredient and opens the recipe without remembering the original source.
4. **Cook:** A user selects two servings, sees scaled ingredients, follows full or step-by-step instructions, and sees tips in the relevant steps.
5. **Plan:** Either user adds 2–3 dinners to an unordered shared lineup and sets servings per meal.
6. **Shop:** A user explicitly generates groceries; staples are excluded; quantities are combined; both users can mark purchased items remotely.
7. **Refresh safely:** Changing the lineup does not change the grocery list until “Update Grocery List” is chosen; manual items and shopping state are preserved or reviewed before changes.
8. **Discover:** Help Me Pick surfaces existing/forgotten dishes without AI and can request novel AI suggestions when desired.

## 8. Out of scope for the first release

- Offline support; pantry inventory/stock counting; nutrition and calorie tracking; barcode scanning; grocery-store integrations; WhatsApp automation; public recipe sharing; elaborate ratings; day-by-day calendars; automatic AI background activity; advanced timers.

## 9. Open decisions

- Exact account onboarding and password recovery approach.
- Whether cookbook-image extraction and YouTube import ship in the first usable release or the next iteration.
- Specific remote-access hostname/domain and access policy.
- Exact ingredient normalization rules for mixed units, package sizes, and optional ingredients.
- Whether source photos are retained indefinitely and whether imported external images may be stored.

## 10. Definition of initial success

Both household members can sign in from phones, save and edit recipes, search by cuisine/ingredients, select 2–3 dinners without dates, generate and edit a shared grocery list excluding fixed staples, and access the website securely outside the home. Advanced AI and import channels can be added incrementally without changing this core workflow.
