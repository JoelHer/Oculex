<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { EoesStream } from '../../models/EoesStream.js'
import { getNextCronExecution } from '../../utils.js'

const props = defineProps({
  stream: {
    type: EoesStream,
    required: true
  }
})
const emit = defineEmits(['save'])

// --- reactive form fields ---
const executionMode = ref('on_api_call') // 'on_api_call' | 'interval' | 'manual'
const intervalPreset = ref('5') // '1','5','15','60','custom'
const intervalMinutes = ref(5) // used when preset or custom numeric
const cronExpression = ref('') // optional custom cron
const cacheEnabled = ref(true)
const cacheDuration = ref(60) // numeric
const cacheDurationUnit = ref('minutes') // 'minutes'|'hours'|'days'
const maxCachedEntries = ref(null) // optional

const deltaTracking = ref(false)
const deltaAmount = ref(0)
const deltaTimespan = ref(60)
const deltaTimespanUnit = ref('minutes') // 'minutes'|'hours'
const resetOnPeriod = ref('none') // 'none' | 'daily' | 'weekly'

const allowDecreasingValues = ref(false) // new field to allow decreasing values

// advanced
const preHook = ref('')
const postHook = ref('')
const loggingLevel = ref('info') // 'debug'|'info'|'warn'|'error'
const notifyOnJump = ref(false)

// UI state
const saving = ref(false)
const loading = ref(true)

// helper: "now" for next-run display (updates every 30s)
const now = ref(new Date())
setInterval(() => now.value = new Date(), 30 * 1000)

// Watch for preset changes and update cron expression
watch(intervalPreset, (newPreset) => {
  if (executionMode.value === 'interval' && newPreset !== 'custom') {
    const cronMap = {
      '1': '* * * * *',        // every minute
      '5': '*/5 * * * *',      // every 5 minutes  
      '15': '*/15 * * * *',    // every 15 minutes
      '60': '0 * * * *'        // every hour
    }
    cronExpression.value = cronMap[newPreset] || ''
  }
})

// --- initial state for dirty-check ---
const initialState = reactive({
  executionMode: executionMode.value,
  intervalPreset: intervalPreset.value,
  intervalMinutes: intervalMinutes.value,
  cronExpression: cronExpression.value,
  cacheEnabled: cacheEnabled.value,
  cacheDuration: cacheDuration.value,
  cacheDurationUnit: cacheDurationUnit.value,
  deltaTracking: deltaTracking.value,
  deltaAmount: deltaAmount.value,
  deltaTimespan: deltaTimespan.value,
  deltaTimespanUnit: deltaTimespanUnit.value,
  allowDecreasingValues: allowDecreasingValues.value,
})

const isDirty = computed(() => {
  return executionMode.value !== initialState.executionMode ||
    intervalPreset.value !== initialState.intervalPreset ||
    intervalMinutes.value !== initialState.intervalMinutes ||
    cronExpression.value !== initialState.cronExpression ||
    cacheEnabled.value !== initialState.cacheEnabled ||
    cacheDuration.value !== initialState.cacheDuration ||
    cacheDurationUnit.value !== initialState.cacheDurationUnit ||
    deltaTracking.value !== initialState.deltaTracking ||
    deltaAmount.value !== initialState.deltaAmount ||
    deltaTimespan.value !== initialState.deltaTimespan ||
    deltaTimespanUnit.value !== initialState.deltaTimespanUnit ||
    allowDecreasingValues.value !== initialState.allowDecreasingValues
})

const nextRun = computed(() => {
  try {
    return getNextCronExecution(cronExpression.value)
  } catch (error) {
    console.error('Failed to compute next run time', error)
  }
  return "invalid cron expression"
})

