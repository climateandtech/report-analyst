/**
 * JSON Schema Form Web Component
 * 
 * Uses RJSF utilities for JSON Schema validation and processing.
 * Framework-agnostic web component that can be used in React, Svelte, Streamlit, etc.
 */

import { getDefaultRegistry } from '@rjsf/utils';
import { createAjv8Validator } from '@rjsf/validator-ajv8';

class JsonSchemaForm extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.validator = createAjv8Validator();
    this.registry = getDefaultRegistry();
    this.formData = {};
    this.errors = [];
  }

  static get observedAttributes() {
    return ['schema', 'ui-schema', 'form-data'];
  }

  connectedCallback() {
    this.render();
    this.setupEventListeners();
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue !== newValue) {
      if (name === 'schema' || name === 'ui-schema') {
        try {
          this[name.replace('-', '_')] = JSON.parse(newValue || '{}');
        } catch (e) {
          console.error(`Error parsing ${name}:`, e);
        }
      } else if (name === 'form-data') {
        try {
          this.formData = JSON.parse(newValue || '{}');
        } catch (e) {
          console.error('Error parsing form-data:', e);
        }
      }
      this.render();
    }
  }

  setupEventListeners() {
    this.shadowRoot.addEventListener('change', (e) => this.handleChange(e));
    this.shadowRoot.addEventListener('input', (e) => this.handleInput(e));
    this.shadowRoot.addEventListener('submit', (e) => this.handleSubmit(e));
  }

  handleChange(e) {
    const field = e.target;
    const path = field.dataset.path;
    if (path) {
      this.updateFormData(path, field.value, field.type);
      this.validate();
      this.dispatchEvent(new CustomEvent('change', {
        detail: {
          formData: this.formData,
          errors: this.errors
        },
        bubbles: true
      }));
    }
  }

  handleInput(e) {
    // Handle real-time input for text fields
    this.handleChange(e);
  }

  handleSubmit(e) {
    e.preventDefault();
    if (this.validate()) {
      this.dispatchEvent(new CustomEvent('submit', {
        detail: {
          formData: this.formData
        },
        bubbles: true
      }));
    } else {
      this.dispatchEvent(new CustomEvent('error', {
        detail: {
          errors: this.errors
        },
        bubbles: true
      }));
    }
  }

  updateFormData(path, value, type) {
    const keys = path.split('.');
    let current = this.formData;
    
    for (let i = 0; i < keys.length - 1; i++) {
      const key = keys[i];
      if (!(key in current)) {
        current[key] = {};
      }
      current = current[key];
    }
    
    const lastKey = keys[keys.length - 1];
    
    // Convert value based on type
    if (type === 'number' || type === 'range') {
      value = parseFloat(value);
    } else if (type === 'checkbox') {
      value = value === 'true' || value === true;
    }
    
    current[lastKey] = value;
  }

  validate() {
    if (!this.schema) {
      this.errors = [];
      return true;
    }

    try {
      // Use RJSF validator
      const result = this.validator.validateFormData(this.formData, this.schema);
      this.errors = result.errors || [];
      
      // Format errors for display
      this.errors = this.errors.map(err => ({
        property: err.property || '',
        message: err.message || 'Validation error',
        schema: err.schema || {}
      }));
    } catch (e) {
      console.error('Validation error:', e);
      this.errors = [{ property: '', message: e.message || 'Validation failed' }];
    }
    
    this.dispatchEvent(new CustomEvent('validate', {
      detail: {
        errors: this.errors,
        valid: this.errors.length === 0
      },
      bubbles: true
    }));
    
    return this.errors.length === 0;
  }

  renderField(fieldSchema, uiSchema, path = '') {
    const { type, title, description, enum: enumValues, default: defaultValue } = fieldSchema;
    const fieldName = path.split('.').pop() || '';
    const fieldId = `field-${path.replace(/\./g, '-')}`;
    
    let html = '';
    
    // Field label
    if (title) {
      html += `<label for="${fieldId}" class="field-label">${title}</label>`;
    }
    
    // Field description
    if (description) {
      html += `<p class="field-description">${description}</p>`;
    }
    
    // Field widget based on type and UI schema
    const widget = uiSchema?.['ui:widget'] || this.getDefaultWidget(type);
    
    switch (widget) {
      case 'text':
      case 'textarea':
        html += this.renderTextarea(fieldSchema, uiSchema, fieldId, path);
        break;
      case 'select':
        html += this.renderSelect(fieldSchema, uiSchema, fieldId, path, enumValues);
        break;
      case 'checkbox':
        html += this.renderCheckbox(fieldSchema, uiSchema, fieldId, path);
        break;
      case 'radio':
        html += this.renderRadio(fieldSchema, uiSchema, fieldId, path, enumValues);
        break;
      default:
        html += this.renderInput(fieldSchema, uiSchema, fieldId, path, type);
    }
    
    // Error display
    const fieldErrors = this.errors.filter(e => {
      const errorPath = e.property || '';
      return errorPath === `.${path}` || errorPath.endsWith(`.${path}`);
    });
    if (fieldErrors.length > 0) {
      html += `<div class="field-errors">${fieldErrors.map(e => e.message || 'Error').join(', ')}</div>`;
    }
    
    return `<div class="field-wrapper" data-path="${path}">${html}</div>`;
  }

  renderInput(fieldSchema, uiSchema, fieldId, path, type) {
    const value = this.getFieldValue(path) || fieldSchema.default || '';
    const placeholder = uiSchema?.['ui:placeholder'] || '';
    const disabled = uiSchema?.['ui:disabled'] || false;
    const readonly = uiSchema?.['ui:readonly'] || false;
    
    return `
      <input
        type="${type === 'integer' ? 'number' : type}"
        id="${fieldId}"
        data-path="${path}"
        value="${value}"
        placeholder="${placeholder}"
        ${disabled ? 'disabled' : ''}
        ${readonly ? 'readonly' : ''}
        class="field-input"
      />
    `;
  }

  renderTextarea(fieldSchema, uiSchema, fieldId, path) {
    const value = this.getFieldValue(path) || fieldSchema.default || '';
    const placeholder = uiSchema?.['ui:placeholder'] || '';
    const rows = uiSchema?.['ui:options']?.rows || 4;
    const disabled = uiSchema?.['ui:disabled'] || false;
    const readonly = uiSchema?.['ui:readonly'] || false;
    
    return `
      <textarea
        id="${fieldId}"
        data-path="${path}"
        placeholder="${placeholder}"
        rows="${rows}"
        ${disabled ? 'disabled' : ''}
        ${readonly ? 'readonly' : ''}
        class="field-textarea"
      >${value}</textarea>
    `;
  }

  renderSelect(fieldSchema, uiSchema, fieldId, path, enumValues) {
    const value = this.getFieldValue(path) || fieldSchema.default || '';
    const disabled = uiSchema?.['ui:disabled'] || false;
    
    let options = '';
    if (enumValues) {
      options = enumValues.map(opt => 
        `<option value="${opt}" ${opt === value ? 'selected' : ''}>${opt}</option>`
      ).join('');
    }
    
    return `
      <select
        id="${fieldId}"
        data-path="${path}"
        ${disabled ? 'disabled' : ''}
        class="field-select"
      >
        <option value="">Select...</option>
        ${options}
      </select>
    `;
  }

  renderCheckbox(fieldSchema, uiSchema, fieldId, path) {
    const value = this.getFieldValue(path) || fieldSchema.default || false;
    const disabled = uiSchema?.['ui:disabled'] || false;
    
    return `
      <input
        type="checkbox"
        id="${fieldId}"
        data-path="${path}"
        ${value ? 'checked' : ''}
        ${disabled ? 'disabled' : ''}
        class="field-checkbox"
      />
    `;
  }

  renderRadio(fieldSchema, uiSchema, fieldId, path, enumValues) {
    const value = this.getFieldValue(path) || fieldSchema.default || '';
    const disabled = uiSchema?.['ui:disabled'] || false;
    
    if (!enumValues) return '';
    
    const radios = enumValues.map((opt, idx) => `
      <label class="radio-label">
        <input
          type="radio"
          name="${fieldId}"
          data-path="${path}"
          value="${opt}"
          ${opt === value ? 'checked' : ''}
          ${disabled ? 'disabled' : ''}
          class="field-radio"
        />
        <span>${opt}</span>
      </label>
    `).join('');
    
    return `<div class="radio-group">${radios}</div>`;
  }

  getDefaultWidget(type) {
    const widgetMap = {
      'string': 'text',
      'number': 'number',
      'integer': 'number',
      'boolean': 'checkbox',
      'array': 'array',
      'object': 'object'
    };
    return widgetMap[type] || 'text';
  }

  getFieldValue(path) {
    const keys = path.split('.');
    let current = this.formData;
    for (const key of keys) {
      if (current && typeof current === 'object' && key in current) {
        current = current[key];
      } else {
        return undefined;
      }
    }
    return current;
  }

  render() {
    if (!this.schema) {
      this.shadowRoot.innerHTML = '<div>No schema provided</div>';
      return;
    }

    const { properties = {}, required = [] } = this.schema;
    const uiSchema = this.ui_schema || {};
    
    let formHtml = '<form class="json-schema-form">';
    
    // Render each field
    for (const [fieldName, fieldSchema] of Object.entries(properties)) {
      const fieldPath = fieldName;
      const fieldUISchema = uiSchema[fieldName] || {};
      const isRequired = required.includes(fieldName);
      
      formHtml += this.renderField(
        { ...fieldSchema, required: isRequired },
        fieldUISchema,
        fieldPath
      );
    }
    
    formHtml += `
      <button type="submit" class="submit-button">Submit</button>
    </form>
    `;
    
    this.shadowRoot.innerHTML = `
      <style>
        ${this.getStyles()}
      </style>
      ${formHtml}
    `;
  }

  getStyles() {
    return `
      :host {
        display: block;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      
      .json-schema-form {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 1rem;
      }
      
      .field-wrapper {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }
      
      .field-label {
        font-weight: 600;
        font-size: 0.875rem;
        color: #333;
      }
      
      .field-description {
        font-size: 0.75rem;
        color: #666;
        margin: 0;
      }
      
      .field-input,
      .field-textarea,
      .field-select {
        padding: 0.5rem;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 1rem;
      }
      
      .field-input:focus,
      .field-textarea:focus,
      .field-select:focus {
        outline: none;
        border-color: #0066cc;
        box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.1);
      }
      
      .field-checkbox,
      .field-radio {
        margin-right: 0.5rem;
      }
      
      .radio-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }
      
      .radio-label {
        display: flex;
        align-items: center;
        cursor: pointer;
      }
      
      .field-errors {
        color: #d32f2f;
        font-size: 0.75rem;
        margin-top: 0.25rem;
      }
      
      .submit-button {
        padding: 0.75rem 1.5rem;
        background-color: #0066cc;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 1rem;
        cursor: pointer;
        margin-top: 1rem;
      }
      
      .submit-button:hover {
        background-color: #0052a3;
      }
      
      .submit-button:disabled {
        background-color: #ccc;
        cursor: not-allowed;
      }
    `;
  }
}

customElements.define('json-schema-form', JsonSchemaForm);

export default JsonSchemaForm;

