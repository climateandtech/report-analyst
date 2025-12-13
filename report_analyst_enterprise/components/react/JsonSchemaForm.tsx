/**
 * React wrapper component for json-schema-form web component
 */

import React, { useEffect, useRef, useState } from 'react';

export interface JsonSchemaFormProps {
  schema: Record<string, any>;
  uiSchema?: Record<string, any>;
  formData?: Record<string, any>;
  onChange?: (data: { formData: any; errors: any[] }) => void;
  onSubmit?: (data: { formData: any }) => void;
  onError?: (errors: any[]) => void;
  className?: string;
}

export const JsonSchemaForm: React.FC<JsonSchemaFormProps> = ({
  schema,
  uiSchema,
  formData,
  onChange,
  onSubmit,
  onError,
  className,
}) => {
  const formRef = useRef<HTMLElement>(null);
  const [internalFormData, setInternalFormData] = useState(formData || {});

  useEffect(() => {
    const form = formRef.current;
    if (!form) return;

    // Set attributes
    form.setAttribute('schema', JSON.stringify(schema));
    if (uiSchema) {
      form.setAttribute('ui-schema', JSON.stringify(uiSchema));
    }
    if (formData) {
      form.setAttribute('form-data', JSON.stringify(formData));
      setInternalFormData(formData);
    }

    // Event listeners
    const handleChange = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { formData: newFormData, errors } = customEvent.detail;
      setInternalFormData(newFormData);
      if (onChange) {
        onChange({ formData: newFormData, errors });
      }
    };

    const handleSubmit = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { formData: submittedData } = customEvent.detail;
      if (onSubmit) {
        onSubmit({ formData: submittedData });
      }
    };

    const handleError = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { errors } = customEvent.detail;
      if (onError) {
        onError(errors);
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

  // Update form data when prop changes
  useEffect(() => {
    const form = formRef.current;
    if (!form || !formData) return;
    form.setAttribute('form-data', JSON.stringify(formData));
    setInternalFormData(formData);
  }, [formData]);

  return (
    <json-schema-form
      ref={formRef}
      className={className}
      schema={JSON.stringify(schema)}
      ui-schema={uiSchema ? JSON.stringify(uiSchema) : undefined}
      form-data={JSON.stringify(internalFormData)}
    />
  );
};

export default JsonSchemaForm;


