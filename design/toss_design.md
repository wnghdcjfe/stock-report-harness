# Design System: Toss (토스)
## 1. Visual Theme & Atmosphere

Toss's design language is the visual thesis of **finance made calm** — a system where complex financial information feels as approachable as a chat message. The interface is overwhelmingly white (`#FFFFFF`) with deep gray (`#191F28`) text, broken only by Toss Blue (`#3182F6`) as a single, disciplined accent. This isn't minimalism as fashion; it's minimalism as **trust engineering**. Financial products historically signal authority through density, charts, and serif typography — Toss does the opposite. The page reads like a friendly assistant taking notes for you, not a Bloomberg terminal.

The signature **8px gray stripe divider** (`#F9FAFB` band between sections) is Toss's structural fingerprint. Instead of hairline rules or whitespace alone, full-bleed gray bands segment the screen into chapters. This horizontal banding gives the long-scroll mobile experience a rhythm: every band signals "new topic," every white section is a self-contained unit. The technique scales effortlessly from a 2-row stock card to a 12-section research report.

Pretendard is the type-system crown jewel — a Korean+Latin variable font with neutral, slightly humanist proportions optimized for Hangul reading. Numbers use `font-variant-numeric: tabular-nums` ubiquitously so that prices, percentages, and counts align in vertical columns without rendering jitter. Large monetary displays use tight negative letter-spacing (`-0.035em`) and weight 800 — the only place in the system where typography becomes loud. Everywhere else, type is calm, lowercase-friendly, and conversational ("~예요", "~했어요" sentence endings).

The depth model is **almost flat**. Toss avoids drop shadows; depth comes from (a) the 8px gray stripes between sections, (b) tonal contrast between white cards and the `#F9FAFB` page background, and (c) hairline borders (`#F2F4F6`) where a card needs a defined edge. The only blur effect is the sticky app bar's `backdrop-filter: blur(12px)` over translucent white. The result feels like paper layered on paper — not screens floating in space.

**Key Characteristics:**
- Single accent color: Toss Blue (`#3182F6`) — used for primary actions, active states, brand moments, and as the "down" color in Korean stock convention
- Korean financial color convention: **Up = Red (`#F04452`), Down = Blue (`#3182F6`)** — opposite of Western markets, mandatory for any Korean fintech UI
- Pretendard Variable font with tabular-nums on every number — prices, percentages, counts, dates
- 8px full-bleed gray stripe (`#F9FAFB`) as the section divider — Toss's signature structural device
- Mobile-first single-column shell at `max-width: 560px` centered on desktop — even desktop sees the mobile composition
- Conversational Korean tone with `~예요/했어요` endings in product copy; never declarative or stiff
- Pill-shaped tags (`border-radius: 999px`) for metadata; rounded rectangles (12–16px) for cards
- Sticky app bar with translucent white + 12px backdrop blur — the only glassmorphism in the system
- Numbers are loud, words are quiet: 34px weight 800 for the headline price, 13–15px weight 400–500 for everything else

## 2. Color Palette & Roles

### Primary Brand
- **Toss Blue** (`#3182F6`): The single accent. Primary CTA background, active link color, brand logo, chart line, "down" indicator in stock context, focus rings, numbered badges.
- **Toss Blue Hover** (`#1B64DA`): Darker blue for `:hover` and `:active` on primary buttons. Never used as a fill color outside interaction states.
- **Toss Blue Bg** (`#E8F3FF`): Light tinted-blue background for pill badges, highlighted stat cards, and brand-colored chips. The "soft blue" that lets Toss Blue appear without dominating.
- **Toss Blue Bg Soft** (`#F4F8FF`): Even lighter blue for callout backgrounds and elevated sections inside white surfaces.

### Korean Stock Up/Down Semantic
- **Up Red** (`#F04452`): Price increase, positive return, gain indicator. Korean convention — opposite of Western markets. Used on `▲` arrows, percentage pills, change values.
- **Up Red Bg** (`#FFF0F1`): Light pink-red background for up-trend pills and gain badges.
- **Down Blue** (`#3182F6`): Price decrease, negative return, loss indicator — intentionally identical to Toss Blue so brand and bearish signal share the same hue. Korean convention.
- **Down Blue Bg** (`#E8F3FF`): Same as Toss Blue Bg — down-trend pills reuse the brand surface.

> **Important:** In Korean fintech UI, never use green for "up" or red for "down" except in international/foreign markets context. Toss is unambiguously Korean-convention.

