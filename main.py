import os

import requests
import telegram
from bs4 import BeautifulSoup

bot = telegram.Bot(token=os.environ["TELEGRAM_TOKEN"])
url = os.environ['BESTBUY_LINK']
chat_id = os.environ['CHAT_ID']


def webhook(request):
    if request.method == "POST":
        response = requests.get(url, headers={'user-agent': 'PostmanRuntime/7.26.8'})
        soup = BeautifulSoup(response.text)
        button = soup.find('button', {'class': 'add-to-cart-button'})
        if 'btn-disabled' not in button.attrs['class']:
            bot.sendMessage(chat_id=chat_id, text=f'PS5 is available at {url}')
    return "ok"
