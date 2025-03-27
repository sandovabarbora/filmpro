# FILMPRO Design Document

**Project:** FILMPRO Film Production Management Application  
**Version:** 1.0  
**Date:** March 27, 2025  

---

## 1. Design Philosophy

FILMPRO's design is driven by the needs of film production professionals who require clear, efficient interfaces that present complex information in an easily digestible format. The application prioritizes:

- **Clarity over decoration** - Clean layouts that prioritize information hierarchy
- **Density with readability** - Information-dense screens that remain scannable
- **Functional aesthetics** - Visually pleasing but never at the expense of usability
- **Technical precision** - Monospaced typography that supports detailed production data
- **Reduced eye strain** - Dark theme optimized for both on-set and office environments

The interface balances the technical requirements of production management with an aesthetic that feels appropriate for creative professionals.

---

## 2. Color Palette

### Primary Colors

| Purpose | Color | Hex Code |
|---------|-------|----------|
| Background (Primary) | Dark Gray/Black | `#0F1117` |
| Background (Secondary) | Darker Gray | `#06070A` |
| Container Background | Dark Gray | `#14161F` |
| Text (Primary) | Off-White | `#E2E4ED` |
| Text (Secondary) | Medium Gray | `#6D7183` |
| Brand/Accent | Blue | `#3B82F6` |

### Secondary Colors

| Purpose | Color | Hex Code |
|---------|-------|----------|
| Success/Approved | Green | `#22C55E` |
| Warning/Pending | Amber | `#F59E0B` |
| Error/Alert | Red | `#EF4444` |
| Info/Note | Purple | `#8B5CF6` |

### UI Element Colors

| Element | Background | Border | Text |
|---------|------------|--------|------|
| Cards | `#14161F` | `#1C1F2E` | `#E2E4ED` |
| Buttons (Primary) | `#3B82F6` | N/A | `#FFFFFF` |
| Buttons (Secondary) | `#14161F` | `#1C1F2E` | `#6D7183` |
| Form Controls | `#14161F` | `#1C1F2E` | `#E2E4ED` |
| Navigation (Active) | `#14161F` | N/A | `#3B82F6` |
| Navigation (Inactive) | Transparent | N/A | `#6D7183` |

### Status Indicators

Status indicators use a 10% opacity background of their respective colors with 30% opacity borders and full opacity text:

- Approved/Complete: Green (`#22C55E`) with transparency
- In Progress/Pending: Amber (`#F59E0B`) with transparency 
- Warning/Issue: Red (`#EF4444`) with transparency
- Information: Blue (`#3B82F6`) with transparency

---

## 3. Typography

### Font Family

The entire application uses **JetBrains Mono**, a monospaced font that provides:

- Technical precision for values, times, and measurements
- Clear readability for complex production information
- Distinct characters that reduce reading errors in critical data
- Consistent spacing for tabular data and code-like elements

### Type Scale

| Element | Size | Weight | Case | Color |
|---------|------|--------|------|-------|
| Page Titles | 18px (1.125rem) | Medium (500) | Normal | `#E2E4ED` |
| Section Headers | 16px (1rem) | Medium (500) | Normal | `#E2E4ED` |
| Card Titles | 14px (0.875rem) | Medium (500) | Normal | `#E2E4ED` |
| Body Text | 14px (0.875rem) | Regular (400) | Normal | `#E2E4ED` |
| Secondary Text | 13px (0.8125rem) | Regular (400) | Normal | `#6D7183` |
| Small/Caption | 12px (0.75rem) | Regular (400) | Normal | `#6D7183` |
| Labels/Categories | 11px (0.6875rem) | Medium (500) | Uppercase | `#6D7183` |

### Typographic Rules

- Line height: 1.5 for body text, 1.3 for headings
- Letter spacing: Default for most text, +0.05em for labels and uppercase text
- Text truncation: Ellipsis for single-line truncation, line clamping for multi-line
- Number formatting: Consistent decimal places and thousand separators
- Date formatting: Consistent "MMM D, YYYY" format (e.g., "Mar 27, 2025")

