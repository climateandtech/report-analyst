# Report Analyst Enterprise Components

Framework-agnostic JSON Schema form components using RJSF engine.

## Overview

This module provides JSON Schema-based form components that work across multiple frameworks:
- **Streamlit** - Python integration
- **React** - React wrapper component
- **Svelte** - Direct web component usage (no generator needed!)
- **HTML/Vanilla JS** - Direct web component usage

The core uses RJSF's (`@rjsf/utils` and `@rjsf/validator-ajv8`) for JSON Schema Draft-07 validation and processing, wrapped in a web component for framework-agnostic usage.

## Architecture

```
Web Component (json-schema-form.js)
  ├── Uses @rjsf/utils for schema processing
  ├── Uses @rjsf/validator-ajv8 for validation
  └── Framework wrappers:
      ├── Streamlit (Python)
      ├── React (TypeScript)
      └── Svelte (direct usage)
```

## Installation

### Python (Streamlit)

```bash
pip install -r report_analyst_enterprise/components/requirements.txt
```

### JavaScript/TypeScript

```bash
cd report_analyst_enterprise/components/web
npm install
```

## Usage

### Streamlit

```python
from report_analyst_enterprise.components.streamlit import json_schema_form
import json

# Load schema
with open('schemas/pdf_upload_schema.json') as f:
    schema = json.load(f)

with open('schemas/pdf_upload_ui_schema.json') as f:
    ui_schema = json.load(f)

# Render form
form_data = json_schema_form(
    schema=schema,
    ui_schema=ui_schema,
    key="pdf_upload"
)

if form_data:
    st.write("Form submitted:", form_data)
```

### React

```tsx
import { JsonSchemaForm } from '@report-analyst/components/react';
import schema from './schemas/pdf_upload_schema.json';
import uiSchema from './schemas/pdf_upload_ui_schema.json';

function App() {
  const [formData, setFormData] = useState({});
  
  return (
    <JsonSchemaForm
      schema={schema}
      uiSchema={uiSchema}
      formData={formData}
      onChange={(e) => setFormData(e.detail.formData)}
      onSubmit={(e) => console.log('Submitted:', e.detail.formData)}
    />
  );
}
```

### Svelte

```svelte
<script>
  import schema from './schemas/pdf_upload_schema.json';
  import uiSchema from './schemas/pdf_upload_ui_schema.json';
  
  let formData = {};
  
  function handleSubmit(event) {
    formData = event.detail.formData;
    console.log('Submitted:', formData);
  }
</script>

<json-schema-form
  schema={JSON.stringify(schema)}
  ui-schema={JSON.stringify(uiSchema)}
  form-data={JSON.stringify(formData)}
  on:submit={handleSubmit}
/>
```

### HTML/Vanilla JS

```html
<!DOCTYPE html>
<html>
<head>
  <script type="module" src="./json-schema-form.js"></script>
</head>
<body>
  <json-schema-form id="form"></json-schema-form>
  
  <script type="module">
    const form = document.getElementById('form');
    form.setAttribute('schema', JSON.stringify({
      type: 'object',
      properties: {
        name: { type: 'string', title: 'Name' }
      }
    }));
    
    form.addEventListener('submit', (e) => {
      console.log('Form data:', e.detail.formData);
    });
  </script>
</body>
</html>
```

## JSON Schema Support

Full JSON Schema Draft-07 support via RJSF:
- All basic types (string, number, integer, boolean, array, object, null)
- Validation keywords (required, format, pattern, minLength, maxLength, etc.)
- Composition (allOf, anyOf, oneOf, not)
- Conditional logic (if/then/else, dependencies)
- Arrays (items, additionalItems, minItems, maxItems, uniqueItems)
- Objects (properties, additionalProperties, patternProperties)
- References ($ref, $id, $anchor)

## UI Schema Support

Customize form appearance without modifying JSON Schema:
- `ui:widget` - Widget type (text, textarea, select, checkbox, radio, etc.)
- `ui:options` - Widget-specific options
- `ui:placeholder` - Placeholder text
- `ui:help` - Help text
- `ui:label` - Custom labels
- `ui:order` - Field ordering
- `ui:classNames` - CSS classes
- `ui:disabled` - Disable field
- `ui:readonly` - Readonly field

## Example Schemas

See `schemas/` directory for example schemas:
- `pdf_upload_schema.json` - PDF upload form schema (used in Streamlit app)
- `pdf_upload_ui_schema.json` - UI customization for PDF upload form
- `question_set_editor_schema.json` - Question set editor schema (for creating/editing question sets)
- `question_set_editor_ui_schema.json` - UI customization for question set editor

### Future: Question Set Editor

The question set editor schema can be used to create a visual editor for question sets in the Streamlit app, allowing users to:
- Create custom question sets
- Edit existing question sets
- Add questions with metadata (category, guidelines, etc.)
- Export/import question sets as YAML or JSON

## Web Component API

### Attributes

- `schema` - JSON Schema (stringified JSON)
- `ui-schema` - UI Schema (stringified JSON, optional)
- `form-data` - Initial form data (stringified JSON, optional)

### Events

- `change` - Fired when form data changes
  - `detail.formData` - Current form data
  - `detail.errors` - Validation errors
- `submit` - Fired when form is submitted
  - `detail.formData` - Submitted form data
- `error` - Fired when validation fails
  - `detail.errors` - Validation errors
- `validate` - Fired after validation
  - `detail.errors` - Validation errors
  - `detail.valid` - Whether form is valid

## Development

### Building Web Component

```bash
cd report_analyst_enterprise/components/web
npm install
# Add bundler if needed (e.g., Vite, Rollup)
```

### Testing

```bash
# Test Streamlit component
streamlit run test_streamlit_form.py

# Test web component
cd web
python -m http.server 8000
# Open http://localhost:8000/test.html
```

## License

See LICENSE file in parent directory.

