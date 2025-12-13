/**
 * React Example - Using the JSON Schema Form Web Component
 * 
 * This shows how to use the web component in a React application.
 */

import React, { useRef, useEffect } from 'react';

// Import the web component (after build)
// import '@report-analyst/json-schema-form/dist/json-schema-form.es.js';

interface JsonSchemaFormElement extends HTMLElement {
  setSchema(schema: any): void;
  setUISchema(uiSchema: any): void;
  setFormData(formData: any): void;
  getFormData(): any;
  addEventListener(type: 'change' | 'submit' | 'error', listener: (e: CustomEvent) => void): void;
}

export const JsonSchemaFormReact: React.FC<{
  schema: any;
  uiSchema?: any;
  formData?: any;
  onChange?: (formData: any) => void;
  onSubmit?: (formData: any) => void;
  onError?: (errors: any) => void;
}> = ({ schema, uiSchema, formData, onChange, onSubmit, onError }) => {
  const formRef = useRef<JsonSchemaFormElement>(null);

  useEffect(() => {
    const form = formRef.current;
    if (!form) return;

    // Set schema and UI schema
    form.setSchema(schema);
    if (uiSchema) {
      form.setUISchema(uiSchema);
    }
    if (formData) {
      form.setFormData(formData);
    }

    // Set up event listeners
    const handleChange = (e: CustomEvent) => {
      if (onChange) {
        onChange(e.detail.formData);
      }
    };

    const handleSubmit = (e: CustomEvent) => {
      if (onSubmit) {
        onSubmit(e.detail.formData);
      }
    };

    const handleError = (e: CustomEvent) => {
      if (onError) {
        onError(e.detail.errors);
      }
    };

    form.addEventListener('change', handleChange);
    form.addEventListener('submit', handleSubmit);
    form.addEventListener('error', handleError);

    return () => {
      form.removeEventListener('change', handleChange);
      form.removeEventListener('submit', handleSubmit);
      form.removeEventListener('error', handleError);
    };
  }, [schema, uiSchema, formData, onChange, onSubmit, onError]);

  return <json-schema-form ref={formRef} />;
};

// Example usage:
export const ExampleApp: React.FC = () => {
  const [formData, setFormData] = React.useState<any>({});

  const schema = {
    type: 'object',
    properties: {
      name: { type: 'string', title: 'Name' },
      email: { type: 'string', format: 'email', title: 'Email' }
    }
  };

  return (
    <div>
      <h1>React Example</h1>
      <JsonSchemaFormReact
        schema={schema}
        onChange={(data) => setFormData(data)}
        onSubmit={(data) => {
          console.log('Submitted:', data);
          alert('Form submitted!');
        }}
      />
      <pre>{JSON.stringify(formData, null, 2)}</pre>
    </div>
  );
};

