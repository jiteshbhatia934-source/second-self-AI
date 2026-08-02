---
kind: frontend_style
name: Standalone HTML Graph Visualization with CSS Design Tokens
category: frontend_style
scope:
    - '**'
source_files:
    - static/graph.html
---

The frontend style in this repository is minimal and centered around a single standalone HTML file: `static/graph.html`, which renders an interactive knowledge graph visualization using the vis-network library. There is no CSS framework, component library, or build toolchain — styling is implemented entirely through inline `<style>` blocks within the HTML file.

**System/Approach:**
- Single-file HTML application with embedded CSS and JavaScript
- Uses vis-network v9.1.9 (loaded from unpkg CDN) for force-directed graph rendering
- Google Fonts (Inter family) loaded via preconnect links
- No CSS preprocessors, no CSS-in-JS, no component framework
- Styled as a dark-themed dashboard with glassmorphism effects (backdrop-filter blur)

**Design Token System:**
The file defines a comprehensive CSS custom properties system under `:root`:
- Color palette: dark background (`--bg: #07101f`), panel/card surfaces with transparency, text hierarchy (`--text`, `--muted`, `--faint`), accent colors (`--sky`, `--indigo`, `--rose`)
- PARA-specific semantic colors for Projects, Areas, Resources, and Archives categories
- Spacing and radius tokens (`--sidebar-w`, `--r-sm`, `--r-md`) and transition timing (`--t`)

**Architecture & Conventions:**
- All styles are scoped to specific IDs and classes within the single page
- CSS follows BEM-like naming conventions (`.sb-header`, `.d-title`, `.d-badge`, `.f-btn`)
- Dark theme is consistent throughout with semi-transparent panels and subtle borders
- Responsive behavior is limited but uses flexbox layout with fixed sidebar width
- The visualization adapts to both standalone HTTP server usage and Streamlit embedding via `__INLINE_GRAPH_DATA__` injection

**Constraints & Patterns:**
- Inline-only styling — no external CSS files
- CSS variables are used consistently for theming rather than hardcoded values
- Glassmorphism effect applied via `backdrop-filter: blur(16px)` on panels
- Custom scrollbar styling for WebKit browsers
- Tooltip styling overrides vis-network defaults for visual consistency
- Search and filter interactions use vanilla JavaScript without frameworks
- Error states display styled fallback messages when data loading fails