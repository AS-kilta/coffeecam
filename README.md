# coffeecam
Coffeecam telegram bot to check ASki's coffee machine's status.

# Useful links
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

# Setup
- Tp-link Tapo C100 camera in the same local network
- The bot needs a volume at /mnt/ramdisk, give it in compose file
- TELEGRAM_TOKEN, TAPO_USERNAME, TAPO_PASSWORD, COFFEE_MAKE_COUNT_FILE and COFFEE_MAKE_STATUS_FILE should be given in .env file
- Also STORE as a path to file to maintain (in ram), and DATABASE as path to file in persistent storage.
- Example env. file:
  TAPO_USERNAME= ...
  TAPO_PASSWORD= ...
  TELEGRAM_TOKEN= ...
  ADMIN_PASSWD= ...
  STORE=/mnt/ramdisk/store.txt
  DATABASE=./persistent/store.txt
  DATABASE2=./persistent/ratings.txt
  COFFEE_MAKE_COUNT_FILE = /coffeeCam/requests/count.txt
  COFFEE_MAKE_STATUS_FILE = /coffeeCam/requests/make.txt
  OLLAMA_URL= ...
- HOST is hardcoded in app.py
- To get it running: pull the repo or simply copy the docker-compose.yml
- run: docker compose up
