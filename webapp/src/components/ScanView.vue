<template>
  <div class="scan-view">
    <!-- Scanner mode selector -->
    <v-card class="ma-4" variant="outlined" rounded="xl">
      <v-card-text class="pa-4">
        <div class="text-subtitle-2 text-medium-emphasis mb-3">Choose a scanner</div>

        <v-row dense>
          <!-- In-app barcode scanner (camera-based, handles all formats) -->
          <v-col cols="6">
            <v-card
              :variant="scanMode === 'camera' ? 'flat' : 'outlined'"
              :color="scanMode === 'camera' ? 'primary' : undefined"
              rounded="xl"
              class="scanner-option pa-4 text-center"
              @click="scanMode = 'camera'"
            >
              <v-icon
                size="36"
                :color="scanMode === 'camera' ? 'white' : 'primary'"
                class="mb-2"
              >
                mdi-barcode-scan
              </v-icon>
              <div
                class="text-subtitle-2 font-weight-bold"
                :class="scanMode === 'camera' ? 'text-white' : ''"
              >
                Camera Scanner
              </div>
              <div
                class="text-caption"
                :class="scanMode === 'camera' ? 'text-white' : 'text-medium-emphasis'"
              >
                EAN-13, Code 128, QR
              </div>
            </v-card>
          </v-col>

          <!-- Native Telegram QR scanner -->
          <v-col cols="6">
            <v-card
              :variant="scanMode === 'native' ? 'flat' : 'outlined'"
              :color="scanMode === 'native' ? 'primary' : undefined"
              :disabled="!supportsNativeScanner"
              rounded="xl"
              class="scanner-option pa-4 text-center"
              @click="supportsNativeScanner && (scanMode = 'native')"
            >
              <v-icon
                size="36"
                :color="scanMode === 'native' ? 'white' : supportsNativeScanner ? 'primary' : 'grey'"
                class="mb-2"
              >
                mdi-qrcode-scan
              </v-icon>
              <div
                class="text-subtitle-2 font-weight-bold"
                :class="scanMode === 'native' ? 'text-white' : ''"
              >
                Telegram QR
              </div>
              <div
                class="text-caption"
                :class="scanMode === 'native' ? 'text-white' : 'text-medium-emphasis'"
              >
                {{ supportsNativeScanner ? 'QR codes only' : 'Not available' }}
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- In-app camera scanner -->
    <div v-if="scanMode === 'camera'" class="mx-4">
      <BarcodeScanner
        @scanned="$emit('scanned', $event)"
      />
    </div>

    <!-- Native QR scanner prompt -->
    <v-card
      v-if="scanMode === 'native'"
      class="ma-4"
      variant="outlined"
      rounded="xl"
    >
      <v-card-text class="text-center pa-6">
        <v-icon size="64" color="primary" class="mb-3">mdi-qrcode-scan</v-icon>
        <div class="text-h6 mb-2">Telegram QR Scanner</div>
        <div class="text-body-2 text-medium-emphasis mb-5">
          Uses Telegram's built-in scanner.<br/>
          Best for QR codes — fast and reliable.
        </div>
        <v-btn
          color="primary"
          size="large"
          rounded="pill"
          prepend-icon="mdi-camera"
          @click="openNativeScanner"
        >
          Open QR Scanner
        </v-btn>
      </v-card-text>
    </v-card>

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
import BarcodeScanner from './BarcodeScanner.vue'

export default {
  name: 'ScanView',

  components: { BarcodeScanner },

  props: {
    themeColors: { type: Object, required: true },
    isTelegramClient: { type: Boolean, default: false },
    supportsNativeScanner: { type: Boolean, default: false },
  },

  emits: ['scanned', 'send'],

  data() {
    return {
      scanMode: 'camera',
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
      this.TMA.showScanQrPopup({ text: 'Point at a QR code' })
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
