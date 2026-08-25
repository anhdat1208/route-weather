# Review package Task 6
BASE: 270b8d9031e897fcf9bd1c57891458494cefcae0
HEAD: 7c3d6468110b9287dac7f75a0e0bf13620b74b9d

## Commits


## Stat
 frontend/app/components/RadarControls.vue | 66 -------------------------------
 1 file changed, 66 deletions(-)

## Diff
diff --git a/frontend/app/components/RadarControls.vue b/frontend/app/components/RadarControls.vue
index cff98ff..ce25001 100644
--- a/frontend/app/components/RadarControls.vue
+++ b/frontend/app/components/RadarControls.vue
@@ -26,20 +26,64 @@
 
     <div v-if="rainCellsEnabled && routeReady" class="space-y-1 text-xs">
       <div v-if="rainCellsLoading" class="text-slate-400">─Éang ph├ón t├¡ch v├╣ng m╞░aΓÇª</div>
       <div v-else-if="rainCellsError" class="text-amber-400">{{ rainCellsError }}</div>
       <div v-else-if="rainCellCount !== null" class="text-slate-300">
         {{ rainCellCount }} v├╣ng m╞░a ─æang theo d├╡i
         <span v-if="rainCellsFramesUsed"> ┬╖ {{ rainCellsFramesUsed }} khung radar</span>
       </div>
     </div>
 
+    <label class="flex cursor-pointer items-center gap-2">
+      <input
+        type="checkbox"
+        class="h-4 w-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
+        :checked="nowcastingEnabled"
+        :disabled="!routeReady"
+        @change="onNowcastingToggle"
+      />
+      <span :class="routeReady ? '' : 'text-slate-500'">Nowcasting (dß╗▒ b├ío m╞░a)</span>
+    </label>
+    <p v-if="!routeReady" class="text-[10px] text-slate-500">Cß║ºn c├│ lß╗Ö tr├¼nh ─æß╗â dß╗▒ b├ío m╞░a.</p>
+
+    <div v-if="nowcastingEnabled && routeReady" class="space-y-2">
+      <div class="space-y-1 text-xs">
+        <div v-if="nowcastingLoading" class="text-slate-400">─Éang dß╗▒ b├ío m╞░aΓÇª</div>
+        <div v-else-if="nowcastingError" class="text-amber-400">{{ nowcastingError }}</div>
+        <div v-else-if="nowcastPredictionCount !== null" class="text-slate-300">
+          {{ nowcastPredictionCount }} v├╣ng m╞░a dß╗▒ b├ío
+        </div>
+      </div>
+
+      <div class="flex flex-wrap gap-1">
+        <button
+          v-for="option in horizonOptions"
+          :key="option.value"
+          type="button"
+          class="rounded border px-2 py-0.5 text-[11px] font-medium"
+          :class="
+            selectedHorizon === option.value
+              ? 'border-blue-500 bg-blue-500/20 text-blue-400'
+              : 'border-slate-600 text-slate-400 hover:border-slate-500 hover:text-slate-200'
+          "
+          @click="$emit('update:selectedHorizon', option.value)"
+        >
+          {{ option.label }}
+        </button>
+      </div>
+
+      <p class="text-[10px] text-slate-500">
+        Dß╗▒ b├ío baseline ΓÇö kh├┤ng phß║úi radar quan s├ít
+        <span v-if="nowcastingModelLabel"> ┬╖ {{ nowcastingModelLabel }}</span>
+      </p>
+    </div>
+
     <label class="flex cursor-pointer items-center gap-2">
       <input
         type="checkbox"
         class="h-4 w-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
         :checked="enabled"
         @change="onToggle"
       />
       <span>Radar m╞░a</span>
     </label>
 
@@ -117,20 +161,21 @@
           <span class="font-medium">Satellite</span>
           <span v-if="satelliteTimestampDisplay"> ┬╖ {{ satelliteTimestampDisplay }} (UTC+7)</span>
           <span v-if="satelliteFreshnessLabel"> ┬╖ {{ satelliteFreshnessLabel }}</span>
         </div>
       </template>
     </div>
   </div>
 </template>
 
 <script setup lang="ts">
+import type { NowcastSelectedHorizon } from "~/types/nowcasting"
 import type { RadarFrameResponse, RadarLegend } from "~/types/radar"
 
 const props = defineProps<{
   enabled: boolean
   opacity: number
   loading: boolean
   errorMessage: string | null
   frame: RadarFrameResponse | null
   freshnessLabel: string | null
   timestampDisplay: string | null
@@ -140,31 +185,48 @@ const props = defineProps<{
   rainCellCount: number | null
   rainCellsFramesUsed: number | null
   routeReady: boolean
   satelliteEnabled: boolean
   satelliteOpacity: number
   satelliteLoading: boolean
   satelliteErrorMessage: string | null
   satelliteStatus: "ok" | "stale" | "unavailable" | null
   satelliteFreshnessLabel: string | null
   satelliteTimestampDisplay: string | null
+  nowcastingEnabled: boolean
+  nowcastingLoading: boolean
+  nowcastingError: string | null
+  nowcastingModelLabel: string | null
+  selectedHorizon: NowcastSelectedHorizon
+  nowcastPredictionCount: number | null
 }>()
 
 const emit = defineEmits<{
   "update:enabled": [value: boolean]
   "update:opacity": [value: number]
   "update:rainCellsEnabled": [value: boolean]
   "update:satelliteEnabled": [value: boolean]
   "update:satelliteOpacity": [value: number]
+  "update:nowcastingEnabled": [value: boolean]
+  "update:selectedHorizon": [value: NowcastSelectedHorizon]
   refresh: []
 }>()
 
+const horizonOptions: { value: NowcastSelectedHorizon; label: string }[] = [
+  { value: 0, label: "NOW" },
+  { value: 5, label: "+5m" },
+  { value: 10, label: "+10m" },
+  { value: 15, label: "+15m" },
+  { value: 30, label: "+30m" },
+  { value: 60, label: "+60m" },
+]
+
 const legend = computed<RadarLegend | null>(() => props.frame?.legend ?? null)
 
 const statusClass = computed(() => {
   if (props.frame?.status === "stale") return "text-amber-400"
   if (props.frame?.status === "ok") return "text-green-400"
   return "text-slate-400"
 })
 
 const satelliteStatusClass = computed(() => {
   if (props.satelliteStatus === "stale") return "text-amber-400"
@@ -177,18 +239,22 @@ function onToggle(event: Event) {
 }
 
 function onOpacity(event: Event) {
   emit("update:opacity", Number((event.target as HTMLInputElement).value))
 }
 
 function onRainCellsToggle(event: Event) {
   emit("update:rainCellsEnabled", (event.target as HTMLInputElement).checked)
 }
 
+function onNowcastingToggle(event: Event) {
+  emit("update:nowcastingEnabled", (event.target as HTMLInputElement).checked)
+}
+
 function onSatelliteToggle(event: Event) {
   emit("update:satelliteEnabled", (event.target as HTMLInputElement).checked)
 }
 
 function onSatelliteOpacity(event: Event) {
   emit("update:satelliteOpacity", Number((event.target as HTMLInputElement).value))
 }
 </script>
