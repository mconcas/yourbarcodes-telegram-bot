<template>
  <v-dialog
    :model-value="modelValue"
    max-width="420"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card v-if="result" rounded="xl" class="result-card">
      <!-- Success animation header -->
      <div class="result-header text-center pa-6">
        <div class="success-circle mb-3">
          <v-icon size="48" color="white">mdi-check</v-icon>
        </div>
        <div class="text-h6 font-weight-bold">Barcode Detected!</div>
      </div>

      <v-divider />

      <v-card-text class="pa-5">
        <!-- Code display -->
        <div class="code-box pa-4 mb-4">
          <div class="text-overline text-medium-emphasis mb-1">Code</div>
          <div class="text-h6 font-weight-medium" style="word-break: break-all; font-family: monospace;">
            {{ result.code }}
          </div>
        </div>

        <!-- Format chip -->
        <div class="d-flex align-center mb-2">
          <v-icon class="mr-2" size="20" color="primary">{{ formatIcon }}</v-icon>
          <span class="text-body-1">{{ formatLabel }}</span>
          <v-spacer />
          <v-chip
            :color="formatChipColor"
            size="small"
            variant="tonal"
          >
            {{ formatLabel }}
          </v-chip>
        </div>
      </v-card-text>

      <v-divider />

      <v-card-actions class="pa-4">
        <v-btn
          variant="text"
          rounded="pill"
          prepend-icon="mdi-camera-retake"
          @click="$emit('scan-again')"
        >
          Scan Again
        </v-btn>
        <v-spacer />
        <v-btn
          color="primary"
          variant="flat"
          rounded="pill"
          size="large"
          prepend-icon="mdi-check-circle"
          @click="$emit('send', result)"
        >
          Confirm code
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'ResultDialog',

  props: {
    modelValue: { type: Boolean, default: false },
    result: { type: Object, default: null },
    themeColors: { type: Object, required: true },
  },

  emits: ['update:modelValue', 'send', 'scan-again'],

  computed: {
    formatIcon() {
      if (!this.result) return 'mdi-barcode'
      const map = {
        'EAN_13': 'mdi-barcode',
        'EAN_8': 'mdi-barcode',
        'CODE_128': 'mdi-barcode',
        'QR_CODE': 'mdi-qrcode',
      }
      return map[this.result.format] || 'mdi-barcode'
    },

    formatLabel() {
      if (!this.result) return ''
      const map = {
        'EAN_13': 'EAN-13',
        'EAN_8': 'EAN-8',
        'CODE_128': 'Code 128',
        'QR_CODE': 'QR Code',
      }
      return map[this.result.format] || this.result.format
    },

    formatChipColor() {
      if (!this.result) return 'grey'
      const map = {
        'EAN_13': 'success',
        'EAN_8': 'success',
        'CODE_128': 'info',
        'QR_CODE': 'purple',
      }
      return map[this.result.format] || 'grey'
    },
  },
}
</script>

<style scoped>
.result-header {
  background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%);
  color: white;
}

.success-circle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  animation: pop-in 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.code-box {
  background: rgba(0, 0, 0, 0.04);
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

@keyframes pop-in {
  0% { transform: scale(0); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

.result-card {
  overflow: hidden;
}
</style>