### Neutral Gray Scale (`gray-50` → `gray-900`)
- **Gray 900** (`#191F28`): Primary text, headings, ticker name, large monetary values. Not pure black — the slight blue-warmth prevents harshness on white.
- **Gray 800** (`#333D4B`): Strong body emphasis, secondary headings, callout body text.
- **Gray 700** (`#4E5968`): Primary body text, paragraph copy, descriptive sentences.
- **Gray 600** (`#6B7684`): Secondary body, news summaries, supporting descriptions.
- **Gray 500** (`#8B95A1`): Muted text, labels above values, date stamps, footnotes.
- **Gray 400** (`#B0B8C1`): Placeholder text, disabled states, dimmed icons.
- **Gray 300** (`#D1D6DB`): Disabled button text, very-low-emphasis dividers.
- **Gray 200** (`#E5E8EB`): Default border for outlined cards and inputs.
- **Gray 100** (`#F2F4F6`): The default hairline divider color — used between list items, KV rows, news entries.
- **Gray 50** (`#F9FAFB`): The signature stripe color. Page background AND the 8px section divider band. Also the fill for muted stat cards and risk-item cards.

### Surface
- **Page Background** (`#F9FAFB`): The body background outside the central shell. Same as Gray 50 — this lets the divider stripes feel like the page itself "shows through."
- **Card Surface** (`#FFFFFF`): All cards, the shell interior, and elevated content. The only true white in the system.
- **Subtle Card** (`#F9FAFB`): Used for stat cards, risk cards, and reference cards that should recede slightly. Identical to Gray 50.

### Status / Tag Colors
- **Tag Default Bg** (`#F2F4F6`) + **Tag Default Text** (`#4E5968`): The neutral pill — used for categorical tags like "슈퍼사이클" or "1조달러 클럽."
- **Tag Blue Bg** (`#E8F3FF`) + **Tag Blue Text** (`#3182F6`): The branded pill — used for primary topic tags like "AI 메모리" or "HBM."
- **Reference Tier Bg** (`#E5E8EB`) + **Reference Tier Text** (`#4E5968`): Tiny tier badges (`A`, `B`, `C`) inside reference list items.

### Tooltip / Overlay
- **Tooltip Surface** (`#191F28`): Dark gray chart tooltip background — the only dark surface in the system.
- **Tooltip Title Text** (`#B0B8C1`): Muted label inside tooltip.
- **Tooltip Body Text** (`#FFFFFF`): Primary number/value inside tooltip.

### Chart / Data Visualization
- **Chart Line** (`#3182F6`): Single-series price line, 2.2px stroke width.
- **Chart Fill Top** (`rgba(49, 130, 246, 0.22)`): Top stop of the under-line gradient fill.
- **Chart Fill Bottom** (`rgba(49, 130, 246, 0.0)`): Bottom stop — fades to transparent.
- **Chart Grid** (`#F2F4F6`): Horizontal Y-axis grid lines only — X-axis grid is suppressed.
- **Chart Axis Text** (`#8B95A1`): Tick labels on both axes.

## 3. Typography Rules

### Font Family
- **Primary**: `Pretendard Variable`, with fallbacks: `"Pretendard", -apple-system, BlinkMacSystemFont, system-ui, "Segoe UI", Roboto, sans-serif`
- **Loading**: Pretendard is loaded via CDN: `https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.min.css` — the static version is preferred for production, the variable version for design tools.
- **OpenType Features**: `font-variant-numeric: tabular-nums` is applied to every numeric display (prices, percentages, dates, durations). `letter-spacing: -0.01em` is the body-text default.

### Hierarchy

| Role | Font | Size | Weight | Line Height | Letter Spacing | Notes |
|------|------|------|--------|-------------|----------------|-------|
| Hero Price | Pretendard | 34px | 800 | 1.15 | -0.035em | The big monetary display (`₩2,243,000`). Tabular nums. |
| Section H2 | Pretendard | 20px | 800 | 1.25 | -0.025em | Section heading (`한눈에 보기`, `핵심 이슈`). |
| Section H3 | Pretendard | 15px | 700 | 1.30 | -0.02em | Sub-heading inside section. Capitalized concept like `HBM, 독점에 가까운 지배력`. |
| Card Stat Value | Pretendard | 18px | 800 | 1.20 | -0.02em | Stat card primary value. Tabular nums. |
| Phase Title | Pretendard | 14px | 700 | 1.30 | -0.01em | Numbered phase card title (`기반 다지기`). |
| Phase Range | Pretendard | 12px | 700 | 1.25 | normal | Date+price range under phase title. Toss Blue color. Tabular nums. |
| Ticker Name | Pretendard | 17px | 700 | 1.30 | -0.015em | Company name in the hero ticker row. |
| KV Value | Pretendard | 15px | 700 | 1.30 | normal | Right-aligned values in KV-list rows. Tabular nums. |
| News Title | Pretendard | 14.5px | 700 | 1.45 | -0.01em | News item headline. |
| Body | Pretendard | 14.5px | 400 | 1.70 | -0.01em | Standard paragraph copy. Gray 700. |
| Body Strong | Pretendard | 14.5px | 700 | 1.70 | -0.01em | Bolded inline emphasis inside body. Gray 900. |
| Callout Body | Pretendard | 14px | 400 | 1.65 | -0.01em | Text inside light-blue callout block. Gray 800. |
| Risk Title | Pretendard | 14px | 700 | 1.30 | -0.01em | Risk-item card title. |
| Risk Desc | Pretendard | 13px | 400 | 1.55 | -0.01em | Risk-item card body. |
| News Source | Pretendard | 12px | 600 | 1.30 | normal | News publisher name. Toss Blue color. |
| News Date / Meta | Pretendard | 12px | 400 | 1.30 | normal | Date stamps, metadata. Tabular nums. |
| Tag | Pretendard | 12px | 600 | 1.30 | normal | Pill-tag text. |
| Stat Card Label | Pretendard | 12px | 500 | 1.30 | normal | Label above stat value. Gray 500. |
| Footer Disclaimer | Pretendard | 12px | 400 | 1.60 | -0.01em | Legal disclaimer text. |
| Change Pill | Pretendard | 12px | 700 | 1.25 | normal | The `▲ 1,007.7%` pill inside hero price block. |

