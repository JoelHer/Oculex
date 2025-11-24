<script setup>
import { ref, onMounted, watch, computed, onBeforeUnmount } from 'vue'
import { EoesStream } from '../../models/EoesStream.js'

const props = defineProps({
  stream: {
    type: EoesStream,
    required: true
  }
})

const logs = ref([])
const loading = ref(true)
const error = ref(null)
const filterLevel = ref('all') 
const searchQuery = ref('')
const autoRefresh = ref(false)
const refreshInterval = ref(null)


async function loadLogs() {
  if (!autoRefresh.value) {
    loading.value = true
  }
  error.value = null
  
  try {
    const res = await fetch(`/streams/${encodeURIComponent(props.stream.name)}/get-logs`)
    if (!res.ok) {
      throw new Error(`Failed to fetch logs: ${res.status}`)
    }
    
    const data = await res.json()
    logs.value = data.logs || []
  } catch (e) {
    console.error('Failed loading logs', e)
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const filteredLogs = computed(() => {
  let filtered = logs.value

  if (filterLevel.value !== 'all') {
    filtered = filtered.filter(log => log.level === filterLevel.value)
  }

  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(log => 
      log.message.toLowerCase().includes(query) ||
      log.level.toLowerCase().includes(query)
    )
  }

  return filtered
})

function getLevelColor(level) {
  const colors = {
    'DEBUG': '#888',
    'INFO': '#40F284',
    'WARN': '#FFA500',
    'ERROR': '#FF4444'
  }
  return colors[level] || '#fff'
}


function formatTimestamp(log) {
  if (log.iso) {
    return new Date(log.iso).toLocaleString()
  }
  
  if (log.timestamp) {
    const ts = parseInt(log.timestamp)
    if (!isNaN(ts) && ts > 1000000000) {
      return new Date(ts * 1000).toLocaleString()
    }
    return new Date(log.timestamp).toLocaleString()
  }
  
  return '—'
}

// Toggle auto-refresh
function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  
  if (autoRefresh.value) {
    refreshInterval.value = setInterval(() => {
      loadLogs()
    }, 5000)
  } else {
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value)
      refreshInterval.value = null
    }
  }
}

async function clearLogs() {
  if (!confirm('Are you sure you want to clear all logs for this stream?')) {
    return
  }
  
  try {
    const res = await fetch(`/streams/${encodeURIComponent(props.stream.name)}/clear-logs`, {
      method: 'POST'
    })
    
    if (!res.ok) {
      throw new Error('Failed to clear logs')
    }
    
    logs.value = []
  } catch (e) {
    console.error('Failed clearing logs', e)
    alert('Error clearing logs: ' + e.message)
  }
}

onMounted(() => {
  loadLogs()
})


onBeforeUnmount(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
})

watch(() => props.stream.name, () => {
  loadLogs()
})
</script>

