<template>
  <div class="barcode-scanner">
    <!-- Camera viewfinder -->
    <v-card
      v-if="!scannedResult"
      class="scanner-card"
      variant="flat"
      rounded="xl"
    >
      <div class="camera-container" :class="{ active: isScanning }">
        <div id="barcode-reader" ref="reader"></div>

        <!-- Scanning overlay with animated line -->
        <div v-if="isScanning" class="scan-overlay">
          <div class="scan-region">
            <div class="scan-line"></div>
            <div class="corner tl"></div>
            <div class="corner tr"></div>
            <div class="corner bl"></div>
            <div class="corner br"></div>
          </div>
        </div>

        <!-- Loading state -->
        <div v-if="isLoading" class="loading-overlay">
          <v-progress-circular indeterminate color="white" size="48" />
          <div class="text-white mt-3">Starting camera…</div>
        </div>
      </div>

      <!-- Controls bar -->
      <v-card-actions class="pa-4 justify-center">
        <v-btn
          v-if="!isScanning"
          color="primary"
          size="large"
          rounded="pill"
          prepend-icon="mdi-camera"
          :loading="isLoading"
          @click="startScanning"
        >
          Start Scanner
        </v-btn>
        <v-btn
          v-else
          color="error"
          variant="tonal"
          size="large"
          rounded="pill"
          prepend-icon="mdi-stop"
          @click="stopScanning"
        >
          Stop
        </v-btn>
      </v-card-actions>

      <!-- Hint -->
      <div class="text-center text-caption text-medium-emphasis pb-3 px-4">
        Point the camera at a barcode. Supports EAN-13, Code 128, QR Code and more.
      </div>
    </v-card>

    <!-- Scanned result inline -->
    <v-card
      v-if="scannedResult"
      class="mx-0"
      variant="outlined"
      rounded="xl"
    >
      <div class="result-banner text-center pa-5">
        <div class="success-icon mb-2">
          <v-icon size="40" color="white">mdi-check-bold</v-icon>
        </div>
        <div class="text-h6 font-weight-bold text-white">Scanned!</div>
      </div>

      <v-card-text class="pa-5">
        <div class="code-display pa-4 mb-3">
          <div class="text-overline text-medium-emphasis mb-1">Code</div>
          <div class="text-h6" style="word-break: break-all; font-family: 'Roboto Mono', monospace;">
            {{ scannedResult.code }}
          </div>
        </div>

        <v-chip
          :color="formatColor"
          variant="tonal"
          size="small"
          prepend-icon="mdi-barcode"
          class="mb-2"
        >
          {{ formatLabel }}
        </v-chip>
      </v-card-text>

      <v-divider />

      <v-card-actions class="pa-4">
        <v-btn
          variant="text"
          rounded="pill"
          prepend-icon="mdi-camera-retake"
          @click="resetAndScan"
        >
          Scan Again
        </v-btn>
        <v-spacer />
        <v-btn
          color="primary"
          variant="flat"
          size="large"
          rounded="pill"
          prepend-icon="mdi-check-circle"
          @click="$emit('send', scannedResult)"
        >
          Confirm code
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script>
import { Html5Qrcode } from 'html5-qrcode'

const FORMAT_MAP = {
  'QR_CODE': { label: 'QR Code', color: 'purple', internal: 'QR_CODE' },
  'EAN_13': { label: 'EAN-13', color: 'success', internal: 'EAN_13' },
  'EAN_8': { label: 'EAN-8', color: 'success', internal: 'EAN_8' },
  'CODE_128': { label: 'Code 128', color: 'info', internal: 'CODE_128' },
  'CODE_39': { label: 'Code 39', color: 'info', internal: 'CODE_39' },
}