### Principles
- **Numbers are louder than words**: The hero price (34px weight 800) is the single loudest element on the page. Everything else recedes to support it. This inverts the magazine convention of "headline > number" — for Toss, the number IS the headline.
- **Tabular nums everywhere**: Every numeric value uses `font-variant-numeric: tabular-nums`. This makes columns of prices, percentages, and dates align perfectly vertical — essential for KV-lists, stat grids, and news date stamps. Without it, the entire UI feels jittery.
- **Three weights only**: 400 (body), 500 (labels), 700 (titles and values), 800 (hero numbers and section titles). No 600 (semibold) and no 900 — the system uses just enough weight contrast to create hierarchy without typographic noise.
- **Negative tracking on size**: Letter-spacing tightens as size increases. -0.035em at 34px, -0.025em at 20px, -0.02em at 18px, -0.01em at body sizes, normal at 12px. The largest text feels "set in stone"; the smallest is left wide for legibility.
- **Conversational copy tone**: All body copy ends in `~예요/했어요` — soft polite Korean. Section subtitles use friendly prompts like `왜 이렇게 올랐을까?` ("Why did it rise this much?"). Never `~이다/한다` declarative. Never English-only mixed labels.
- **Hangul-first leading**: Line-height runs 1.65–1.70 on body — generous compared to Latin-only design systems — because Hangul glyphs have square bounding boxes that read tightly without breathing space.

## 4. Component Stylings

### App Bar (Sticky Top Navigation)

- Height: 52px (padding `14px 20px`)
- Background: `rgba(255,255,255,0.95)` with `backdrop-filter: saturate(180%) blur(12px)` and `-webkit-backdrop-filter` for Safari
- Border-bottom: `1px solid #F2F4F6`
- Position: `sticky; top: 0; z-index: 10;`
- Layout: flex row, `align-items: center; gap: 12px`
- Back chevron: `‹` glyph, 22px, Gray 900, 28×28px touch target
- Title: 16px Pretendard weight 700, Gray 900
- **Critical**: Backdrop blur is the *only* glassmorphism in the system. Do not use it elsewhere.

### Hero Ticker Card

The opening identity block — combines logo, name, price, change, and metadata.

- Padding: `24px 20px 28px`
- Border-bottom: `8px solid #F9FAFB` (the signature stripe — see Layout Principles)
- **Logo tile**: 44×44px, `border-radius: 12px`, filled with brand-specific gradient (e.g., SK Hynix uses `linear-gradient(135deg, #FF4040 0%, #C50019 100%)`). White text, 16px weight 800, letter-spacing -0.04em. Two characters max (e.g., "SK").
- **Ticker meta**: Stacked. Name 17px weight 700 Gray 900, code "000660 · 코스피" 12px Gray 500.
- **Price block** (18px top margin):
  - Hero price: 34px weight 800 Gray 900, tabular nums, letter-spacing -0.035em.
  - Change row: 6px top margin, inline-flex with 6px gap, 14px weight 600 Up Red color.
  - Change pill: `▲ 1,007.7%` — Up Red Bg `#FFF0F1`, Up Red text `#F04452`, 12px weight 700, padding `2px 8px`, border-radius `999px`.
  - Change delta: `+2,040,500원` — same color, no pill background.
  - Change period: `· 최근 1년` — Gray 500, weight 500, 13px.
- **Subtitle line** (16px top margin): 14px Gray 700, line-height 1.55. One sentence introducing the topic in `~했어요` tone.
- **Tag row** (16px top margin): flex-wrap with 6px gap. Mixes Tag Default and Tag Blue pills.

