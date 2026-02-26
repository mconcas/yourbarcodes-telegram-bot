<template>
  <div class="recent-scans">
    <v-card v-if="!scans.length" class="ma-4" variant="flat">
      <v-card-text class="text-center pa-8">
        <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-barcode-off</v-icon>
        <div class="text-h6 text-medium-emphasis mb-2">No scans yet</div>
        <div class="text-body-2 text-medium-emphasis">
          Scan a barcode to see it here.
        </div>
      </v-card-text>
    </v-card>

    <v-expansion-panels v-if="scans.length" v-model="expandedPanels" class="ma-4">
      <v-expansion-panel
        v-for="(scan, index) in scans"
        :key="scan.timestamp"
        rounded="xl"
        class="mb-2"
      >
        <v-expansion-panel-title>
          <v-row no-gutters align="center">
            <v-col cols="auto" class="mr-3">
              <v-avatar :color="getFormatColor(scan.format)" size="40">
                <v-icon color="white" size="20">{{ getFormatIcon(scan.format) }}</v-icon>
              </v-avatar>
            </v-col>
            <v-col>
              <div class="text-subtitle-1 font-weight-medium">
                {{ limitLength(scan.code, 30) }}
              </div>
              <div class="text-caption text-medium-emphasis">
                {{ getFormatLabel(scan.format) }} · {{ formatTime(scan.timestamp) }}
              </div>
            </v-col>
          </v-row>
        </v-expansion-panel-title>

        <v-expansion-panel-text>
          <div class="code-display pa-3 mb-3">
            <code class="text-body-2">{{ scan.code }}</code>
          </div>

          <div class="d-flex gap-2">
            <v-btn
              color="primary"
              variant="flat"
              rounded="pill"
              prepend-icon="mdi-send"
              size="small"
              @click="$emit('select', scan)"
            >
              Send to Bot
            </v-btn>
            <v-spacer />
            <v-btn
              color="error"
              variant="text"
              rounded="pill"
              prepend-icon="mdi-delete-outline"
              size="small"
              @click="$emit('remove', index)"
            >
              Remove
            </v-btn>
          </div>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>
</template>

<script>
export default {
  name: 'RecentScans',

  props: {
    scans: { type: Array, required: true },
    themeColors: { type: Object, required: true },
  },

  emits: ['select', 'remove'],

  data() {
    return {
      expandedPanels: [],
    }
  },

  methods: {
    getFormatIcon(format) {
      const map = {
        'EAN_13': 'mdi-barcode',
        'EAN_8': 'mdi-barcode',
        'CODE_128': 'mdi-barcode',
        'QR_CODE': 'mdi-qrcode',
      }
      return map[format] || 'mdi-barcode'
    },

    getFormatColor(format) {
      const map = {
        'EAN_13': '#4caf50',
        'EAN_8': '#4caf50',
        'CODE_128': '#2196f3',
        'QR_CODE': '#9c27b0',
      }
      return map[format] || '#757575'
    },

    getFormatLabel(format) {
      const map = {
        'EAN_13': 'EAN-13',
        'EAN_8': 'EAN-8',
        'CODE_128': 'Code 128',
        'QR_CODE': 'QR Code',
      }
      return map[format] || format
    },

    limitLength(value, max) {
      if (!value) return ''
      return value.length <= max ? value : value.substring(0, max) + '…'
    },

    formatTime(timestamp) {
      const d = new Date(timestamp)
      const pad = (n) => n.toString().padStart(2, '0')
      return `${pad(d.getDate())}/${pad(d.getMonth() + 1)} ${pad(d.getHours())}:${pad(d.getMinutes())}`
    },
  },
}
</script>

<style scoped>
.recent-scans {
  padding-bottom: 80px;
}
.code-display {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 12px;
  word-break: break-all;
  font-family: monospace;
}
.gap-2 {
  gap: 8px;
}
</style>
