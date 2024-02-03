# coffeecam
Coffeecam telegram bot to check ASki's coffee machine's status.

# Useful links
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

# Setup
- Tp-link Tapo C100 camera in the same local network
- The bot needs a volume at /mnt/ramdisk, give it in compose file
- TELEGRAM_TOKEN, TAPO_USERNAME and TAPO_PASSWORD should be given in .env file
- Also STORE as a path to file to maintain (in ram), and DATABASE as path to file in persistent storage.
- HOST is hardcoded in app.py
- To get it running: pull the repo or simply copy the docker-compose.yml
- run: docker compose up