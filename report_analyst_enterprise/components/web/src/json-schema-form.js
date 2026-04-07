/**
 * JSON Schema Form Web Component (PoC)
 * 
 * Framework-agnostic web component that works in:
 * - Plain HTML/Vanilla JS
 * - React
 * - Svelte
 * - Streamlit (via iframe)
 * 
 * Uses React + RJSF internally but exposes a standard web component API.
 */

// Suppress React defaultProps warnings from RJSF library
// Set React to production mode to suppress development warnings
if (typeof process !== 'undefined') {
  process.env.NODE_ENV = 'production';
}
// Also filter console warnings/errors as fallback
const originalError = console.error;
const originalWarn = console.warn;
console.error = (...args) => {
  if (args.some(arg => typeof arg === 'string' && arg.includes('defaultProps'))) {
    return;
  }
  originalError.apply(console, args);
};
console.warn = (...args) => {
  if (args.some(arg => typeof arg === 'string' && arg.includes('defaultProps'))) {
    return;
  }
  originalWarn.apply(console, args);
};

import React from 'react';
import { createRoot } from 'react-dom/client';
import Form from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';

class JsonSchemaForm extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._schema = {};
    this._uiSchema = {};
    this._formData = {};
    this._reactRoot = null;
    this._container = null;
  }

  static get observedAttributes() {
    return ['schema', 'ui-schema', 'form-data'];
  }

  connectedCallback() {
    // Create container for React
    this._container = document.createElement('div');
    this._container.style.width = '100%';
    this.shadowRoot.appendChild(this._container);
    
    // Create React root
    this._reactRoot = createRoot(this._container);
    
    // Initial render
    this.render();
  }

  disconnectedCallback() {
    if (this._reactRoot) {
      this._reactRoot.unmount();
      this._reactRoot = null;
    }
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue !== newValue) {
      try {
        if (name === 'schema') {
          this._schema = newValue ? JSON.parse(newValue) : {};
        } else if (name === 'ui-schema') {
          this._uiSchema = newValue ? JSON.parse(newValue) : {};
        } else if (name === 'form-data') {
          this._formData = newValue ? JSON.parse(newValue) : {};
        }
        this.render();
      } catch (e) {
        console.error(`Error parsing ${name}:`, e);
      }
    }
  }

  // Public API: Set schema programmatically
  setSchema(schema) {
    this._schema = schema;
    this.setAttribute('schema', JSON.stringify(schema));
  }

  // Public API: Set UI schema programmatically
  setUISchema(uiSchema) {
    this._uiSchema = uiSchema;
    this.setAttribute('ui-schema', JSON.stringify(uiSchema));
  }

  // Public API: Set form data programmatically
  setFormData(formData) {
    this._formData = formData;
    this.setAttribute('form-data', JSON.stringify(formData));
  }

  // Public API: Get current form data
  getFormData() {
    return this._formData;
  }

  render() {
    if (!this._reactRoot || !this._container) {
      return;
    }

    const handleChange = ({ formData }) => {
      this._formData = formData;
      
      // Dispatch change event
      this.dispatchEvent(new CustomEvent('change', {
        detail: {
          formData: formData,
          valid: true // Could validate here if needed
        },
        bubbles: true,
        composed: true
      }));
    };

    const handleSubmit = ({ formData }) => {
      this._formData = formData;
      
      // Dispatch submit event
      this.dispatchEvent(new CustomEvent('submit', {
        detail: {
          formData: formData
        },
        bubbles: true,
        composed: true
      }));
    };

    const handleError = (errors) => {
      // Dispatch error event
      this.dispatchEvent(new CustomEvent('error', {
        detail: {
          errors: errors
        },
        bubbles: true,
        composed: true
      }));
    };

    // Render React component inside shadow DOM
    this._reactRoot.render(
      React.createElement('div', {
        style: {
          width: '100%',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
          padding: '16px'
        }
      }, [
        React.createElement('style', { key: 'styles' }, `
          :host {
            display: block;
            width: 100%;
          }
          .rjsf {
            background: #ffffff;
            border-radius: 8px;
          }
          .rjsf .form-group {
            margin-bottom: 24px;
          }
          .rjsf .form-group > label,
          .rjsf .control-label {
            font-weight: 600;
            font-size: 14px;
            color: #4313C8;
            margin-bottom: 8px;
            display: block;
          }
          .rjsf input[type="text"],
          .rjsf input[type="email"],
          .rjsf input[type="url"],
          .rjsf input[type="date"],
          .rjsf input[type="number"],
          .rjsf select,
          .rjsf textarea {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid #c0c4fa;
            border-radius: 6px;
            font-size: 14px;
            background-color: #ffffff;
            box-sizing: border-box;
          }
          .rjsf input:focus,
          .rjsf select:focus,
          .rjsf textarea:focus {
            outline: none;
            border-color: #4313C8;
            box-shadow: 0 0 0 2px rgba(67, 19, 200, 0.1);
          }
          .rjsf .btn {
            background: #4313C8;
            color: white;
            border: none;
            padding: 12px 32px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            margin-top: 16px;
          }
          .rjsf .btn:hover {
            background: #979DF6;
          }
        `),
        React.createElement(Form, {
          key: 'form',
          schema: this._schema,
          uiSchema: this._uiSchema,
          formData: this._formData,
          validator: validator,
          onChange: handleChange,
          onSubmit: handleSubmit,
          onError: handleError,
          showErrorList: false
        })
      ])
    );
  }
}

// Register the custom element
if (!customElements.get('json-schema-form')) {
  customElements.define('json-schema-form', JsonSchemaForm);
}

export default JsonSchemaForm;

