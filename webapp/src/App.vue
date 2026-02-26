<template>
  <v-app :style="appStyle">
    <v-main>
      <v-container fluid class="pa-0">
        <!-- Header -->
        <v-toolbar
          :color="themeColors.bgColor"
          flat
          density="compact"
        >
          <v-toolbar-title class="text-h6 font-weight-bold" :style="{ color: themeColors.textColor }">
            <v-icon class="mr-2">mdi-barcode-scan</v-icon>
            Barcode Scanner
          </v-toolbar-title>
        </v-toolbar>

        <!-- Tab Navigation -->
        <v-tabs
          v-model="activeTab"
          :bg-color="themeColors.bgColor"
          :color="themeColors.buttonColor"
          grow
          density="comfortable"
        >
          <v-tab value="scan">
            <v-icon start>mdi-camera</v-icon>
            Scan
          </v-tab>
          <v-tab value="recent">
            <v-icon start>mdi-history</v-icon>
            Recent
            <v-badge
              v-if="recentScans.length"
              :content="recentScans.length"
              color="primary"
              inline
              class="ml-1"
            />
          </v-tab>
        </v-tabs>

        <v-divider />

        <!-- Scan Tab -->
        <v-window v-model="activeTab">
          <v-window-item value="scan">
            <ScanView
              :theme-colors="themeColors"
              :is-telegram-client="isTelegramClient"
              @detected="onDetected"
              @send="sendToBot"
            />
          </v-window-item>

          <!-- Recent Tab -->
          <v-window-item value="recent">
            <RecentScans
              :scans="recentScans"
              :theme-colors="themeColors"
              @select="onSelectRecent"
              @remove="onRemoveRecent"
            />
          </v-window-item>
        </v-window>

        <!-- Result Dialog -->
        <ResultDialog
          v-model="showResult"
          :result="currentResult"
          :theme-colors="themeColors"
          @send="sendToBot"
          @scan-again="scanAgain"
        />

        <!-- Not compatible warning -->
        <v-dialog v-model="showWarning" max-width="400" persistent>
          <v-card>
            <v-card-title class="text-h6">
              <v-icon color="warning" class="mr-2">mdi-alert</v-icon>
              Compatibility Note
            </v-card-title>
            <v-card-text>
              This Mini App works best on Telegram mobile clients.
              QR scanning may not be available on web or desktop clients.
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn color="primary" @click="showWarning = false">Got it</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
import ScanView from './components/ScanView.vue'
import RecentScans from './components/RecentScans.vue'
import ResultDialog from './components/ResultDialog.vue'

export default {
  components: { ScanView, RecentScans, ResultDialog },

  data() {
    return {
      activeTab: 'scan',
      showResult: false,
      showWarning: false,
      currentResult: null,
      recentScans: [],
      isTelegramClient: false,
    }
  },

  computed: {
    themeColors() {
      const tg = this.TMA
      return {
        bgColor: tg?.themeParams?.bg_color || '#ffffff',
        textColor: tg?.themeParams?.text_color || '#000000',
        hintColor: tg?.themeParams?.hint_color || '#999999',
        buttonColor: tg?.themeParams?.button_color || '#3390ec',
        buttonTextColor: tg?.themeParams?.button_text_color || '#ffffff',
        secondaryBgColor: tg?.themeParams?.secondary_bg_color || '#f0f0f0',
      }
    },

    appStyle() {
      return {
        backgroundColor: this.themeColors.bgColor,
        color: this.themeColors.textColor,
        minHeight: '100vh',
      }
    },
  },

  created() {
    const tg = this.TMA
    if (tg?.platform && tg.platform !== 'unknown') {
      this.isTelegramClient = true
    }

    if (!this.isTelegramClient) {
      this.showWarning = true
    }

    // Load recent scans from session
    this.loadRecentScans()
  },

  mounted() {
    this.TMA?.ready()
    this.TMA?.expand()
  },

  methods: {
    onDetected(result) {
      this.addToRecent(result)
    },

    sendToBot(result) {
      const payload = JSON.stringify({
        code: result.code,
        format: result.format,
      })
      this.showResult = false
      this.TMA.sendData(payload)
      setTimeout(() => this.TMA.close(), 300)
    },

    scanAgain() {
      this.showResult = false
      this.currentResult = null
    },

    onSelectRecent(scan) {
      this.currentResult = scan
      this.showResult = true
    },

    onRemoveRecent(index) {
      this.recentScans.splice(index, 1)
      this.saveRecentScans()
    },

    addToRecent(result) {
      this.recentScans.unshift(result)
      if (this.recentScans.length > 20) {
        this.recentScans.pop()
      }
      this.saveRecentScans()
    },

    loadRecentScans() {
      try {
        const stored = sessionStorage.getItem('barcode_recent')
        if (stored) this.recentScans = JSON.parse(stored)
      } catch { /* ignore */ }
    },

    saveRecentScans() {
      try {
        sessionStorage.setItem('barcode_recent', JSON.stringify(this.recentScans))
      } catch { /* ignore */ }
    },

    detectFormat(code) {
      if (/^\d{13}$/.test(code)) return 'EAN_13'
      if (/^\d{8}$/.test(code)) return 'EAN_8'
      if (/^https?:\/\//.test(code) || code.length > 50) return 'QR_CODE'
      return 'CODE_128'
    },

    haptic(type) {
      try {
        this.TMA?.HapticFeedback?.notificationOccurred(type)
      } catch { /* not supported */ }
    },
  },
}
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  overflow-x: hidden;
  width: 100%;
  max-width: 100vw;
}

/* Prevent Vuetify buttons / cards from overflowing the Mini App frame */
.v-application {
  max-width: 100vw;
  overflow-x: hidden;
}

.v-card-actions {
  flex-wrap: wrap;
  gap: 4px;
}

.v-btn {
  max-width: 100%;
}
</style>
