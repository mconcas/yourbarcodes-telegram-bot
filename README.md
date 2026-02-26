# Barcode Bot

A Telegram bot that stores loyalty-card barcodes and generates scannable images on the fly. No images are stored — only the barcode identifiers.

## Features

- **Scan barcodes** via an in-app camera scanner (Mini App) — supports EAN-13, Code 128, QR Code
- **Store cards** in OpenSearch, tied to your Telegram account
- **Generate barcodes** on demand when you select a saved card
- **Works in groups** — deep-links to private chat for scanning, card retrieval works everywhere
- **Manual entry** — type a barcode number if you can't scan it

## Stack

| Component | Technology |
|-----------|-----------|
| Bot | Python 3.12, [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) |
| Storage | OpenSearch 2.11 |
| Scanner webapp | Vue 3 + Vuetify 3 + [html5-qrcode](https://github.com/mebjas/html5-qrcode) |
| Hosting | Docker Compose (bot + OpenSearch), GitHub Pages (webapp) |

## Quick start

```bash
cp .env.example .env
# Edit .env and set TELEGRAM_BOT_TOKEN (from @BotFather)
docker compose up -d
```

The bot will connect to OpenSearch, create the index, and start polling for updates.

### Scanner webapp

The webapp is deployed automatically to GitHub Pages on push to `master` (see `.github/workflows/deploy-webapp.yml`). Set `WEBAPP_URL` in `.env` to the Pages URL.

To run locally:

```bash
cd webapp
npm install
npm run dev
```

## Bot commands

| Command | Description |
|---------|-------------|
| `/start` | Show main menu |
| `/addcard` | Add a new card (name → code → format) |
| `/mycards` | List saved cards, tap to generate barcode |
| `/deletecard` | Delete a saved card |
| `/cancel` | Cancel current operation |

## Project structure

```
├── bot/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # Entry point
│       ├── config.py            # Environment config
│       ├── handlers/
│       │   ├── start.py         # /start, menu navigation
│       │   ├── cards.py         # Card CRUD + add-card conversation
│       │   └── scan.py          # Photo decoding + webapp scan flow
│       └── services/
│           ├── opensearch_client.py
│           ├── barcode_generator.py
│           └── barcode_decoder.py
├── webapp/                      # Vue Mini App (GitHub Pages)
│   ├── src/
│   │   ├── App.vue
│   │   └── components/
│   │       ├── ScanView.vue
│   │       ├── BarcodeScanner.vue
│   │       ├── RecentScans.vue
│   │       └── ResultDialog.vue
│   └── vite.config.js
├── docker-compose.yml
└── .env.example
```

## License

MIT