### Stat Card (Numerical Summary)

- Background: `#F9FAFB` (Gray 50)
- Border-radius: 14px
- Padding: 16px
- Layout: two stacked text lines — label (12px weight 500 Gray 500, 6px margin-bottom) above value (18px weight 800 Gray 900, tabular nums, letter-spacing -0.02em)
- **Variants**:
  - `--up`: Value color → Up Red `#F04452`
  - `--down`: Value color → Down Blue `#3182F6`
  - `--highlight`: Background → Toss Blue Bg `#E8F3FF`, value color → Toss Blue `#3182F6`
- Grid container: `display: grid; grid-template-columns: 1fr 1fr; gap: 8px;`
- **Do not** use heavy shadows, gradients, or borders. Background tint alone differentiates.

### Phase Card (Numbered Timeline)

A vertical stack of cards documenting sequential stages (e.g., "주가 흐름 4단계").

- Container: `display: flex; flex-direction: column; gap: 10px;`
- Each card:
  - Background: `#FFFFFF`
  - Border: `1px solid #F2F4F6`
  - Border-radius: 14px
  - Padding: 16px
  - Layout: flex row, `gap: 14px`
- **Number badge**: 28×28px, `border-radius: 8px`, background `#3182F6` Toss Blue, white text, 13px weight 800, centered. `flex-shrink: 0`.
- **Body**: flex 1, with three lines:
  - Title: 14px weight 700 Gray 900, 2px margin-bottom.
  - Range: 12px weight 700 Toss Blue, tabular nums, 6px margin-bottom (e.g., `2025.05~09 · 20만 → 35만원`)
  - Description: 13.5px weight 400 Gray 700, line-height 1.6.

### KV List (Key-Value Rows)

For numerical breakdowns like earnings tables.

- Container: `margin: 14px 0;`
- Each row:
  - `display: flex; justify-content: space-between; align-items: baseline;`
  - Padding: `14px 0`
  - Border-bottom: `1px solid #F2F4F6` (last row has `border-bottom: 0`)
- Label: 13.5px weight 500 Gray 500.
- Value: 15px weight 700 Gray 900, tabular nums, right-aligned.
- **Variants**:
  - `kv-value--up`: Up Red color
  - `kv-value--blue`: Toss Blue color
- **Critical**: Never use a vertical pipe `|`, colon `:`, or dotted leader between label and value. The space-between flex layout is the visual relationship.

### Callout (Highlighted Block)

For tagged insight or formula recaps.

- Background: `#F4F8FF` (Toss Blue Bg Soft)
- Border-left: `3px solid #3182F6`
- Border-radius: 14px (top-right and bottom-right corners) — left edge appears flush with the blue rule
- Padding: `16px 18px`
- Margin: `18px 0`
- Text: 14px weight 400 Gray 800, line-height 1.65
- Inline `<strong>` for the lead phrase, breaks via `<br>` for short list-like content

### News Item

A list of clickable news cards.

- Container: `display: flex; flex-direction: column; gap: 4px;`
- Each `<a class="news-item">`:
  - Padding: `14px 0`
  - Border-bottom: `1px solid #F2F4F6` (last item removes it)
  - `text-decoration: none; color: inherit;`
  - Layout: three stacked rows
- **Row 1 (meta)**: `display: flex; gap: 8px; font-size: 12px;`
  - Source name: weight 600 Toss Blue (e.g., "머니투데이")
  - Separator: `·` (middle dot) Gray 500
  - Date: weight 400 Gray 500, tabular nums (e.g., "2026.05.27")
- **Row 2 (title)**: 14.5px weight 700 Gray 900, line-height 1.45, 4px margin-bottom.
- **Row 3 (summary)**: 13px weight 400 Gray 700, line-height 1.5.

### Risk Item

A grid of warning/risk callouts.

- Container: `display: flex; flex-direction: column; gap: 10px;`
- Each item:
  - Background: `#F9FAFB` (Gray 50)
  - Border-radius: 12px
  - Padding: 14px
  - Layout: flex row with `gap: 12px; align-items: flex-start;`
- **Icon badge**: 24×24px, `border-radius: 7px`, background `#FFEDED`, color Up Red `#F04452`, character `!`, 13px weight 800, centered. `flex-shrink: 0`.
- **Body**: title (14px weight 700 Gray 900, 2px margin-bottom) above description (13px weight 400 Gray 700, line-height 1.55).
- **Critical**: Risks use the Up Red palette intentionally — in Korean financial UI, red = warning/alert (the same hue that means "gain" in stock context is semantically overloaded as "caution" in non-price contexts). This is a deliberate Toss convention.

### Reference Item

A list of citation links with tier badges.

