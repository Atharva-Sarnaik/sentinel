---
name: Aerospace Mission Control
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#45464d'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#0058be'
  on-secondary: '#ffffff'
  secondary-container: '#2170e4'
  on-secondary-container: '#fefcff'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#002113'
  on-tertiary-container: '#009668'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
  mono-data-lg:
    fontFamily: JetBrains Mono
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 28px
    letterSpacing: -0.03em
  mono-data-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: -0.02em
  mono-data-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: -0.01em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.08em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 0.75rem
  gutter-desktop: 1rem
  margin: 1rem
  margin-desktop: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style
The brand personality is disciplined, analytical, and hyper-reliable. Built specifically for high-consequence orbital operations, the interface evokes calm authority, precision instrumentation, and cognitive clarity under stress. Operators monitor critical telemetry streams, anomalies, and multi-agent coordination trees; the design eliminates visual noise, decorative ambiguity, and heavy ornamentation.

The visual style blends **Technical Minimalism** with **Aerospace Instrumentation UI**:
- Stark, crisp light mode architecture prioritizing maximum optical contrast and daylight legibility.
- Architectural micro-borders and hairline dividers replacing heavy elevation shadows.
- High-density data layouts structured around tabular efficiency, micro-badges, and instantaneous state recognition.
- Dedicated semantic signaling: chromatic restraint across the operational frame, reserving saturation strictly for telemetry status flags (Nominal, Warning, Critical, Informational).

## Colors
The palette utilizes an intentional high-contrast structural scale paired with strict, ISO-compliant telemetry status signals.

### Core Canvas & Structure
- **Canvas Base:** `#F8FAFC` (Slate 50) provides a soft, non-fatiguing cockpit backdrop.
- **Surface Panels:** `#FFFFFF` (Pure White) houses discrete operational modules and cards.
- **Hairline Dividers & Borders:** `#E2E8F0` (Slate 200) for structural grid definition; `#CBD5E1` (Slate 300) for interactive control boundaries.

### Typography & Content
- **Primary Readouts & Headers:** `#0F172A` (Slate 900) for uncompromised typographic contrast.
- **Labels, Telemetry Units, Secondary Text:** `#334155` (Slate 700).
- **Muted Metadata & Grid Lines:** `#64748B` (Slate 500) and `#94A3B8` (Slate 400).

### Telemetry Status Tokens
- **Nominal (Stable / Go):** `#10B981` (Emerald 500) with tint container `#ECFDF5` (Emerald 50) and stroke `#A7F3D0`.
- **Warning (Anomaly / Drift):** `#F59E0B` (Amber 500) with tint container `#FFFBEB` (Amber 50) and stroke `#FDE68A`.
- **Critical (Degraded / Failure):** `#EF4444` (Rose 500) with tint container `#FEF2F2` (Rose 50) and stroke `#FECACA`.
- **Informational / Uplink:** `#3B82F6` (Aerospace Blue 500) with tint container `#EFF6FF` (Blue 50) and stroke `#BFDBFE`.

## Typography
Typography is separated into two operational layers:
1. **System & Human UI (`Inter`):** Handles mission directives, structural navigation, subsystem names, modal windows, and dialogs.
2. **Precision Stream Data (`JetBrains Mono`):** Dedicated to mission elapsed time (MET), UTC coordinate frames, raw sensor numbers, telemetry vectors, hex memory dumps, and satellite IDs. Monospaced styling prevents horizontal layout jitter during continuous streaming updates.

All micro-labels (`label-caps`) must use uppercase styling with wide tracking (`0.08em`) to guarantee quick recognition on high-DPI operator monitors.

## Layout & Spacing
The layout adheres to a dense, fluid 12-column grid engine optimized for multi-screen mission consoles:
- **Desktop (>= 1440px):** 12-column dynamic grid with fixed 1rem gutters and 1.5rem outer canvas padding. Views stay full-width to provide unobstructed visibility across charts, telemetry streams, and coordinate maps.
- **Sub-Consoles / Laptops (1024px - 1439px):** 12-column layout; secondary panels (e.g., historical audit logs) collapse into side drawers or tabbed panes.
- **Tactical Field Terminals / Mobile (< 1023px):** Single-column stacked stream. Critical orbital vectors, anomaly tickers, and communications status lock to sticky persistent top modules.

Vertical rhythm relies strictly on a 4px base increment (`0.25rem`), keeping module overhead minimal to prioritize raw information density.

## Elevation & Depth
In alignment with aerospace instrumentation principles, elevation is communicated through **structural containment, surface tonal shifts, and 1px crisp micro-borders**, not heavy blur shadows.

