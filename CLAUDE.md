# Project context for LLMs

This repo is the **BrickSight — Genie Code for Data Engineers** demo. It plays back a recorded Databricks Genie Code session in the browser via the [rehearseur](https://github.com/lbruand/rehearseur) React component, with a markdown annotations file driving voiceover cues and driver.js popovers.

Live site: https://lbruand-db.github.io/genie-code-for-dataeng-demo/ (built and deployed by `.github/workflows/deploy.yml` on every push to `main`).

## Key files

- `public/bricksight_demo.json` — the rrweb event log (22 MB, ~10k events, 8:18 long after a 2× acceleration). Top-level shape is `{ session, events: [...] }` — when you parse it, the events array is at `data["events"]`, not the root.
- `public/bricksight_demo.annotations.md` — voiceover beats, autopause cues, and `driverjs` popover code blocks pinned to real timestamps in the recording.
- `SPECS/DEMOSCRIPT.md` — the live voiceover script, segment by segment. Source of truth for what the presenter says at each ★ proof point.
- `SPECS/SPEC.md` — overall demo design.
- `src/App.jsx` — loads the two files above into `RrwebPlayer`.
- `setup/` — Unity Catalog seed scripts (data download, catalog/schema creation, semantic metadata).
- `skills/brickvault_analyst_skill.md` — reference output for the Segment 3 skill-file generation.

## Conventions specific to this repo

- **Timestamps in the annotations file are anchored to real signals in the recording**, not proportional estimates. When adding or moving annotations, find the actual on-screen beat by scanning `events[*].timestamp` for the relevant text (prompt strings, column names, etc.) and use the offset from `events[0].timestamp`. See git history of `bricksight_demo.annotations.md` for prior anchor work.
- **driver.js popovers** are written as fenced ` ```driverjs ` code blocks inside an annotation body. They use `driverObj.highlight({ popover: {...} })` with `align: 'center'` for element-less modals; swap in `element: createPhantom('<selector>')` to anchor to a DOM node.
- **Filenames** in `src/App.jsx` are relative (no leading `/`) so they work both at local dev `/` and at the GitHub Pages base `/genie-code-for-dataeng-demo/`. The `base` path is set in `vite.config.js` gated on the `GITHUB_PAGES` env var.
- The recording was 2×-accelerated once already (997s → 499s). Apply further speed changes proportionally and also update annotation timestamps.

## rrweb Recording JSON Format

rrweb (record and replay the web) recordings are JSON files containing an array of events that capture DOM changes and user interactions over time.

### Basic Structure

```json
[
  {
    "type": 0,
    "data": {},
    "timestamp": 1234567890123
  },
  {
    "type": 2,
    "data": {},
    "timestamp": 1234567891456
  }
]
```

Each event has:
- **`type`** - Event type (integer)
- **`data`** - Event-specific payload (object)
- **`timestamp`** - Unix timestamp in milliseconds (integer)

### Event Types

| Type | Name | Description |
|------|------|-------------|
| 0 | DomContentLoaded | Initial full DOM snapshot |
| 1 | Load | Page load complete |
| 2 | FullSnapshot | Complete DOM state capture |
| 3 | IncrementalSnapshot | Incremental DOM mutations |
| 4 | Meta | Metadata (viewport, URLs) |
| 5 | Custom | Custom application events |
| 6 | Plugin | Plugin-specific events |

### Common Event Data Structures

#### Type 0/2: Full Snapshot
```json
{
  "type": 2,
  "data": {
    "node": {
      "type": 0,
      "childNodes": [...],
      "id": 1
    },
    "initialOffset": {
      "top": 0,
      "left": 0
    }
  },
  "timestamp": 1234567890123
}
```

#### Type 3: Incremental Snapshot
```json
{
  "type": 3,
  "data": {
    "source": 2,  // MouseMove=0, MouseInteraction=1, Scroll=2, ViewportResize=3, Input=4, etc.
    "positions": [...],  // For mouse movements
    "id": 123,  // Target element ID
    "x": 100,
    "y": 200
  },
  "timestamp": 1234567891456
}
```

#### Type 4: Meta
```json
{
  "type": 4,
  "data": {
    "href": "https://example.com",
    "width": 1920,
    "height": 1080
  },
  "timestamp": 1234567890123
}
```

### Incremental Snapshot Sources

The `source` field in Type 3 events indicates what kind of incremental change occurred. **Important:** this enum has shifted across rrweb versions — the table below matches the recorder version used in this repo (verified against `public/bricksight_demo.json`):

- **0** - Mutation (DOM adds/removes/attribute/text changes — this is the dominant event in a real recording)
- **1** - MouseMove
- **2** - MouseInteraction (click, dblclick, mousedown, mouseup, etc.)
- **3** - Scroll
- **4** - ViewportResize
- **5** - Input (text input, checkbox, radio, select)
- **6** - TouchMove
- **7** - MediaInteraction
- **8** - StyleSheetRule
- **9** - CanvasMutation
- **10** - Font
- **11** - Log
- **12** - Drag
- **13** - StyleDeclaration
- **14** - Selection
- **15** - AdoptedStyleSheet
- **16** - CustomElement

When in doubt, dump a handful of events and inspect `data` keys — Mutation events carry `adds`/`removes`/`texts`/`attributes`, Scroll events carry `id`/`x`/`y`, Input events carry `text`/`isChecked`, etc.

## Modifying rrweb Recordings with LLMs

### 1. Clean Up Sensitive Data

Remove passwords, personal information, or API keys from the recording.

**Task:** Scan events for sensitive data and redact it.

**Targets:**
- Type 3 events with `source: 4` (Input events)
- Look for `data.text` or `data.value` fields
- Search for patterns: emails, passwords, tokens, credit cards

**Example modification:**
```json
// Before
{
  "type": 3,
  "data": {
    "source": 4,
    "text": "user@example.com",
    "id": 45
  },
  "timestamp": 1234567891456
}

// After
{
  "type": 3,
  "data": {
    "source": 4,
    "text": "[REDACTED]",
    "id": 45
  },
  "timestamp": 1234567891456
}
```

### 2. Edit or Remove Events

Remove unwanted portions of the recording.

**Task:** Filter out events within a timestamp range.

**Example:**
```
Remove all events between timestamps 1234567890000 and 1234570000000
```

**Implementation:** Filter the array to exclude events where `timestamp` falls within the range.

### 3. Inject Synthetic Events

Add artificial events to demonstrate scenarios.

**Task:** Insert a new event at a specific timestamp.

**Example - Adding a click event:**
```json
{
  "type": 3,
  "data": {
    "source": 1,  // MouseInteraction
    "type": 2,    // Click (0=mouseup, 1=mousedown, 2=click, etc.)
    "id": 123,    // Element ID to click
    "x": 100,
    "y": 200
  },
  "timestamp": 1234575000
}
```

**Important:** Insert the event in chronological order (sorted by timestamp).

### 4. Speed Up or Slow Down Sections

Modify timestamps to change playback speed.

**Task:** Adjust timestamps in a specific range to compress/expand time.

**Example - 2x speed (compress by half):**
```
For events between timestamp 1234570000 and 1234572000:
- Calculate original duration: 2000ms
- New duration: 1000ms (half)
- Recalculate each event's timestamp proportionally
```

**Algorithm:**
```javascript
const start = 1234570000;
const end = 1234572000;
const speedFactor = 0.5; // 2x speed = compress to 50%

events.forEach(event => {
  if (event.timestamp >= start && event.timestamp <= end) {
    const offset = event.timestamp - start;
    event.timestamp = start + (offset * speedFactor);
  } else if (event.timestamp > end) {
    // Shift all events after the range
    event.timestamp -= (end - start) * (1 - speedFactor);
  }
});
```

### 5. Working with Large Files: TOON Format

rrweb recording JSON files can be very large (several MB) and may exceed LLM context limits or consume excessive tokens.

**Solution:** Use [TOON format](https://github.com/toon-format/toon) (Token-Oriented Object Notation).

**Benefits:**
- **40% fewer tokens** than standard JSON
- **Human-readable** YAML-like indentation with CSV-style tables
- **Lossless** conversion (preserves all data perfectly)
- **Better LLM accuracy** (73.9% vs 70.7% for JSON)
- **Easier editing** - More compact structure

**Conversion Commands:**

```bash
# JSON to TOON
npx @toon-format/cli public/bricksight_demo.json -o bricksight_demo.toon

# TOON to JSON
npx @toon-format/cli bricksight_demo.toon -o public/bricksight_demo.json

# Pipe to stdin/stdout
cat bricksight_demo.toon | npx @toon-format/cli > bricksight_demo.json
```

**Workflow:**
1. Convert large JSON to TOON format
2. Provide TOON file to LLM for modification
3. LLM edits TOON (easier to read/modify)
4. Convert back to JSON

**Example TOON structure:**
```toon
- type, data, timestamp
0, {node: {...}}, 1234567890123
3, {source: 2, positions: [...]}, 1234567891456
3, {source: 4, text: "input"}, 1234567892789
```

## Best Practices

### Validation
- **Preserve JSON structure** - Ensure the output is valid JSON
- **Sort by timestamp** - Events must be in chronological order
- **Check event types** - Use correct type integers (0-6)
- **Validate data fields** - Each event type expects specific data structure

### Safety
- **Backup originals** - Always keep a copy before modifications
- **Test playback** - Verify modified recordings play correctly
- **Incremental changes** - Make small modifications and test
- **Chunk large files** - Split or use TOON format for large recordings

### Common Mistakes to Avoid
- Breaking timestamp ordering
- Using incorrect event type numbers
- Modifying element IDs (breaks references)
- Creating orphaned events (referencing non-existent elements)
- Inconsistent source types in incremental snapshots

## Example Prompts for LLM Processing

### Generate Annotations
```
I have an rrweb recording. Please analyze the events and create
a markdown annotations file with bookmarks for key moments like:
- Page loads (type 0, 1, 2, 4)
- Form submissions (type 3, source 4)
- Button clicks (type 3, source 1)
- Navigations (type 4 with href changes)

Format each bookmark with timestamp, color, and description.
```

### Redact Sensitive Data
```
Please scan this rrweb recording and redact sensitive information:
- Password fields (type 3, source 4, look for password-related IDs)
- Email addresses (in text/value fields)
- API tokens (in any text data)

Replace with "[REDACTED]" and preserve the event structure.
```

### Edit Timeline
```
Remove all events between timestamps X and Y from this rrweb recording.
Ensure the remaining events maintain chronological order and
adjust any relative timestamps if needed.
```

## Resources

- [rrweb Documentation](https://github.com/rrweb-io/rrweb/blob/master/guide.md)
- [rrweb Event Types Guide](https://github.com/rrweb-io/rrweb/blob/master/docs/recipes/event-types.md)
- [TOON Format](https://toonformat.dev/)
- [TOON CLI](https://toonformat.dev/cli/)