- Container: `display: flex; flex-direction: column; gap: 10px;`
- Each `<a class="ref-item">`:
  - Background: `#F9FAFB`
  - Border-radius: 10px
  - Padding: `12px 14px`
  - Layout: flex row, `gap: 10px; align-items: baseline;`
- **Title**: 13px weight 600 Gray 900
- **Source line**: 13px Gray 500 (publisher + date, e.g., "TrendForce · 2026.01.28")
- **Tier badge**: `margin-left: auto;` (pushes right), background `#E5E8EB`, color Gray 700, font-size 11px weight 700, padding `2px 6px`, border-radius 5px. Single letter A/B/C indicating source reliability.

### Tag / Pill

The general-purpose categorization chip.

- Padding: `6px 12px`
- Border-radius: 999px (full pill)
- Font: 12px weight 600
- **Variants**:
  - Default: background `#F2F4F6`, color Gray 700
  - Blue: background `#E8F3FF`, color `#3182F6`
- Container: `display: flex; gap: 6px; flex-wrap: wrap;`
- **Do not** use borders on pills — they are filled-only.

### Chart (Chart.js Configuration)

Single-line price chart with under-line gradient fill.

- Container: 240px height on mobile, transparent background
- Library: Chart.js v4 (`type: 'line'`)
- Line: `borderColor: '#3182F6'`, `borderWidth: 2.2`, `tension: 0.28`
- Fill: linear gradient top→bottom, `rgba(49, 130, 246, 0.22)` → `rgba(49, 130, 246, 0.0)`
- Points: `pointRadius: 0` (hidden), `pointHoverRadius: 5` with white border on hover, Toss Blue fill
- Tooltip: dark surface `#191F28`, title color `#B0B8C1` (10px weight normal), body color `#FFFFFF` (13px weight bold), 8px corner-radius, no color swatch (`displayColors: false`), `padding: 10`
- X-axis: max 6 ticks, no grid lines, no border, 10px Pretendard Gray 500 tick text
- Y-axis: `position: 'right'` (Korean financial convention), 10px tick text, custom callback formats values as `"224만"` (divides by 10000, appends `만`), grid color `#F2F4F6`, no border
- **Critical**: Y-axis on the right side is the Korean financial chart convention — never default to left.

### Footer

- Background: `#F9FAFB`
- Padding: `24px 20px 48px`
- Margin-top: 24px
- Color: Gray 500
- Font: 12px weight 400 line-height 1.6
- Each paragraph: 6px bottom margin
- Used for legal disclaimer, generation date, data source attribution.

## 5. Layout Principles

### Spacing System
- **Base unit**: 4px
- **Scale**: 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 48
- Most common gaps: 8px (tight stacks), 14–16px (card padding), 24–28px (section padding), 48px (footer bottom)
- The 8px section-divider stripe is **not** part of the spacing scale — it's a structural element with its own role.

### Container Strategy
- **Single column, mobile-first**: The entire shell is `max-width: 560px` and centered with `margin: 0 auto`. Desktop sees the same composition as mobile, just centered with `#F9FAFB` page background showing on either side. Toss does not produce wide desktop layouts for product surfaces.
- **No multi-column grids** for content (text, news, references). The only grids are stat grids (`1fr 1fr` for 2-column number cards).
- **Edge-to-edge dividers**: Section dividers (the 8px stripes) span 100% of the shell width with no padding inset.
- **Content padding**: 20px horizontal inside sections — never 16px (too tight for Hangul) and never 24px (too generous for mobile).

### Section Structure
Every major content section follows this rhythm:
```
<hr class="divider">        ← 8px gray stripe
<section>
  <h2>Section title</h2>     ← 20px weight 800
  <p class="section-sub">    ← 13px weight 400 Gray 500
    Friendly one-line intro
  </p>
  ...content...
</section>
```

### Whitespace Philosophy
- **Banded composition**: Toss segments long-scroll content with 8px gray stripes. This means whitespace isn't dead space — it's structural. A reader scrolling sees "section, band, section, band" as a paged experience, not an infinite scroll.
- **Generous within, tight between**: Cards have generous internal padding (14–16px), but card-to-card gaps inside a list are tight (8–10px). This produces dense lists that don't feel cramped because each card itself breathes.
- **Section vertical rhythm**: 28px top padding inside a section. The 8px stripe + 28px section top = 36px between content boundaries — enough separation without feeling like wasted screen real estate on mobile.

### Border Radius Scale
- **Micro (5–7px)**: Tiny inline badges (tier letters, icon badges inside risk cards)
- **Small (8px)**: Numbered phase badges, code snippet inlines
- **Standard (10px)**: Reference cards
- **Comfortable (12px)**: Risk cards, brand logo tiles
- **Large (14px)**: Stat cards, phase cards, callouts
- **Pill (999px)**: Tags, change pills, status indicators
- **Never used**: Full circles (50% radius), squircles (smooth-corner SVG), heavy rounding beyond 16px

