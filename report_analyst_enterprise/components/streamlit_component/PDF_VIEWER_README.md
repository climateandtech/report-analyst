# PDF Viewer Component with Chunks

A Streamlit custom component that displays PDFs with chunk annotations, allowing users to view chunks per question and filter by evidence.

## Features

- **PDF Display**: Renders PDF documents using PDF.js
- **Chunk Annotations**: Shows chunks associated with each question
- **Evidence Filtering**: Filter to show only evidence chunks
- **Question Navigation**: Select a question to see its associated chunks
- **Page Navigation**: Navigate to specific pages and see chunk highlights
- **Works Standalone**: Can be used outside Streamlit as a web component

## Architecture

The component follows a three-layer architecture:

1. **Web Component** (`web/src/pdf-viewer.js`): Framework-agnostic web component using PDF.js directly (not using streamlit-pdf-viewer repo - we built our own)
2. **React Wrapper** (`frontend/src/pdf-viewer.tsx`): React component that wraps the web component for Streamlit
3. **Streamlit Backend** (`backend/pdf_viewer.py`): Python interface for Streamlit

**Note**: This is a custom implementation built from scratch using PDF.js. We do not use or depend on the streamlit-pdf-viewer repository. We use PDF.js (the same underlying library) but have built our own component specifically for displaying chunks per question with evidence filtering.

## Development Setup

### Prerequisites

- Node.js and npm
- Python with Streamlit

### Building the Component

1. **Build the web component** (framework-agnostic):
```bash
cd report_analyst_enterprise/components/web
npm install
npm run build
```

This creates `dist/pdf-viewer.es.js` which is used by both standalone and Streamlit versions.

2. **Build the Streamlit component**:
```bash
cd report_analyst_enterprise/components/streamlit_component/frontend
npm install
npm run build:pdf-viewer
```

### Development Mode

For hot-reload during development:

1. **Start the PDF viewer dev server** (in one terminal):
```bash
cd report_analyst_enterprise/components/streamlit_component/frontend
npm run dev:pdf-viewer
```

This starts a dev server on port 3002.

2. **Run your Streamlit app** (in another terminal):
```bash
streamlit run report_analyst/streamlit_app.py
```

The component will automatically use the dev server if it's running.

## Usage in Streamlit

```python
from report_analyst_enterprise.components.streamlit_component.backend import pdf_viewer

# Prepare data
chunks_by_question = {
    "q1": [
        {
            "text": "Chunk text...",
            "metadata": {"page_number": 1},
            "is_evidence": True,
            "similarity_score": 0.85,
            "llm_score": 0.92,
            "chunk_order": 0
        }
    ]
}

questions_data = {
    "q1": "How does the organization identify climate risks?"
}

# Display the component
pdf_viewer(
    pdf_path="/path/to/document.pdf",
    chunks_data=chunks_by_question,
    questions_data=questions_data,
    selected_question_id="q1",  # Optional
    show_evidence_only=False,    # Optional
    height=800,
    key="my_pdf_viewer"
)
```

## Standalone Usage

The web component can be used outside Streamlit. See `web/examples/pdf-viewer-standalone.html` for an example.

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
</head>
<body>
    <pdf-viewer-with-chunks
        id="viewer"
        pdf-url="path/to/document.pdf"
        chunks='[...]'
        questions='[...]'
    ></pdf-viewer-with-chunks>
    
    <script type="module">
        import PdfViewerWithChunks from './dist/pdf-viewer.es.js';
        // Use the component
    </script>
</body>
</html>
```

## Data Format

### Chunks

Each chunk should have:
- `text`: The chunk text content
- `metadata`: Object containing metadata (should include `page_number`)
- `is_evidence`: Boolean indicating if this chunk is evidence
- `similarity_score`: Float similarity score
- `llm_score`: Optional float LLM relevance score
- `chunk_order`: Integer position of chunk

### Questions

Questions should be provided as a dictionary mapping question_id to question text:
```python
{
    "q1": "Question text here",
    "q2": "Another question..."
}
```

## Integration with Streamlit App

The component is integrated into `report_analyst/streamlit_app.py` in the `display_analysis_results()` function. It automatically appears when:
- The PDF viewer component is available (enterprise feature)
- A file path is provided
- Chunks data is available

The component appears in an expander section titled "📄 PDF Viewer with Chunks".

## Troubleshooting

### Component not loading

1. Check that the dev server is running (for development) or the component is built (for production)
2. Check browser console for errors
3. Verify PDF.js is loading correctly

### PDF not displaying

1. Check that the PDF path is correct and accessible
2. For local files, ensure the path is absolute or relative to the Streamlit app
3. Check browser console for PDF.js errors

### Chunks not showing

1. Verify chunks data format matches the expected structure
2. Check that `page_number` is included in chunk metadata
3. Verify questions data is provided correctly


