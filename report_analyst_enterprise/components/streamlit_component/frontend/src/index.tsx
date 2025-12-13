/**
 * Streamlit custom component for JSON Schema form
 * 
 * Uses the framework-agnostic web component.
 */

import React, { useEffect, useRef } from "react";
import { Streamlit } from "streamlit-component-lib";

interface JsonSchemaFormProps {
  schema: string;
  uiSchema: string;
  formData: string;
}

// Extend HTMLElement to include web component methods
interface JsonSchemaFormElement extends HTMLElement {
  setSchema(schema: any): void;
  setUISchema(uiSchema: any): void;
  setFormData(formData: any): void;
  getFormData(): any;
  addEventListener(type: 'change' | 'submit' | 'error', listener: (e: CustomEvent) => void): void;
  removeEventListener(type: 'change' | 'submit' | 'error', listener: (e: CustomEvent) => void): void;
}

const JsonSchemaForm: React.FC<JsonSchemaFormProps> = (props) => {
  const formRef = useRef<JsonSchemaFormElement | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const heightUpdateTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastHeightRef = useRef<number>(0);
  const observerRef = useRef<MutationObserver | null>(null);

  // Parse props
  const schema = JSON.parse(props.schema || "{}");
  const uiSchema = JSON.parse(props.uiSchema || "{}");
  const initialFormData = JSON.parse(props.formData || "{}");

  // Debounced height update function
  const updateFrameHeight = React.useCallback(() => {
    // Clear any pending updates
    if (heightUpdateTimeoutRef.current) {
      clearTimeout(heightUpdateTimeoutRef.current);
    }

    heightUpdateTimeoutRef.current = setTimeout(() => {
      try {
        const formElement = formRef.current;
        if (!formElement) return;

        // Get the actual height of the form element
        const height = Math.max(
          formElement.offsetHeight || formElement.scrollHeight || 600,
          600 // minimum height
        );

        // Only update if height changed significantly (more than 50px difference)
        // This prevents flickering from minor layout shifts
        if (Math.abs(height - lastHeightRef.current) > 50 || lastHeightRef.current === 0) {
          lastHeightRef.current = height;
          Streamlit.setFrameHeight(height + 100); // Add padding
        }
      } catch (e) {
        console.debug('Could not set frame height yet:', e);
      }
    }, 150); // Debounce by 150ms
  }, []);

  useEffect(() => {
    // Load web component script if not already loaded
    const loadWebComponent = async () => {
      // Check if web component is already defined
      if (customElements.get('json-schema-form')) {
        createFormElement();
        return;
      }

      // Load the web component script
      // Use relative path since Streamlit serves components from a subdirectory
      const script = document.createElement('script');
      script.type = 'module';
      // Always use relative path - Streamlit serves from component subdirectory
      script.src = './json-schema-form.es.js';
      
      // Wait for custom element to be defined
      const waitForCustomElement = (maxAttempts = 50) => {
        let attempts = 0;
        const check = () => {
          if (customElements.get('json-schema-form')) {
            createFormElement();
          } else if (attempts < maxAttempts) {
            attempts++;
            setTimeout(check, 100);
          } else {
            console.error('Custom element json-schema-form not defined after loading script');
          }
        };
        setTimeout(check, 100);
      };
      
      script.onload = () => {
        waitForCustomElement();
      };
      script.onerror = (e) => {
        console.error('Failed to load web component from', script.src, e);
        // Try absolute path as fallback (for dev server)
        const fallbackScript = document.createElement('script');
        fallbackScript.type = 'module';
        fallbackScript.src = '/json-schema-form.es.js';
        fallbackScript.onload = () => {
          waitForCustomElement();
        };
        fallbackScript.onerror = (e2) => {
          console.error('Failed to load web component from fallback path:', e2);
        };
        document.head.appendChild(fallbackScript);
      };
      document.head.appendChild(script);
    };

    const createFormElement = () => {
      if (!containerRef.current) return;

      // Remove existing form if any
      const existing = containerRef.current.querySelector('json-schema-form');
      if (existing) {
        existing.remove();
      }

      // Disconnect previous observer
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
      }

      // Create web component element
      const formElement = document.createElement('json-schema-form') as JsonSchemaFormElement;
      formRef.current = formElement;

      // Set schema and UI schema
      formElement.setSchema(schema);
      formElement.setUISchema(uiSchema);
      formElement.setFormData(initialFormData);

      // Set up event listeners
      const handleChange = (e: CustomEvent) => {
        // Don't send to Streamlit on every change - only on submit
        // Height will be updated by observer
      };

      const handleSubmit = (e: CustomEvent) => {
        // Send submitted data to Streamlit
        Streamlit.setComponentValue({
          type: "submit",
          formData: e.detail.formData,
        });
        // Update height after submit
        updateFrameHeight();
      };

      const handleError = (e: CustomEvent) => {
        // Send errors to Streamlit
        Streamlit.setComponentValue({
          type: "error",
          errors: e.detail.errors,
        });
        // Update height after error
        updateFrameHeight();
      };

      formElement.addEventListener('change', handleChange);
      formElement.addEventListener('submit', handleSubmit);
      formElement.addEventListener('error', handleError);

      // Append to container
      containerRef.current.appendChild(formElement);

      // Set up mutation observer for dynamic height updates
      // Only observe the container, not the shadow DOM
      observerRef.current = new MutationObserver(() => {
        updateFrameHeight();
      });

      // Observe the container, not the shadow DOM (which we can't observe)
      if (containerRef.current) {
        observerRef.current.observe(containerRef.current, {
          childList: true,
          subtree: false, // Don't observe subtree to avoid shadow DOM issues
          attributes: false // Don't observe attributes to reduce triggers
        });
      }

      // Initial height update after a delay to let the form render
      setTimeout(updateFrameHeight, 300);
    };

    loadWebComponent();

    // Update form data when props change (but only if form already exists)
    if (formRef.current) {
      formRef.current.setSchema(schema);
      formRef.current.setUISchema(uiSchema);
      formRef.current.setFormData(initialFormData);
      // Update height after props change
      updateFrameHeight();
    }

    return () => {
      // Cleanup
      if (heightUpdateTimeoutRef.current) {
        clearTimeout(heightUpdateTimeoutRef.current);
      }
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
      }
      if (formRef.current) {
        formRef.current.remove();
        formRef.current = null;
      }
    };
  }, [schema, uiSchema, initialFormData, updateFrameHeight]);

  return (
    <div 
      ref={containerRef}
      style={{ 
        width: "100%", 
        minHeight: "400px",
      }}
    />
  );
};

export default JsonSchemaForm;