### Y-axis Convention (Charts)
- Korean financial charts place the Y-axis on the **right** side, not the left. This mirrors trading-screen conventions where price ticks are read against the most recent candle on the right edge. Always set `scales.y.position: 'right'` in Chart.js.

## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| Flat (Level 0) | No shadow, no border | Page background, section content blocks, footer |
| Tonal Recede (Level 1) | Background shift to `#F9FAFB` against `#FFFFFF` surroundings | Stat cards, risk cards, reference cards, footer — they "sit below" the white surface by tone alone |
| Hairline Defined (Level 1b) | `1px solid #F2F4F6` on white background | Phase cards, app bar bottom — defined edge without elevation |
| Section Band (Level 2) | 8px `#F9FAFB` full-bleed stripe between sections | The signature divider — replaces both shadows and traditional `<hr>` rules |
| Glass Surface (Level 3) | `backdrop-filter: blur(12px)` + `rgba(255,255,255,0.95)` background | Sticky app bar only — the lone glassmorphism in the system |
| Dark Overlay (Level 4) | `#191F28` solid surface, `rgba` not needed | Chart tooltips only — the only dark surface |
| Focus (Accessibility) | `2px solid #3182F6` outline on `:focus-visible` | Keyboard focus on interactive elements |

### Shadow Philosophy
**Toss has almost no traditional shadows.** Depth is communicated through tonal contrast (white vs. `#F9FAFB`) and structural devices (the 8px stripe). When a card sits on a white parent and needs definition, it gets a `#F2F4F6` hairline border — never a drop-shadow. When a card needs to recede, it adopts the `#F9FAFB` page-background fill and dissolves into the surface tone.

This is a deliberate trust signal: shadows in fintech read as "decorative," and decoration reads as "selling." Flat tonal hierarchy reads as "official document," which is what Toss wants its product surfaces to feel like — a bank statement printed on premium paper, not a marketing landing page.

### The 8px Stripe Convention
The 8px `#F9FAFB` stripe (`<hr class="divider">` styled as `height: 8px; background: #F9FAFB; border: 0;`) is Toss's **canonical section divider**. It is:
- 8px tall (not 6, not 10)
- Full-bleed (no padding inset, edge-to-edge of the shell)
- The same color as the page background — visually it reads as "the page showing through" between content cards
- Used between every major section, never decoratively
- Never replaced with a horizontal rule, never replaced with whitespace alone

## 7. Do's and Don'ts

### Do
- Use the 8px `#F9FAFB` stripe between every major section — it is the system's structural backbone
- Use Korean stock convention (up = red `#F04452`, down = blue `#3182F6`) for all Korean-market UI
- Apply `font-variant-numeric: tabular-nums` to every numeric value — prices, percentages, dates, counts
- Use Pretendard Variable as the only font family — no English-only display fonts, no serif accents
- Write product copy with `~예요/했어요` sentence endings — soft polite Korean
- Place chart Y-axis on the right side (`scales.y.position: 'right'`) — Korean financial convention
- Use tonal recede (`#F9FAFB` background) instead of drop-shadows for card hierarchy
- Use single-line section subtitles ("이렇게 올랐을까?") in Gray 500 below every H2
- Use the 4-weight Pretendard stack: 400 (body), 500 (labels), 700 (titles/values), 800 (hero numbers)
- Limit shells to `max-width: 560px` even on desktop — Toss is mobile-shaped at every viewport

### Don't
- Don't use green for "up" or red for "down" in Korean-market context — that's Western convention
- Don't use drop-shadows on cards — depth comes from tonal contrast and hairline borders, never blur
- Don't use multiple accent colors — Toss Blue `#3182F6` is the only brand color, period
- Don't use serif fonts, monospace, or non-Pretendard sans-serifs for body or display
- Don't use weight 600 (semibold) — the system goes 500 → 700 directly
- Don't use declarative Korean (`~이다/한다`) in product copy — always conversational polite (`~예요`)
- Don't replace the 8px section stripe with a 1px `<hr>` rule, gradient divider, or empty whitespace
- Don't put chart Y-axis on the left side — that's a Western charting default that breaks Korean expectations
- Don't add background colors to text paragraphs (yellow highlight, pink emphasis) — emphasis is `<strong>` weight 700 Gray 900 only
- Don't use heavy borders (`>1px`) anywhere — `1px` is the maximum stroke weight
- Don't introduce orange, green, purple, or yellow into the UI chrome — the palette is strictly white + gray scale + Toss Blue + Up Red
- Don't use `border-radius` larger than 16px on cards — Toss is "softly rounded," not "blob-shaped"
- Don't apply backdrop blur anywhere except the sticky app bar — glassmorphism is reserved
- Don't mix Korean and English in tags or labels (`AI 메모리` ✓, `AI Memory` ✗, `AI/메모리` ✗)