export default {
  name: 'BarcodeScanner',

  emits: ['detected', 'send', 'close'],

  data() {
    return {
      scanner: null,
      isScanning: false,
      isLoading: false,
      scannedResult: null,
      retried: false,
    }
  },

  computed: {
    formatLabel() {
      if (!this.scannedResult) return ''
      return FORMAT_MAP[this.scannedResult.format]?.label || this.scannedResult.format
    },
    formatColor() {
      if (!this.scannedResult) return 'grey'
      return FORMAT_MAP[this.scannedResult.format]?.color || 'grey'
    },
  },

  beforeUnmount() {
    this.stopScanning()
  },

  methods: {
    async startScanning() {
      this.isLoading = true
      this.scannedResult = null

      try {
        this.scanner = new Html5Qrcode('barcode-reader', { verbose: false })

        const config = {
          fps: 30,
          qrbox: (w, h) => {
            const side = Math.min(w, h) * 0.85
            return { width: Math.floor(side), height: Math.floor(side * 0.45) }
          },
          disableFlip: false,
          // Request higher resolution + continuous autofocus via advanced constraints
          videoConstraints: {
            facingMode: 'environment',
            width: { ideal: 1920 },
            height: { ideal: 1080 },
            focusMode: { ideal: 'continuous' },
            zoom: { ideal: 1.5 },
          },
        }

        await this.scanner.start(
          config.videoConstraints,
          config,
          this.onScanSuccess,
          () => { /* scan-in-progress errors — ignore */ }
        )

        // Apply autofocus via the video track if the browser supports it
        this.applyAutofocus()

        this.isScanning = true
      } catch (err) {
        console.error('Camera error:', err)
        // Fallback: retry without advanced constraints
        if (!this.retried) {
          this.retried = true
          await this.startScanningFallback()
        }
      } finally {
        this.isLoading = false
      }
    },

    async startScanningFallback() {
      try {
        this.scanner = new Html5Qrcode('barcode-reader', { verbose: false })

        const config = {
          fps: 20,
          qrbox: (w, h) => {
            const side = Math.min(w, h) * 0.85
            return { width: Math.floor(side), height: Math.floor(side * 0.45) }
          },
          disableFlip: false,
        }

        await this.scanner.start(
          { facingMode: 'environment' },
          config,
          this.onScanSuccess,
          () => {}
        )

        this.applyAutofocus()
        this.isScanning = true
      } catch (err) {
        console.error('Camera fallback also failed:', err)
      }
    },

    applyAutofocus() {
      // Try to enable continuous autofocus on the active video track
      try {
        const videoEl = document.querySelector('#barcode-reader video')
        if (!videoEl || !videoEl.srcObject) return
        const track = videoEl.srcObject.getVideoTracks()[0]
        if (!track) return
        const caps = track.getCapabilities?.()
        if (caps?.focusMode?.includes('continuous')) {
          track.applyConstraints({ advanced: [{ focusMode: 'continuous' }] })
        }
        // Also try a slight zoom to help with small barcodes
        if (caps?.zoom) {
          const zoom = Math.min(caps.zoom.max, Math.max(caps.zoom.min, 1.5))
          track.applyConstraints({ advanced: [{ zoom }] })
        }
      } catch { /* not supported — ok */ }
    },

    async stopScanning() {
      if (this.scanner && this.isScanning) {
        try {
          await this.scanner.stop()
        } catch { /* already stopped */ }
      }
      this.isScanning = false
    },

    onScanSuccess(decodedText, decodedResult) {
      // Pause immediately to avoid duplicate scans
      this.scanner.pause(true)
      this.isScanning = false

      const formatName = decodedResult?.result?.format?.formatName || 'CODE_128'

      this.scannedResult = {
        code: decodedText,
        format: formatName,
        timestamp: Date.now(),
      }

      this.$emit('detected', this.scannedResult)

      // Haptic feedback
      try {
        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success')
      } catch { /* not in telegram */ }
    },

    async resetAndScan() {
      // Fully stop and restart
      if (this.scanner) {
        try { await this.scanner.stop() } catch { /* ok */ }
        this.scanner = null
      }
      this.scannedResult = null
      this.isScanning = false

      // Wait for DOM to re-render the reader div
      this.$nextTick(() => {
        this.startScanning()
      })
    },
  },
}
</script>

<style scoped>
.scanner-card {
  overflow: hidden;
}

.camera-container {
  position: relative;
  width: 100%;
  min-height: 280px;
  background: #000;
  overflow: hidden;
}

.camera-container :deep(video) {
  object-fit: cover !important;
  width: 100% !important;
}

/* Hide the default html5-qrcode UI chrome */
.camera-container :deep(#barcode-reader) {
  border: none !important;
}
.camera-container :deep(#barcode-reader__scan_region) {
  min-height: 250px;
}
.camera-container :deep(#barcode-reader__dashboard_section),
.camera-container :deep(#barcode-reader__dashboard_section_swaplink),
.camera-container :deep(#barcode-reader__status_span),
.camera-container :deep(#barcode-reader__header_message),
.camera-container :deep(#barcode-reader img) {
  display: none !important;
}

/* Scanning overlay */
.scan-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.scan-region {
  position: relative;
  width: 75%;
  height: 40%;
  max-width: 350px;
  max-height: 180px;
}

.scan-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #3390ec, transparent);
  box-shadow: 0 0 12px rgba(51, 144, 236, 0.6);
  animation: scan-sweep 2s ease-in-out infinite;
}

@keyframes scan-sweep {
  0%, 100% { top: 0; }
  50% { top: 100%; }
}

/* Corner markers */
.corner {
  position: absolute;
  width: 24px;
  height: 24px;
  border-color: #3390ec;
  border-style: solid;
  border-width: 0;
}
.corner.tl { top: 0; left: 0; border-top-width: 3px; border-left-width: 3px; border-top-left-radius: 6px; }
.corner.tr { top: 0; right: 0; border-top-width: 3px; border-right-width: 3px; border-top-right-radius: 6px; }
.corner.bl { bottom: 0; left: 0; border-bottom-width: 3px; border-left-width: 3px; border-bottom-left-radius: 6px; }
.corner.br { bottom: 0; right: 0; border-bottom-width: 3px; border-right-width: 3px; border-bottom-right-radius: 6px; }

/* Loading */
.loading-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
}

/* Result */
.result-banner {
  background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%);
}

.success-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  animation: pop-in 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes pop-in {
  0% { transform: scale(0); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

.code-display {
  background: rgba(0, 0, 0, 0.04);
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}
</style>