- **Level 0 (Canvas Base):** `#F8FAFC` flat surface.
- **Level 1 (Module Panels & Telemetry Cards):** `#FFFFFF` surface framed by a persistent `1px solid #E2E8F0` border. Zero drop-shadow in static states.
- **Level 2 (Hover / Active Context Panels):** Hairline border transitions to `#CBD5E1` with an ultra-subtle directional ambient shadow: `0 1px 3px 0 rgba(15, 23, 42, 0.05)`.
- **Level 3 (Command Modals, Overlays, Replay Controls):** `#FFFFFF` surface with `1px solid #94A3B8` border and disciplined floating shadow: `0 8px 24px -4px rgba(15, 23, 42, 0.10)`.
- **Status Glow (Critical Alert State only):** Pulsing perimeter outline using `rgba(239, 68, 68, 0.25)` micro-ring (2px spread), preventing distracting visual flashes while directing immediate operator focus.

## Shapes
Shapes are engineered with compact, subtle roundedness (`0.25rem` / `rounded-sm` up to `0.5rem` / `rounded-lg`). 

Large, soft curves are intentionally excluded to maintain high tabular density, clear grid alignment, and the feel of calibrated hardware equipment. Status pills and micro-badges employ controlled `0.25rem` containment borders rather than full circular pill ends, preserving alignment with tabular telemetry rows.

## Components

### 1. KPI Telemetry Summary Cards
- White `#FFFFFF` container with `1px solid #E2E8F0` border and `rounded-sm` geometry.
- Top section: uppercase sub-label in `label-caps` (`#64748B`), paired with an inline status dot (8px circle).
- Center: telemetry metric rendered in `mono-data-lg` (`#0F172A`) along with standard engineering units (e.g., `GHz`, `dBm`, `°C`, `km/s`) in `body-sm` (`#64748B`).
- Bottom section: 24px micro-sparkline with threshold baseline guide.

### 2. Subsystem Gauges & Radial Instruments
- Crisp linear or semi-circular progress tracks: background track `#F1F5F9`, filled indicator path mapped to the active state color (Nominal, Warning, or Critical).
- Center value rendered in `mono-data-md` with delta trend indicator (`+0.04%` / `-0.12%`).

### 3. Status Badges & Audit Integrity Flags
- High-visibility micro-tags: `padding: 2px 6px`, border radius `0.25rem`.
- **Nominal:** Background `#ECFDF5`, text `#065F46`, border `1px solid #A7F3D0`.
- **Warning:** Background `#FFFBEB`, text `#92400E`, border `1px solid #FDE68A`.
- **Critical:** Background `#FEF2F2`, text `#991B1B`, border `1px solid #FECACA`.
- **Cryptographic Audit Badge:** Monospace hash indicator with padlock icon in `#F1F5F9` background, `#334155` text, and `#CBD5E1` border.

### 4. Interactive Telemetry Time-Series Charts
- Crisp canvas surface with vertical and horizontal crosshair guides in `#E2E8F0`.
- Dual Y-axis labels rendered in `mono-data-sm`.
- Chart lines: 1.5px solid stroke with no gradient fills beneath curves to avoid visual clutter during signal overlays.
- Hover state: precise vertical tracking line with floating numeric readout tooltip.

### 5. Multi-Agent AI Coordinator / Fusion Decision Tree
- Hierarchical node cards connected via clean orthogonal 1px `#CBD5E1` vector lines.
- Node elements: Agent role header (e.g., `ORBIT-CALC-04`, `POWER-ALLOC-AI`), confidence score percentage in monospace bold, and active decision branch tags.
- Fallback/Override manual control trigger button on every critical decision node.

### 6. Replay Timeline Bar & Scrubbing Controls
- Fixed or docked bottom bar spanning the viewport width.
- Includes playback controls (Step Back 10s, Pause, Play 1x/5x/10x, Jump to Live).
- Scrub rail rendered with marked timeline bands showing anomaly sectors in light red/amber tint blocks along the time track.
- Active scrub head: vertical blue `#3B82F6` hairline flag displaying current replay timestamp in UTC.

### 7. Form Controls, Checkboxes & Inputs
- Inputs: `#FFFFFF` background, `1px solid #CBD5E1` border, `font-family: JetBrains Mono`, padding `6px 10px`. Focus ring: `0 0 0 2px rgba(59, 130, 246, 0.20)`.
- Buttons:
  - **Primary Action:** Solid `#0F172A` background, white text, 0.25rem radius.
  - **Emergency Action:** Solid `#EF4444` background, white text.
  - **Secondary / Instrument Action:** Outline style `#FFFFFF` background, `1px solid #CBD5E1`, text `#334155`.