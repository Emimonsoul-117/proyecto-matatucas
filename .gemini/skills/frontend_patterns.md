# Frontend Patterns & CDN Dependencies - Matatucas LMS

## Template Hierarchy
```
base.html
├── Navigation (responsive, role-aware)
├── Flash messages (auto-dismiss)
├── Content block
└── Footer

All pages extend base.html via {% extends "base.html" %}
```

## CDN Dependencies (loaded in base.html)
| Library | Version | Purpose |
|---------|---------|---------|
| Bootstrap | 5.3.x | Layout, components, responsive grid |
| Bootstrap Icons | 1.11.x | Icon system (bi-*) |
| KaTeX | latest | Math equation rendering |
| SortableJS | 1.15.7 | Drag-and-drop reordering |
| Chart.js | 4.x | Analytics charts (admin metrics) |
| Google Fonts (Inter) | - | Typography |

## CSS Design System (index.css)
```css
/* Primary brand colors from TecNM color palette */
--primary-brand: #003366;      /* Navy blue */
--primary-brand-light: #1a5276;
--primary-accent: #2980b9;     /* Bright blue */
--bg-light: #f8fafc;
--text-primary: #1e293b;
--text-secondary: #64748b;
```

## Animation Classes
- `.animate-fade-in` — Entry fade for page sections
- `.animate-slide-up` — Slide up for cards
- Transition: `all 0.2s` on interactive elements (hover effects)

## Component Patterns

### Metric Cards
```html
<div class="metric-card">
    <div class="metric-icon" style="background: #color; color: #color;">
        <i class="bi bi-icon-name"></i>
    </div>
    <div>
        <div class="text-muted small">Label</div>
        <div class="fw-bold fs-4">Value</div>
    </div>
</div>
```

### Estado Badges
```html
<span class="estado-badge estado-borrador">📝 Borrador</span>
<span class="estado-badge estado-publicado">✅ Publicado</span>
```

### Flash Messages (auto mapped)
- `exito` → Bootstrap `alert-success`
- `peligro` → Bootstrap `alert-danger`
- `advertencia` → Bootstrap `alert-warning`
- `info` → Bootstrap `alert-info`

## JavaScript Patterns
- AJAX: Use `fetch()` with JSON body. Always include CSRF token:
```javascript
fetch(url, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrf_token]').value
    },
    body: JSON.stringify(data)
})
```

## Drag-and-Drop (SortableJS) Pattern
```javascript
new Sortable(container, {
    animation: 150,
    handle: '.drag-handle',        // Only drag from handle
    ghostClass: 'sortable-ghost',  // Placeholder styling
    onEnd: function(evt) {
        // POST new order to backend
        const items = container.querySelectorAll('[data-id]');
        const order = Array.from(items).map((el, i) => ({
            id: parseInt(el.dataset.id),
            orden: i + 1
        }));
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token },
            body: JSON.stringify({ orden: order })
        });
    }
});
```

## Responsive Breakpoints
- `col-md-2` — 6 cards per row on desktop
- `col-6` — 2 cards per row on mobile
- Container max-width: 1100px (courses), 1200px (dashboard)

## Accessibility
- All buttons must have `title` attributes
- Icons-only buttons need `aria-label`
- Form inputs need associated `<label>` elements
- Color contrast: minimum 4.5:1 ratio
