<template>
  <div class="seed-container">
    <div class="seed-panel">
      <h2>📤 Seed Reference Data</h2>
      <p class="subtitle">Upload CSV or DBF files to populate reference data</p>

      <!-- Step 1: Upload -->
      <div v-if="step === 1" class="step">
        <h3>Step 1: Upload File</h3>
        
        <div class="upload-area" 
             @dragover="dragover = true" 
             @dragleave="dragover = false"
             @drop="handleDrop"
             :class="{ dragging: dragover }">
          <input 
            type="file" 
            ref="fileInput" 
            @change="handleFileSelect"
            accept=".csv,.dbf"
            style="display: none"
          />
          <div @click="$refs.fileInput.click()" class="upload-trigger">
            <span class="upload-icon">📁</span>
            <p>Click to select or drag & drop CSV/DBF file</p>
            <small>Supported: CSV, DBF</small>
          </div>
        </div>

        <div v-if="selectedFile" class="file-info">
          <span>✓ {{ selectedFile.name }} ({{ formatFileSize(selectedFile.size) }})</span>
        </div>

        <button 
          @click="uploadFile" 
          :disabled="!selectedFile || loading"
          class="btn btn-primary"
        >
          {{ loading ? 'Uploading...' : 'Upload & Analyze' }}
        </button>

        <div v-if="error" class="alert alert-error">{{ error }}</div>
      </div>

      <!-- Step 2: Preview -->
      <div v-if="step === 2" class="step">
        <h3>Step 2: Preview Data</h3>
        
        <div class="preview-info">
          <p><strong>Type:</strong> {{ seedType }}</p>
          <p><strong>Records:</strong> {{ recordCount }}</p>
          <p><strong>Columns:</strong> {{ columns.join(', ') }}</p>
        </div>

        <div class="preview-table">
          <table>
            <thead>
              <tr>
                <th v-for="col in columns" :key="col">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in previewRows" :key="idx">
                <td v-for="col in columns" :key="col">
                  {{ formatCellValue(row[col]) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="button-group">
          <button @click="step = 1" class="btn btn-secondary">← Back</button>
          <button @click="importData" class="btn btn-primary">
            {{ loading ? 'Importing...' : 'Confirm & Import' }}
          </button>
        </div>

        <div v-if="error" class="alert alert-error">{{ error }}</div>
      </div>

      <!-- Step 3: Results -->
      <div v-if="step === 3" class="step">
        <h3>✓ Import Complete</h3>
        
        <div class="results">
          <div class="result-item success">
            <span class="icon">✓</span>
            <div>
              <p class="label">Created</p>
              <p class="value">{{ importResults.created }}</p>
            </div>
          </div>
          <div class="result-item info">
            <span class="icon">~</span>
            <div>
              <p class="label">Updated</p>
              <p class="value">{{ importResults.updated }}</p>
            </div>
          </div>
          <div v-if="importResults.errors.length > 0" class="result-item error">
            <span class="icon">⚠</span>
            <div>
              <p class="label">Errors</p>
              <p class="value">{{ importResults.errors.length }}</p>
            </div>
          </div>
        </div>

        <div v-if="importResults.errors.length > 0" class="errors-list">
          <h4>Error Details:</h4>
          <ul>
            <li v-for="(err, idx) in importResults.errors" :key="idx">
              {{ err }}
            </li>
          </ul>
        </div>

        <div class="button-group">
          <button @click="resetForm" class="btn btn-primary">
            ⟲ Seed More Data
          </button>
        </div>
      </div>
    </div>

    <!-- Templates Section -->
    <div class="templates-panel">
      <h3>📋 Download Templates</h3>
      <p>Download CSV templates and fill them with your data:</p>
      
      <button 
        v-for="template in templates" 
        :key="template.name"
        @click="downloadTemplate(template)"
        class="template-btn"
        :title="template.description"
      >
        📥 {{ template.name }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const step = ref(1)
const selectedFile = ref(null)
const loading = ref(false)
const error = ref('')
const dragover = ref(false)

// Data from API
const seedType = ref('')
const recordCount = ref(0)
const columns = ref([])
const previewRows = ref([])
const importResults = ref({ created: 0, updated: 0, errors: [] })

// Templates
const templates = [
  { name: 'sales_departments.csv', description: 'Sales Departments template' },
  { name: 'sales_areas.csv', description: 'Sales Areas/Salesmen template' },
  { name: 'tax_codes.csv', description: 'Tax Codes template' },
  { name: 'payment_methods.csv', description: 'Payment Methods template' },
  { name: 'credit_terms.csv', description: 'Credit Terms template' },
  { name: 'income_categories.csv', description: 'Income Categories template' },
  { name: 'expense_categories.csv', description: 'Expense Categories template' }
]

const templateData = {
  'sales_departments.csv': 'number,name\n1,Electronics\n2,Furniture\n3,Clothing',
  'sales_areas.csv': 'number,name,commission_rate\n1,Metropolitan,2.5\n2,Suburban,2.0',
  'tax_codes.csv': 'code,description,rate\n1,Standard 14%,14.00\n2,Zero Rated,0.00',
  'payment_methods.csv': 'code,name,requires_reference,is_electronic\nCASH,Cash,No,No\nCHQ,Cheque,Yes,No',
  'credit_terms.csv': 'days,description\n0,Cash On Delivery\n30,30 Days\n60,60 Days',
  'income_categories.csv': 'number,name\n1,Sales Income\n2,Service Income\n3,Interest Income',
  'expense_categories.csv': 'number,name,category_type\n1,Rent,BOTH\n2,Utilities,BOTH'
}

const handleFileSelect = (event) => {
  selectedFile.value = event.target.files[0]
  error.value = ''
}

const handleDrop = (event) => {
  event.preventDefault()
  dragover.value = false
  selectedFile.value = event.dataTransfer.files[0]
}

const uploadFile = async () => {
  if (!selectedFile.value) return

  loading.value = true
  error.value = ''

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const response = await fetch('/api/settings/seed/upload_and_analyze/', {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      }
    })

    const result = await response.json()

    if (result.success) {
      seedType.value = result.seed_type
      recordCount.value = result.record_count
      columns.value = result.columns
      previewRows.value = result.preview_rows
      step.value = 2
    } else {
      error.value = result.error || 'Unknown error'
    }
  } catch (err) {
    error.value = 'Upload failed: ' + err.message
  } finally {
    loading.value = false
  }
}

const importData = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch('/api/settings/seed/import_data/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      }
    })

    const result = await response.json()

    if (result.success) {
      importResults.value = result
      step.value = 3
    } else {
      error.value = result.error || 'Import failed'
    }
  } catch (err) {
    error.value = 'Import failed: ' + err.message
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  step.value = 1
  selectedFile.value = null
  seedType.value = ''
  previewRows.value = []
  error.value = ''
}

