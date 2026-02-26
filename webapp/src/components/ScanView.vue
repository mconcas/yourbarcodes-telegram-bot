<template>
  <div class="scan-view">
    <!-- Native scanner available -->
    <v-card
      v-if="supportsNativeScanner"
      class="ma-4"
      variant="outlined"
      rounded="xl"
    >
      <v-card-text class="text-center pa-8">
        <v-icon size="80" color="primary" class="mb-4">mdi-qrcode-scan</v-icon>
        <div class="text-h6 mb-2">Native Scanner</div>
        <div class="text-body-2 text-medium-emphasis mb-6">
          Uses your device's camera for fast, reliable scanning.
          Supports QR codes and most barcode formats.
        </div>
        <v-btn
          color="primary"
          size="large"
          rounded="pill"
          prepend-icon="mdi-camera"
          @click="openNativeScanner"
        >
          Open Scanner
        </v-btn>
      </v-card-text>
    </v-card>

    <v-divider v-if="supportsNativeScanner" class="mx-4">
      <span class="text-medium-emphasis text-caption px-2">or enter manually</span>
    </v-divider>

    <!-- Fallback: not native scanner available -->
    <v-card
      v-if="!supportsNativeScanner"
      class="ma-4"
      variant="outlined"
      rounded="xl"
    >
      <v-card-text class="text-center pa-6">
        <v-icon size="48" color="warning" class="mb-3">mdi-camera-off</v-icon>
        <div class="text-body-1 mb-2">
          Native scanner not available on this client.
        </div>
        <div class="text-body-2 text-medium-emphasis">
          Use the manual entry below, or open on your phone.
        </div>
      </v-card-text>
    </v-card>

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
          size="large"
          rounded="pill"
          :disabled="!manualCode"
          prepend-icon="mdi-send"
          @click="submitManual"
        >
          Send to Bot
        </v-btn>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'ScanView',

  props: {
    themeColors: { type: Object, required: true },
    isTelegramClient: { type: Boolean, default: false },
    supportsNativeScanner: { type: Boolean, default: false },
  },

  emits: ['scanned', 'send'],

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
    openNativeScanner() {
      this.TMA.showScanQrPopup({ text: 'Point at a barcode or QR code' })
    },

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