<template>
  <div class="logs-root">
    <h2 class="section-title">Logs</h2>

    <div class="logs-layout">
      <div class="main-col">
        <div class="stream-box controls-box">
          <div class="controls-row">
            <div class="control-group">
              <label>Level</label>
              <select v-model="filterLevel">
                <option value="all">All levels</option>
                <option value="DEBUG">DEBUG</option>
                <option value="INFO">INFO</option>
                <option value="WARN">WARN</option>
                <option value="ERROR">ERROR</option>
              </select>
            </div>

            <div class="control-group flex-grow">
              <label>Search</label>
              <input 
                type="text" 
                v-model="searchQuery" 
                placeholder="Search logs..."
              />
            </div>

            <div class="button-group">
              <button 
                class="control-button"
                @click="loadLogs"
                :disabled="loading"
              >
                Refresh
              </button>
              
              <button 
                class="control-button"
                :class="{ active: autoRefresh }"
                @click="toggleAutoRefresh"
              >
                {{ autoRefresh ? 'Auto ✓' : 'Auto' }}
              </button>
              
              <button 
                class="control-button danger"
                @click="clearLogs"
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        <!-- Logs Display -->
        <div class="stream-box logs-box">
          <div v-if="loading && logs.length === 0" class="loading-state">
            <div class="spinner-large"></div>
            <div>Loading logs...</div>
          </div>

          <div v-else-if="error" class="error-state">
            <div class="error-icon">⚠️</div>
            <div>{{ error }}</div>
            <button @click="loadLogs" class="retry-button">Retry</button>
          </div>

          <div v-else-if="filteredLogs.length === 0" class="empty-state">
            <div class="empty-icon">📋</div>
            <div>{{ logs.length === 0 ? 'No logs available' : 'No logs match your filters' }}</div>
          </div>

          <div v-else class="logs-list">
            <div 
              v-for="log in filteredLogs" 
              :key="log.id"
              class="log-entry"
            >
              <div class="log-header">
                <span 
                  class="log-level"
                  :style="{ color: getLevelColor(log.level) }"
                >
                  {{ log.level }}
                </span>
                <span class="log-timestamp">{{ formatTimestamp(log) }}</span>
              </div>
              <div class="log-message">{{ log.message }}</div>
            </div>
          </div>
        </div>

        <!-- Stats -->
        <div class="stats-row">
          <span class="stat">
            Total: <strong>{{ logs.length }}</strong>
          </span>
          <span class="stat">
            Filtered: <strong>{{ filteredLogs.length }}</strong>
          </span>
          <span v-if="autoRefresh" class="stat refresh-indicator">
            🔄 Auto-refreshing
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.logs-root { 
  display: flex; 
  flex-direction: column; 
  gap: 16px; 
  color: white; 
}

.section-title { 
  font-size: 1.5rem; 
  font-weight: 600; 
}

.logs-layout { 
  display: flex; 
  flex-direction: column; 
  gap: 16px; 
}

.main-col { 
  display: flex; 
  flex-direction: column; 
  gap: 12px; 
}

.stream-box {
  background: #23252c;
  padding: 14px;
  border-radius: 15px;
  border: 2px solid #2d2f37;
}

/* Controls */
.controls-box {
  padding: 12px 14px;
}

.controls-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 120px;
}

.control-group.flex-grow {
  flex: 1;
  min-width: 200px;
}

.control-group label {
  color: #aaa;
  font-size: 0.9rem;
}

.button-group {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

input[type="text"], select {
  background: #1e1f25;
  color: white;
  border: 1px solid #2d2f37;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 0.98rem;
}

.control-button {
  background: #2d2f37;
  color: white;
  border: 1px solid #3d3f47;
  padding: 8px 14px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.control-button:hover {
  background: #3d3f47;
}

.control-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-button.active {
  background: #40F284;
  color: black;
  border-color: #40F284;
}

.control-button.danger {
  background: #4d2020;
  border-color: #6d3030;
}

.control-button.danger:hover {
  background: #6d3030;
}

/* Logs Box */
.logs-box {
  min-height: 400px;
  max-height: 600px;
  overflow-y: auto;
  padding: 0;
}

.logs-list {
  display: flex;
  flex-direction: column;
}

.log-entry {
  padding: 12px 14px;
  border-bottom: 1px solid #2d2f37;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  gap: 12px;
}

.log-level {
  font-weight: 700;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.log-timestamp {
  color: #888;
  font-size: 0.85rem;
  white-space: nowrap;
}

.log-message {
  color: #ddd;
  font-size: 0.95rem;
  line-height: 1.4;
  font-family: 'Monaco', 'Consolas', monospace;
  word-break: break-word;
}

/* States */
.loading-state, .error-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
  color: #888;
}

.spinner-large {
  width: 40px;
  height: 40px;
  border: 4px solid #2d2f37;
  border-top: 4px solid #40F284;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon, .empty-icon {
  font-size: 3rem;
}

.retry-button {
  background: #40F284;
  color: black;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
}

/* Stats */
.stats-row {
  display: flex;
  gap: 20px;
  color: #aaa;
  font-size: 0.9rem;
  padding: 0 4px;
}

.stat strong {
  color: #40F284;
}

.refresh-indicator {
  color: #40F284;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>