## 8. Responsive Behavior

### Breakpoints
| Name | Width | Key Changes |
|------|-------|-------------|
| Mobile Small | <380px | Hero price drops to 30px, stat values drop to 16px, section H2 drops to 18px |
| Mobile | 380–560px | Default layout — single column at full width, edge-to-edge content |
| Tablet+ | >560px | Shell becomes centered at `max-width: 560px`, `#F9FAFB` page background visible on either side |
| Desktop | >1024px | No layout change — shell remains 560px, just more page-background gutter |

### Touch Targets
- Tappable rows (news items, reference items): minimum 44px touch height (achieved by 14px vertical padding + content)
- Tags / pills: 28px touch height (6px vertical padding + 12px text + 6px) — borderline minimum, acceptable because tags are non-critical interactions
- App bar back button: 28×28px hit area
- Numbered phase badges: visual only, not interactive

### Collapsing Strategy
- Toss is **mobile-shaped at every viewport** — there is no "tablet layout" or "desktop layout" in the traditional sense. The shell stays 560px wide and centers.
- Stat grid stays `1fr 1fr` (2 columns) on all sizes — it does not expand to 4 columns on desktop.
- News/reference lists remain single-column on all sizes.
- The 8px section stripe scales identically — it never grows to 12px or 16px on larger screens.

### Image / Chart Behavior
- Chart container: fixed 240px height on mobile, no responsive height scaling — Chart.js handles internal width
- Brand logo tile: fixed 44×44px on all sizes
- No hero images, no full-bleed photography — Toss is a textual + numeric system, not an image-driven one

### Type Scaling
- Only the Hero Price scales: 34px → 30px below 380px viewport width
- All other type sizes are fixed — Pretendard is sharp enough at 12–14px that further scaling isn't needed
- Line-height stays constant across sizes (1.65–1.70 on body, 1.30 on titles)

## 9. Agent Prompt Guide

### Quick Color Reference
- Primary CTA / Brand: Toss Blue (`#3182F6`)
- Background (page): `#F9FAFB`
- Background (card): `#FFFFFF`
- Heading text: Gray 900 (`#191F28`)
- Body text: Gray 700 (`#4E5968`)
- Muted text / labels: Gray 500 (`#8B95A1`)
- Hairline border: Gray 100 (`#F2F4F6`)
- Up (stock gain): Up Red (`#F04452`) — Korean convention
- Down (stock loss): Toss Blue (`#3182F6`) — Korean convention
- Section divider: 8px stripe of `#F9FAFB`
- Highlight background: Toss Blue Bg (`#E8F3FF`)

