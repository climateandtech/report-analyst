# JSON Schema Form Web Component (PoC)

Framework-agnostic web component for rendering forms from JSON Schema. Works in **any** framework or plain HTML!

## Features

- ✅ **Framework-agnostic** - Works in React, Svelte, Vue, Angular, or plain HTML
- ✅ **JSON Schema Draft-07** - Full support via RJSF
- ✅ **UI Schema** - Customize form appearance
- ✅ **Event-based API** - Standard web component events
- ✅ **Shadow DOM** - Encapsulated styling
- ✅ **TypeScript support** - Full type definitions

## Installation

```bash
cd report_analyst_enterprise/components/web
npm install
npm run build
```

## Usage

### Plain HTML

```html
<!DOCTYPE html>
<html>
<head>
  <script type="module" src="./dist/json-schema-form.es.js"></script>
</head>
<body>
  <json-schema-form id="my-form"></json-schema-form>
  
  <script type="module">
    const form = document.getElementById('my-form');
    
    form.setAttribute('schema', JSON.stringify({
      type: 'object',
      properties: {
        name: { type: 'string', title: 'Name' }
      }
    }));
    
    form.addEventListener('submit', (e) => {
      console.log('Submitted:', e.detail.formData);
    });
  </script>
</body>
</html>
```

### React

```tsx
import { useRef, useEffect } from 'react';
import '@report-analyst/json-schema-form/dist/json-schema-form.es.js';

function MyForm() {
  const formRef = useRef(null);
  
  useEffect(() => {
    const form = formRef.current;
    form.setAttribute('schema', JSON.stringify({
      type: 'object',
      properties: {
        name: { type: 'string', title: 'Name' }
      }
    }));
    
    form.addEventListener('submit', (e) => {
      console.log('Submitted:', e.detail.formData);
    });
  }, []);
  
  return <json-schema-form ref={formRef} />;
}
```

### Svelte

```svelte
<script>
  let formElement;
  
  onMount(() => {
    formElement.setAttribute('schema', JSON.stringify({
      type: 'object',
      properties: {
        name: { type: 'string', title: 'Name' }
      }
    }));
    
    formElement.addEventListener('submit', (e) => {
      console.log('Submitted:', e.detail.formData);
    });
  });
</script>

<json-schema-form bind:this={formElement}></json-schema-form>
```

## API

### Attributes

- `schema` - JSON Schema (stringified JSON)
- `ui-schema` - UI Schema (stringified JSON, optional)
- `form-data` - Initial form data (stringified JSON, optional)

### Methods

- `setSchema(schema)` - Set schema programmatically
- `setUISchema(uiSchema)` - Set UI schema programmatically
- `setFormData(formData)` - Set form data programmatically
- `getFormData()` - Get current form data

### Events

- `change` - Fired when form data changes
  - `detail.formData` - Current form data
  - `detail.valid` - Whether form is valid
- `submit` - Fired when form is submitted
  - `detail.formData` - Submitted form data
- `error` - Fired when validation fails
  - `detail.errors` - Validation errors

## Examples

See the `examples/` directory:
- `vanilla-html.html` - Plain HTML example
- `react-example.tsx` - React integration
- `svelte-example.svelte` - Svelte integration

## Development

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview build
npm run preview
```

## Architecture

The web component uses React + RJSF internally but exposes a standard web component API:

```
Web Component (Custom Element)
  └── Shadow DOM
      └── React Root
          └── RJSF Form Component
```

This allows:
- Framework-agnostic usage (any framework can use it)
- React/RJSF power internally
- Standard web component API externally
- Shadow DOM encapsulation

## Testing

```bash
# Serve examples
python -m http.server 8000
# Open http://localhost:8000/examples/vanilla-html.html
```

## License

See LICENSE file in parent directory.