---

## 4. Layout Structure

### Global Structure

The application follows a consistent layout structure:

1. **Fixed Sidebar** (width: 64px)
   - App icon/logo at top
   - Primary navigation icons
   - Always visible on all screens

2. **Main Content Area** (full width minus sidebar)
   - Top navigation bar with page title and user controls
   - Control bar with filters, search, and primary actions
   - Content area (page-specific)
   - Status bar (when applicable)

### Grid System

- Base grid: 12-column grid system
- Gutters: 24px (1.5rem) between grid columns
- Margins: 24px (1.5rem) padding from edges of screen
- Card padding: 16px (1rem) internal padding for cards and containers

### Responsive Breakpoints

| Breakpoint | Size | Layout Changes |
|------------|------|----------------|
| Small | < 640px | Single column layout, stacked controls |
| Medium | 640px - 768px | 2-column grid for cards, inline controls |
| Large | 768px - 1024px | Multi-column layouts, expanded content |
| Extra Large | > 1024px | Full desktop experience, dashboard layouts |

---

## 5. Common Components

### Cards

Cards are the primary containers for content with:
- Background: `#14161F`
- Border: 1px solid `#1C1F2E`
- Border radius: 8px
- Shadow: none by default, subtle shadow on hover
- Padding: 16px (1rem) internal padding
- Hover state: Subtle border color change to `#2F3446`

### Buttons

#### Primary Button
- Background: `#3B82F6` (Blue)
- Text: White
- Border radius: 4px
- Padding: 8px 16px (0.5rem 1rem)
- Hover state: Slightly darker blue
- Icon placement: Left aligned, 16px size, 8px spacing

#### Secondary Button
- Background: `#14161F`
- Text: `#6D7183`
- Border: 1px solid `#1C1F2E`
- Border radius: 4px
- Padding: 8px 16px (0.5rem 1rem)
- Hover state: Background `#1C1F2E`

### Form Controls

#### Text Input
- Background: `#14161F`
- Border: 1px solid `#1C1F2E`
- Border radius: 8px
- Text color: `#E2E4ED`
- Placeholder color: `#6D7183`
- Focus state: Border `#3B82F6`
- Size: 36px height for standard inputs

#### Select/Dropdown
- Same styling as text inputs
- Chevron indicator for dropdown functionality
- Dropdown menu same styling as cards

### Status Tags/Pills

- Border radius: 12px (fully rounded)
- Padding: 4px 8px
- Border: 1px solid color at 30% opacity
- Background: color at 10% opacity
- Text: color at 100% opacity
- Icon: Left-aligned, same color as text

### Data Tables

- Header background: `#14161F`
- Header text: Uppercase, `#6D7183`
- Row border: 1px solid `#1C1F2E`
- Hover state: Background `#1C1F2E` at 30% opacity
- Alternating rows: None
- Cell padding: 12px 16px

---

## 6. Page-Specific Elements

### Dashboard

- Key metrics: 4-column layout with colored icons
- Charts: Muted grid lines, color-coded datasets
- Activity feed: Timeline style with user avatars
- Quick access: 2x2 grid of action buttons

### Script Breakdown

- Two-panel layout: Script text left, breakdown elements right
- Script formatting: Character names bold, stage directions in gray
- Element tagging: Color-coded by element type
- Scene list: Left sidebar with progress indicators

### Calendar/Schedule

- Week view: Default view with day columns
- Time markers: Left axis with hour indicators
- Event cards: Color-coded by event type, pill-shaped
- Timeline: Visual indicators for current time and date

### Asset Management

- Grid view: Card-based with 16:9 thumbnails
- List view: Row-based with compact information
- Preview mode: Lightbox-style image/video viewing
- Metadata display: Key-value pairs below assets

### Budget Management

