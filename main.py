import asyncio
import json
import os
from typing import Dict, Callable, Coroutine, Any

import requests
import telegram
from aiohttp import ClientSession
from bs4 import BeautifulSoup

bot = telegram.Bot(token=os.environ["TELEGRAM_TOKEN"])
bestbuy_ps_url = 'https://www.bestbuy.com/site/sony-playstation-5-console/6426149.p'
bestbuy_xbox_url = 'https://www.bestbuy.com/site/microsoft-xbox-series-x-1tb-console-black/6428324.p?skuId=6428324'
walmart_ps_url = 'https://www.walmart.com/ip/Sony-PlayStation-5-Video-Game-Console/363472942'
target_ps_url = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_fulfillment_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin=81114595&store_id=2128&store_positions_store_id=2128&has_store_positions_store_id=true&scheduled_delivery_store_id=95&pricing_store_id=2128&is_bot=false'
target_xbox_url = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_fulfillment_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin=80790841&store_positions_store_id=95&has_store_positions_store_id=true&pricing_store_id=95&has_pricing_store_id=true&is_bot=false'
chat_id = os.environ['CHAT_ID']

urls = {
    'walmart': walmart_ps_url,
    'target': target_ps_url
}


def bestbuy_fn(resp: str) -> bool:
    button = BeautifulSoup(resp).find('button', {'class': 'add-to-cart-button'})
    return button is not None and 'btn-disabled' not in button.attrs['class']


checking_functions: Dict[str, Callable[[str], bool]] = {
    'bestbuy': bestbuy_fn,
    'walmart': lambda resp: BeautifulSoup(resp).find(lambda tag: 'Add to cart' in tag.text) is not None,
    'target': lambda resp: json.loads(resp)['data']['product']['fulfillment'][
                               'is_out_of_stock_in_all_store_locations'] is False
}


def fetch(session: ClientSession) -> Callable[[str], Coroutine[Any, Any, str]]:
    async def f(url: str) -> str:
        async with session.get(url,
                               headers={
                                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
                               }) as resp:
            return await resp.text()

    return f


def webhook(request):
    async def process():
        async with ClientSession() as session:
            pages = {store: fetch(session)(urls[store]) for store in urls}
            for store in pages:
                page = await pages[store]
                if checking_functions[store](page):
                    bot.sendMessage(chat_id=chat_id, text=f'Console in {store} at {urls[store]}')

    if request.method == "POST":
        asyncio.run(process())
        for url in [bestbuy_ps_url, bestbuy_xbox_url]:
            response = requests.get(url, headers={'user-agent': 'PostmanRuntime/7.26.8'})
            if checking_functions['bestbuy'](response.text):
                bot.sendMessage(chat_id=chat_id, text=f'Console in BestBuy at {urls["bestbuy"]}')
    return "ok"
