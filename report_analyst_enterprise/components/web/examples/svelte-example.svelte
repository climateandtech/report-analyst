<!--
  Svelte Example - Using the JSON Schema Form Web Component
  
  This shows how to use the web component in a Svelte application.
  Svelte can use web components directly without any wrapper!
-->

<script>
  import { onMount } from 'svelte';
  
  let formElement;
  let formData = {};
  let output = 'No form data yet...';
  
  const schema = {
    type: 'object',
    title: 'Company Information',
    properties: {
      companyName: {
        type: 'string',
        title: 'Company Name'
      },
      email: {
        type: 'string',
        format: 'email',
        title: 'Email'
      },
      category: {
        type: 'string',
        title: 'Category',
        enum: ['Sustainability', 'Financial', 'Governance']
      }
    }
  };
  
  const uiSchema = {
    companyName: {
      'ui:placeholder': 'Enter company name'
    },
    category: {
      'ui:widget': 'select'
    }
  };
  
  onMount(() => {
    if (!formElement) return;
    
    // Set schema and UI schema
    formElement.setAttribute('schema', JSON.stringify(schema));
    formElement.setAttribute('ui-schema', JSON.stringify(uiSchema));
    
    // Listen for events
    formElement.addEventListener('change', (e) => {
      formData = e.detail.formData;
      output = JSON.stringify(formData, null, 2);
    });
    
    formElement.addEventListener('submit', (e) => {
      formData = e.detail.formData;
      output = `Submitted: ${JSON.stringify(formData, null, 2)}`;
      alert('Form submitted!');
    });
  });
</script>

<div class="container">
  <h1>JSON Schema Form - Svelte Example</h1>
  <p>This demonstrates the web component working in Svelte. No wrapper needed!</p>
  
  <json-schema-form bind:this={formElement}></json-schema-form>
  
  <div class="output">
    <h2>Output</h2>
    <pre>{output}</pre>
  </div>
</div>

<style>
  .container {
    max-width: 800px;
    margin: 2rem auto;
    padding: 2rem;
    background: white;
    border-radius: 8px;
  }
  
  .output {
    margin-top: 2rem;
    padding: 1rem;
    background: #f9f9f9;
    border-radius: 4px;
  }
  
  pre {
    background: #fff;
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
    border: 1px solid #ddd;
  }
  
  h1 {
    color: #4313C8;
  }
</style>