### Required Setup
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.min.css">
<style>
  body {
    font-family: "Pretendard Variable", "Pretendard", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    background: #F9FAFB;
    letter-spacing: -0.01em;
  }
  .shell { max-width: 560px; margin: 0 auto; background: #FFFFFF; }
  .divider { height: 8px; background: #F9FAFB; border: 0; }
</style>
```

### Example Component Prompts

**Hero Ticker Card (Stock Header)**
> "Create a stock detail hero card. White background, 24px top padding, 20px horizontal padding, 28px bottom padding. Include: (1) a row with a 44×44px square logo tile (12px radius, gradient fill, white initials in 16px weight 800) next to a stacked company name (17px weight 700 Gray 900) + ticker code (12px Gray 500). (2) Below, a 34px weight 800 Gray 900 price with tabular-nums and -0.035em letter-spacing. (3) Below the price, a 14px weight 600 Up Red row with a `▲ percentage` pill (Up Red Bg `#FFF0F1`, Up Red text `#F04452`, 999px radius, 2px 8px padding, 12px weight 700) followed by the delta value and a `· 최근 1년` period in Gray 500 weight 500. (4) A 14px Gray 700 subtitle line. (5) A wrap-flex tag row with mixed Toss Blue Bg pills (`#E8F3FF` bg, `#3182F6` text) and Gray pills (`#F2F4F6` bg, Gray 700 text). End the card with an 8px tall `#F9FAFB` border-bottom — the signature stripe."

**Section with H2 and 8px Stripe**
> "Create a content section: precede it with `<hr style='height: 8px; background: #F9FAFB; border: 0; margin: 0;'>`. Inside the section, use 28px top padding and 20px horizontal padding. Add an H2 at 20px weight 800 Gray 900 -0.025em letter-spacing, then a one-line subtitle at 13px Gray 500 in conversational Korean (`~예요/했어요` ending) with 18px margin-bottom. Section body uses 14.5px weight 400 Gray 700 with line-height 1.70."

**Stat Card Grid**
> "Build a 2x2 stat card grid: `display: grid; grid-template-columns: 1fr 1fr; gap: 8px;`. Each card has `#F9FAFB` background, 14px border-radius, 16px padding, with a 12px weight 500 Gray 500 label above an 18px weight 800 Gray 900 value (tabular-nums, -0.02em letter-spacing). For positive returns, set value color to Up Red `#F04452`. For brand-highlighted metrics, use Toss Blue Bg `#E8F3FF` for the card and Toss Blue `#3182F6` for the value."

**Numbered Phase Card**
> "Create a vertical stack of phase cards (gap 10px). Each card: white background, `1px solid #F2F4F6` border, 14px radius, 16px padding, flex row with 14px gap. Left: 28×28px Toss Blue `#3182F6` square (8px radius) with white digit (13px weight 800). Right: stacked title (14px weight 700 Gray 900), range line (12px weight 700 Toss Blue, tabular-nums, e.g., `2025.05~09 · 20만 → 35만원`), and description (13.5px weight 400 Gray 700, line-height 1.6)."

**KV Numeric Breakdown**
> "Build a key-value list for financial data. Each row uses `display: flex; justify-content: space-between; align-items: baseline; padding: 14px 0; border-bottom: 1px solid #F2F4F6;` (last row has no bottom border). Left label: 13.5px weight 500 Gray 500. Right value: 15px weight 700 Gray 900 with tabular-nums. For up/positive values, use Up Red color. Never put a colon or dotted leader between label and value."

**Callout Block**
> "Make a callout: `#F4F8FF` background, `border-left: 3px solid #3182F6`, 14px border-radius, 16px 18px padding. Inside, 14px weight 400 Gray 800 text with line-height 1.65. Use `<strong>` for a leading phrase, then `<br>` for short multi-line content."

**News List Item**
> "Build a clickable news item as a vertical link (no decoration, color inherit). Three rows: (1) meta line — 12px row with `weight 600 Toss Blue` source name, a `·` separator in Gray 500, and a tabular-nums date in Gray 500. (2) title — 14.5px weight 700 Gray 900, line-height 1.45. (3) summary — 13px weight 400 Gray 700, line-height 1.5. Separate items with `1px solid #F2F4F6` bottom border; remove on last item."

**Risk Card**
> "Create a risk-warning card: `#F9FAFB` background, 12px radius, 14px padding, flex row with 12px gap and `align-items: flex-start`. Left: 24×24px badge (7px radius, `#FFEDED` background, `#F04452` text, `!` character, 13px weight 800). Right: title (14px weight 700 Gray 900) above description (13px weight 400 Gray 700, line-height 1.55)."

**Chart.js Price Line**
> "Configure a Chart.js v4 line chart: `borderColor: '#3182F6'`, `borderWidth: 2.2`, `tension: 0.28`, `pointRadius: 0`, `pointHoverRadius: 5`. Use a top-to-bottom gradient fill from `rgba(49, 130, 246, 0.22)` to `rgba(49, 130, 246, 0.0)`. Tooltip: dark `#191F28` background, title color `#B0B8C1` weight normal 11px, body color white 13px weight bold, no color swatch, 10px padding, 8px corner radius. X-axis: max 6 ticks, no grid, no border, 10px Gray 500 text. Y-axis: **position 'right'** (Korean convention), 10px Gray 500 text, custom callback formatting values as `(v/10000).toFixed(0) + '만'`, grid color `#F2F4F6`, no border. Set `maintainAspectRatio: false` and pin canvas height to 240px."

### Iteration Guide
1. **Always start with the 8px stripe**: Section dividers come first in the layout. Without them, the page feels like a long undifferentiated scroll.
2. **Numbers > Words**: Whenever displaying a quantity, make sure it has tabular-nums and appropriate weight contrast against its label. The hero price should be the loudest thing on the page.
3. **Korean color convention is non-negotiable**: Up = Red, Down = Blue. If targeting a Korean audience, never invert this.
4. **Tonal recede, not shadows**: When a card needs to feel "below" the surface, change its background to `#F9FAFB`. Don't reach for `box-shadow`.
5. **One accent color**: If a component needs a color beyond gray, it gets Toss Blue. If it can't justify Toss Blue, leave it gray.
6. **Conversational copy**: All product copy ends in `~예요/했어요`. Section subtitles ask friendly questions (`이렇게 올랐을까?`).
7. **Mobile shape at every viewport**: `max-width: 560px` centered. Resist the urge to "use the desktop space."
8. **The 4-weight system**: 400 → 500 → 700 → 800. No 600, no 900. Hierarchy is built on size + weight pairs, not weight alone.
9. **Tag pills, never bordered**: Filled pill backgrounds only. Outlined tags read as "form input," not "topic chip."
10. **Y-axis on the right** for any chart — a small detail that immediately signals "Korean financial UI" to native users.

---

**Maintained by**: 주홍철