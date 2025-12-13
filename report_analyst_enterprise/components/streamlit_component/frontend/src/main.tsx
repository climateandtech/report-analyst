import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { Streamlit } from 'streamlit-component-lib';
import JsonSchemaForm from './index';

// Call setComponentReady IMMEDIATELY - before React renders
// This ensures Streamlit registers the component before any messages are sent
Streamlit.setComponentReady();

// Streamlit component entry point
function App() {
  const [args, setArgs] = useState<any>({});
  
  // Listen for render events from Streamlit
  useEffect(() => {
    const handleRender = (event: any) => {
      // Extract args from the render event
      const renderData = event.detail || event;
      if (renderData && renderData.args) {
        setArgs(renderData.args);
      }
    };
    
    // Listen to Streamlit's event target
    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, handleRender);
    
    // Also listen on window as fallback
    window.addEventListener(Streamlit.RENDER_EVENT, handleRender);
    
    return () => {
      Streamlit.events.removeEventListener(Streamlit.RENDER_EVENT, handleRender);
      window.removeEventListener(Streamlit.RENDER_EVENT, handleRender);
    };
  }, []);
  
  // If no args yet, show loading
  if (!args || Object.keys(args).length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Loading form...</p>
      </div>
    );
  }
  
  return (
    <JsonSchemaForm
      schema={args.schema || '{}'}
      uiSchema={args.uiSchema || '{}'}
      formData={args.formData || '{}'}
    />
  );
}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

