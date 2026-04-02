# Global Workspace Configuration for OpenCode

## Available Global Dependencies

### @chenglou/pretext
Text measurement and layout library available in all projects.

**Usage in any project:**
```javascript
import { prepare, layout, prepareWithSegments, layoutWithLines } from '@chenglou/pretext';

// Basic usage
const prepared = prepare('Your text here', '16px Inter');
const { height, lineCount } = layout(prepared, 300, 20);
```

## Installation

From any new project folder:
```bash
# Link to workspace root dependencies
npm link ../../package.json

# Or install fresh
npm install @chenglou/pretext
```

## Quick Start Template

```javascript
import { prepare, layout } from '@chenglou/pretext';

const font = '16px system-ui';
const text = 'Your text content here';
const maxWidth = 300;
const lineHeight = 20;

const prepared = prepare(text, font);
const result = layout(prepared, maxWidth, lineHeight);

console.log(`Height: ${result.height}px`);
console.log(`Lines: ${result.lineCount}`);
```
