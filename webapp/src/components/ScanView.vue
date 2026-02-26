<template>
  <div class="scan-view">
    <!-- Camera barcode scanner -->
    <div class="mx-4 mt-4">
      <BarcodeScanner
        @detected="$emit('detected', $event)"
        @send="$emit('send', $event)"
      />
    </div>

    <!-- Divider -->
    <v-divider class="mx-4">
      <span class="text-medium-emphasis text-caption px-2">or enter manually</span>
    </v-divider>

    <!-- Manual entry -->
    <v-card class="ma-4" variant="outlined" rounded="xl">
      <v-card-text class="pa-5">
        <div class="text-subtitle-1 font-weight-medium mb-4">
          <v-icon class="mr-1">mdi-keyboard</v-icon>
          Manual Entry
        </div>

        <v-text-field
          v-model="manualCode"
          label="Barcode number"
          placeholder="e.g. 4006381333931"
          variant="outlined"
          rounded="lg"
          density="comfortable"
          prepend-inner-icon="mdi-barcode"
          clearable
          :rules="[v => !!v || 'Enter a code']"
        />

        <v-select
          v-model="manualFormat"
          :items="formatOptions"
          label="Barcode format"
          variant="outlined"
          rounded="lg"
          density="comfortable"
          prepend-inner-icon="mdi-format-list-bulleted-type"
        />

        <v-btn
          block
          color="primary"
          rounded="pill"
          :disabled="!manualCode"
          prepend-icon="mdi-check-circle"
          @click="submitManual"
        >
          Confirm code
        </v-btn>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import BarcodeScanner from './BarcodeScanner.vue'

export default {
  name: 'ScanView',

  components: { BarcodeScanner },

  props: {
    themeColors: { type: Object, required: true },
    isTelegramClient: { type: Boolean, default: false },
  },

  emits: ['detected', 'send'],

  data() {
    return {
      manualCode: '',
      manualFormat: 'EAN_13',
      formatOptions: [
        { title: 'EAN-13', value: 'EAN_13' },
        { title: 'Code 128', value: 'CODE_128' },
        { title: 'QR Code', value: 'QR_CODE' },
      ],
    }
  },

  methods: {
    submitManual() {
      if (!this.manualCode) return
      const result = {
        code: this.manualCode.trim(),
        format: this.manualFormat,
        timestamp: Date.now(),
      }
      this.$emit('send', result)
    },
  },
}
</script>

<style scoped>
.scan-view {
  padding-bottom: 80px;
}
</style>