const downloadTemplate = (template) => {
  const content = templateData[template.name]
  const blob = new Blob([content], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = template.name
  a.click()
}

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatCellValue = (value) => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return String(value).substring(0, 50)
}

const getCookie = (name) => {
  let cookieValue = null
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}
</script>

<style scoped>
.seed-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.seed-panel, .templates-panel {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

h2 { color: #333; margin-bottom: 0.5rem; }
h3 { color: #555; margin-bottom: 1rem; margin-top: 1.5rem; }
.subtitle { color: #999; font-size: 0.95rem; margin-bottom: 2rem; }

.step { margin-bottom: 2rem; }

.upload-area {
  border: 3px dashed #ddd;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 1.5rem;
  background: #fafafa;
}

.upload-area:hover { border-color: #007bff; background: #f0f7ff; }
.upload-area.dragging { border-color: #28a745; background: #f0fff4; }

.upload-icon { font-size: 2.5rem; display: block; margin-bottom: 0.5rem; }
.upload-area p { margin: 0.5rem 0; }
.upload-area small { display: block; color: #999; }

.file-info {
  background: #f0fff4;
  border-left: 4px solid #28a745;
  padding: 0.75rem;
  margin-bottom: 1rem;
  border-radius: 4px;
  font-size: 0.9rem;
}

.preview-info {
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
}

.preview-info p { margin: 0.5rem 0; }
.preview-info strong { color: #555; }

.preview-table {
  overflow-x: auto;
  margin-bottom: 1.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.preview-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.preview-table th {
  background: #f5f5f5;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #ddd;
}

.preview-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #eee;
}

.preview-table tr:hover { background: #fafafa; }

.button-group {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
}

.btn-primary {
  background: #007bff;
  color: white;
  flex: 1;
}

.btn-primary:hover:not(:disabled) { background: #0056b3; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover { background: #545b62; }

.alert {
  padding: 0.75rem;
  border-radius: 4px;
  margin-top: 1rem;
  font-size: 0.9rem;
}

.alert-error {
  background: #ffe5e5;
  border-left: 4px solid #dc3545;
  color: #721c24;
}

.results {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 4px;
  background: #f5f5f5;
}

.result-item.success { background: #f0fff4; border-left: 4px solid #28a745; }
.result-item.info { background: #e7f3ff; border-left: 4px solid #0066cc; }
.result-item.error { background: #ffe5e5; border-left: 4px solid #dc3545; }

.result-item .icon {
  font-size: 1.5rem;
  font-weight: bold;
}

.result-item .label {
  font-size: 0.85rem;
  color: #666;
  margin: 0;
}

.result-item .value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
  margin: 0;
}

.errors-list {
  background: #ffe5e5;
  border: 1px solid #ffcccc;
  border-radius: 4px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.errors-list h4 { margin-top: 0; color: #721c24; }
.errors-list li { color: #721c24; margin: 0.5rem 0; }

.templates-panel {
  position: sticky;
  top: 2rem;
  height: fit-content;
}

.templates-panel p { color: #666; font-size: 0.9rem; margin-bottom: 1rem; }

.template-btn {
  display: block;
  width: 100%;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  text-align: left;
  transition: all 0.3s;
}

.template-btn:hover {
  background: #e7f3ff;
  border-color: #0066cc;
  color: #0066cc;
}

@media (max-width: 768px) {
  .seed-container { grid-template-columns: 1fr; }
  .templates-panel { position: static; }
  .button-group { flex-direction: column; }
  .results { grid-template-columns: 1fr; }
}
</style>