// load existing scheduling config
async function loadSettings() {
  loading.value = true
  try {
    const res = await fetch(`/streams/${encodeURIComponent(props.stream.name)}/scheduling-settings`)
    if (!res.ok) {
      // no settings yet — leave defaults
      loading.value = false
      return
    }
    const cfg = await res.json()
    // map server fields to local form fields (defensive)
    executionMode.value = cfg.execution_mode || executionMode.value
    if (cfg.interval_minutes) {
      intervalMinutes.value = cfg.interval_minutes
      intervalPreset.value = ['1','5','15','60'].includes(String(cfg.interval_minutes)) ? String(cfg.interval_minutes) : 'custom'
    }
    cronExpression.value = cfg.cron_expression || ''
    cacheEnabled.value = cfg.cache_enabled ?? cacheEnabled.value
    cacheDuration.value = cfg.cache_duration ?? cacheDuration.value
    cacheDurationUnit.value = cfg.cache_duration_unit || cacheDurationUnit.value

    deltaTracking.value = cfg.delta_tracking ?? deltaTracking.value
    deltaAmount.value = cfg.delta_amount ?? deltaAmount.value
    deltaTimespan.value = cfg.delta_timespan ?? deltaTimespan.value
    deltaTimespanUnit.value = cfg.delta_timespan_unit || deltaTimespanUnit.value
    allowDecreasingValues.value = cfg.allow_decreasing_values ?? allowDecreasingValues.value

    // set initialState snapshot
    Object.assign(initialState, {
      executionMode: executionMode.value,
      intervalPreset: intervalPreset.value,
      intervalMinutes: intervalMinutes.value,
      cronExpression: cronExpression.value,
      cacheEnabled: cacheEnabled.value,
      cacheDuration: cacheDuration.value,
      cacheDurationUnit: cacheDurationUnit.value,
      deltaTracking: deltaTracking.value,
      deltaAmount: deltaAmount.value,
      deltaTimespan: deltaTimespan.value,
      deltaTimespanUnit: deltaTimespanUnit.value,
      allowDecreasingValues: allowDecreasingValues.value,
    })
  } catch (e) {
    console.error('Failed loading scheduling settings', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSettings()
})

// save
async function saveChanges() {
  if (!isDirty.value || saving.value) return
  saving.value = true
  try {
    const payload = {
      execution_mode: executionMode.value,
      // prefer explicit numeric intervalMinutes
      interval_minutes: (intervalPreset.value === 'custom') ? "custom" : parseInt(intervalPreset.value),
      cron_expression: cronExpression.value,
      cache_enabled: cacheEnabled.value,
      cache_duration: parseInt(cacheDuration.value),
      cache_duration_unit: cacheDurationUnit.value,
      delta_tracking: deltaTracking.value,
      delta_amount: parseFloat(deltaAmount.value),
      delta_timespan: parseInt(deltaTimespan.value),
      delta_timespan_unit: deltaTimespanUnit.value,
      allow_decreasing_values: allowDecreasingValues.value,
    }

    const res = await fetch(`/streams/${encodeURIComponent(props.stream.name)}/scheduling-settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!res.ok) throw new Error('Failed saving scheduling')

    // update initial snapshot
    Object.assign(initialState, {
      executionMode: executionMode.value,
      intervalPreset: intervalPreset.value,
      intervalMinutes: intervalMinutes.value,
      cronExpression: cronExpression.value,
      cacheEnabled: cacheEnabled.value,
      cacheDuration: cacheDuration.value,
      cacheDurationUnit: cacheDurationUnit.value,
      deltaTracking: deltaTracking.value,
      deltaAmount: deltaAmount.value,
      deltaTimespan: deltaTimespan.value,
      deltaTimespanUnit: deltaTimespanUnit.value,
      allowDecreasingValues: allowDecreasingValues.value,
    })

    emit('save', props.stream)
  } catch (e) {
    console.error(e)
    alert('Error saving scheduling settings')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="scheduling-root">
    <h2 class="section-title">Scheduling</h2>

    <div class="scheduling-layout">
      <div class="left-col">
        <!-- Execution Mode -->
        <div class="stream-box category-box">
          <h3 class="category-title">OCR Execution Mode</h3>
          <div class="category-body">
            <label class="radio-row">
              <input type="radio" value="on_api_call" v-model="executionMode" />
              <span>On every API call</span>
            </label>
            <label class="radio-row">
              <input type="radio" value="interval" v-model="executionMode" />
              <span>On interval (cron-like)</span>
            </label>
            <label class="radio-row">
              <input type="radio" value="manual" v-model="executionMode" />
              <span>Manual (button-triggered)</span>
            </label>

            <div v-if="executionMode === 'interval'" class="interval-block">
              <label>Cron preset</label>
              <select v-model="intervalPreset">
                <option value="1">every 1 min (* * * * *)</option>
                <option value="5">every 5 min (*/5 * * * *)</option>
                <option value="15">every 15 min (*/15 * * * *)</option>
                <option value="60">every 1 hour (0 * * * *)</option>
                <option value="custom">custom</option>
              </select>

              <div class="form-field">
                <label>Cron expression</label>
                <input 
                  type="text" 
                  v-model="cronExpression" 
                  placeholder="e.g. 0 * * * *"
                  :readonly="intervalPreset !== 'custom'"
                />
              </div>

              <div class="form-field readonly">
                <label>Next scheduled run</label>
                <div class="readonly-value">{{ nextRun || '—' }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Cache Settings -->
        <div class="stream-box category-box">
          <h3 class="category-title">OCR Cache</h3>
          <div class="category-body">
            <label class="checkbox-row">
              <input type="checkbox" v-model="cacheEnabled" />
              <span>Enable cache</span>
            </label>

            <div v-if="cacheEnabled" class="cache-block">
              <div class="form-field">
                <label>Cache duration</label>
                <div style="display:flex;gap:8px;">
                  <input type="number" v-model="cacheDuration" min="1" />
                  <select v-model="cacheDurationUnit">
                    <option value="minutes">minutes</option>
                    <option value="hours">hours</option>
                    <option value="days">days</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Delta / Value Change -->
        <div class="stream-box category-box">
          <h3 class="category-title">OCR Value Adjustment</h3>
          <div class="category-body">
            <label class="checkbox-row">
              <input type="checkbox" v-model="allowDecreasingValues" />
              <span>Allow decreasing values</span>
            </label>

            <label class="checkbox-row">
              <input type="checkbox" v-model="deltaTracking" />
              <span>Enable delta tracking</span>
            </label>

            <div v-if="deltaTracking" class="delta-block">
              <div class="form-field">
                <label>Increase amount</label>
                <input type="number" v-model="deltaAmount" step="any" />
              </div>

              <div class="form-field">
                <label>Timespan</label>
                <div style="display:flex;gap:8px;align-items:center;">
                  <input type="number" v-model="deltaTimespan" min="1" />
                  <select v-model="deltaTimespanUnit">
                    <option value="minutes">minutes</option>
                    <option value="hours">hours</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Save controls -->
        <div style="margin-top:10px; display:flex; gap:12px; align-items:center;">
          <button 
            class="save-button"
            @click="saveChanges"
            :disabled="!isDirty || saving"
            :class="{ 'disabled': !isDirty || saving }"
          >
            <span class="button-content">
              <span class="spinner" v-if="saving"></span>
              <span class="text" :class="{ invisible: saving }">Save Changes</span>
            </span>
          </button>

          <template v-if="loading">
            <div class="skeleton skeleton-text"></div>
          </template>
          <template v-else>
            <div style="color:#aaa; font-size:0.95rem;">{{ isDirty ? 'Unsaved changes' : 'Saved' }}</div>
          </template>
        </div>
      </div>

      <!-- right column reserved / empty for now -->
      <div class="right-col">
        <!-- empty placeholder - keep layout consistent with other tabs -->
      </div>
    </div>
  </div>
</template>

<style scoped>
.scheduling-root { display:flex; flex-direction:column; gap:16px; color:white; }
.section-title { font-size:1.5rem; font-weight:600; }

/* layout similar to parser */
.scheduling-layout { display:grid; grid-template-columns: 1fr 0px; gap:20px; align-items:start; } /* Originally 1fr 300px. */
.left-col { display:flex; flex-direction:column; gap:12px; }
.right-col { /* empty placeholder */ }

/* reuse parser-like box styling */
.stream-box {
  background: #23252c;
  padding: 14px;
  border-radius: 15px;
  border: 2px solid #2d2f37;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* semantic category class */
.category-box { padding: 12px 14px; }
.category-title { color:#40F284; font-size:1.05rem; margin:0; font-weight:700; }
.category-body { display:flex; flex-direction:column; gap:10px; margin-top:6px; }

.radio-row, .checkbox-row { display:flex; align-items:center; gap:8px; color:#ddd; font-size:0.98rem; }
.form-field { display:flex; flex-direction:column; gap:6px; }
label { color:#aaa; font-size:0.95rem; }
input[type="text"], input[type="number"], select {
  background: #1e1f25;
  color: white;
  border: 1px solid #2d2f37;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 0.98rem;
}

input[type="text"]:read-only {
  background: #15161a;
  color: #ccc;
}

.readonly { opacity:0.95; }
.readonly-value { background:#15161a; border-radius:6px; padding:8px; font-size:0.95rem; color:#ccc; border:1px solid #2d2f37; }

.save-button {
  position: relative;
  align-self: flex-start;
  background-color: #40F284;
  color: black;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  min-width: 140px;
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.save-button.disabled { background-color:#444; color:#999; cursor:not-allowed; }
.save-button:disabled { pointer-events:none; }

.skeleton {
  background: #2d3038;
  border-radius: 6px;
  position: relative;
  overflow: hidden;
}

.skeleton::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(74, 77, 87, 0.3),
    transparent
  );
  animation: shimmer 1.5s infinite;
}

.skeleton-text {
  width: 120px;  /* matches approx length of "Loading…" */
  height: 16px;
}

@keyframes shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}


.button-content { position:relative; display:flex; align-items:center; justify-content:center; }
.spinner { position:absolute; width:16px; height:16px; border:3px solid black; border-top:3px solid transparent; border-radius:50%; animation:spin 0.8s linear infinite; }
.text { transition: opacity 0.2s ease; }
.invisible { opacity:0; }

@keyframes spin { 0%{transform:rotate(0deg)} 100%{transform:rotate(360deg)} }
</style>
