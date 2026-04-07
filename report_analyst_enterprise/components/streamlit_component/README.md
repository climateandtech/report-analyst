# Streamlit Custom Component for JSON Schema Form

This is a proper Streamlit custom component that wraps the `json-schema-form` web component.

## Development

### Setup

```bash
cd frontend
npm install
```

### Development Mode

```bash
# Terminal 1: Start the component dev server
npm start

# Terminal 2: Run your Streamlit app
streamlit run your_app.py
```

The component will hot-reload when you make changes.

### Build for Production

**Quick build (recommended):**
```bash
cd report_analyst_enterprise/components/streamlit_component
./build.sh
```

**Manual build:**
```bash
cd frontend
npm install
npm run build
```

This creates a `build/` directory that the backend component will use. The component will automatically use the built version if it exists.

## Architecture

- **Backend** (`backend/`): Python code that declares the component to Streamlit
- **Frontend** (`frontend/`): React component that wraps the web component and communicates with Streamlit

The frontend React component:
1. Loads the `json-schema-form` web component
2. Passes schema, UI schema, and form data as attributes
3. Listens for form events (change, submit, error)
4. Sends data back to Streamlit via `Streamlit.setComponentValue()`

## Usage

```python
from report_analyst_enterprise.components.streamlit import json_schema_form

form_data = json_schema_form(
    schema=my_schema,
    ui_schema=my_ui_schema,
    form_data=initial_data,
    key="my_form"
)

if form_data:
    st.write("Form submitted:", form_data)
```