- Budget cards: Key financial metrics with trend indicators
- Category breakdown: Bar chart visualization
- Line item table: Detailed budget vs. actual
- Variance visualization: Color-coded based on over/under budget

### Team Management

- Personnel cards: Photo/avatar, contact details, status
- Department grouping: Color-coded by department
- Availability indicators: Status dots for availability
- Contact methods: Quick action buttons for communication

### Locations Management

- Location cards: Photo thumbnails with address details
- Map integration: Interactive location maps
- Permit status: Color-coded approval indicators
- Schedule integration: Calendar links for shooting days

### Reports & Analytics

- Data visualizations: Line, bar, and pie charts with consistent styling
- Metrics dashboard: Key indicators with trend data
- Report cards: Document-style report previews
- Export options: PDF, Excel, CSV formats

---

## 7. Interaction Patterns

### Navigation

- Section navigation: Icon sidebar with hover tooltips
- Breadcrumb navigation: For deeply nested content
- Tab navigation: For related content within a section
- Back navigation: For drill-down flows

### Actions

- Primary actions: Blue button, top right of content areas
- Secondary actions: Text button or icon button
- Bulk actions: Appear when items are selected
- Contextual actions: Appear on hover for list/grid items

### Feedback

- Success: Green toast notification, top right
- Error: Red toast notification, top right
- Warning: Amber toast notification, top right
- Progress: Blue progress indicators for long operations

### Data Entry

- Inline editing: Direct manipulation of fields when possible
- Form submission: Explicit save/cancel actions
- Validation: Immediate field-level validation
- Auto-save: Background saving with status indicators for documents

### Filtering & Sorting

- Filter controls: Dropdown or popover with multiple options
- Sort controls: Column headers for tables
- Search: Global search and context-specific search
- View options: Grid/list toggle for content areas

---

## 8. Responsive Behavior

### Mobile Adaptations

- Sidebar: Collapses to bottom navigation
- Tables: Horizontal scrolling with fixed first column
- Multi-column layouts: Stack to single column
- Forms: Full-width inputs and controls

### Tablet Adaptations

- Sidebar: Collapsible with hamburger menu
- Layouts: 2-column grid for most content
- Split-panes: Toggle between panes rather than side-by-side
- Controls: Maintain horizontal control bars

### Touch Optimization

- Tap targets: Minimum 44px × 44px
- Swipe actions: For list items and navigation
- Gestures: Pinch-zoom for images and maps
- Long-press: For contextual menus

---

## 9. Implementation Notes

### Development Guidelines

- Use CSS variables for all colors and spacing
- Component-based architecture for all UI elements
- Support dark mode only (no light mode variant)
- Implement responsive designs using Tailwind breakpoints
- Ensure all interactive elements have appropriate focus states

### Accessibility Considerations

- Sufficient color contrast (WCAG AA compliance)
- Keyboard navigation support
- Screen reader compatibility
- Focus management for modals and complex widgets
- Text alternatives for all visual information

### Performance Optimization

- Lazy loading for off-screen content
- Image optimization for thumbnails and previews
- Code splitting for page-specific components
- Virtualization for long lists and data tables
- Memoization for expensive calculations and renders

---

## 10. Page Directory

The application includes the following key pages, each designed with the specific needs of film production workflows in mind:

1. **Dashboard** - Overview of production status, tasks, and metrics
2. **Script Breakdown** - Script analysis and element tagging
3. **Calendar/Schedule** - Production schedule with scene and resource allocation
4. **Asset Management** - Media and file management for production assets
5. **Budget Management** - Financial tracking, reporting, and analysis
6. **Team Management** - Crew and cast management with availability tracking
7. **Locations Management** - Location scouting, management, and scheduling
8. **Reports & Analytics** - Production metrics and performance reporting

Each page follows the global design principles while addressing the specific workflow needs of that production area.

---

This design document serves as the definitive reference for FILMPRO's visual design, interaction patterns, and implementation guidelines. All development work should adhere to these specifications to ensure a consistent, high-quality user experience across the application.