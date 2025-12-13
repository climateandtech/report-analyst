"""
Example usage of JSON Schema form in Streamlit.

This demonstrates how to use the PDF upload form component.
"""

import json
import streamlit as st
from pathlib import Path

# Import the component
from report_analyst_enterprise.components.streamlit import json_schema_form

# Load schemas
SCHEMA_DIR = Path(__file__).parent / "schemas"

def load_schema(name: str) -> dict:
    """Load a JSON schema file."""
    with open(SCHEMA_DIR / f"{name}.json", "r") as f:
        return json.load(f)

def main():
    st.title("PDF Upload Form Example")
    st.markdown("This form is generated from JSON Schema using the web component.")
    
    # Load schemas
    schema = load_schema("pdf_upload_schema")
    ui_schema = load_schema("pdf_upload_ui_schema")
    
    # Render form
    form_data = json_schema_form(
        schema=schema,
        ui_schema=ui_schema,
        key="pdf_upload_form",
        height=700
    )
    
    # Display results
    if form_data:
        st.success("Form submitted successfully!")
        st.json(form_data)
        
        # You can now use form_data to process the upload
        st.write("### Form Data Summary")
        st.write(f"**Filename:** {form_data.get('filename', 'N/A')}")
        st.write(f"**Category:** {form_data.get('category', 'N/A')}")
        st.write(f"**Tags:** {', '.join(form_data.get('tags', []))}")
        if form_data.get('description'):
            st.write(f"**Description:** {form_data.get('description')}")
        if form_data.get('year'):
            st.write(f"**Year:** {form_data.get('year')}")

if __name__ == "__main__":
    main()


