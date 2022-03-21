import scrapy
import json
from scrapy.loader import ItemLoader
from ..items import Protocol
from playwright.sync_api import sync_playwright 

# Defillama's backend API URL format
# https://defillama.com/_next/data/{dynamic_url}/protocol/{protocol_name}.json
# https://defillama.com/_next/data/{dynamic_url}/chain/{chain_name}.json

with sync_playwright() as p:
    
    def find_dynamic_url(response):
        """Intercept AJAX request to capture the dynamic URL for this session"""
        global dynamic_url
        
        if 'json' in response.url:
            # https://defillama.com/_next/data/ozCSq74DvtFFUyHU_j6TZ/nfts.json
            print('\n<< Intercepted:', response.url)
            dynamic_url = response.url.split('/')[-2]
            print('<< Dynamic part:', dynamic_url, '\n')
    
    
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("response", find_dynamic_url)
    page.goto(
        "https://defillama.com/protocol/curve", 
        wait_until="networkidle", 
        timeout=5000) 
    page.context.close()
    browser.close()
    
class DefiSpider(scrapy.Spider):
    name = 'defi'
    start_urls = ['http://defillama.com/']

    def parse(self, response):
        """Get the list of protocol names to construct URLs for requests"""
        
        names = response.xpath('//table/tbody/tr/td[1]/div/a//text()').getall()
        # >> ['Curve (CRV)', 'MakerDAO (MKR)', ... ]

        cleaned_names = []
        for name in names:
            if ' (' in name:
                clean = name.split(' (')[0]
                clean = clean.replace(' ', '-')
                cleaned_names.append(clean)
            # Not all names have abbreviated symbols
            else:
                cleaned_names.append(name.replace(' ', '-'))

        # Construct URLs and yield request
        for name in cleaned_names:
            url = f'https://defillama.com/_next/data/{dynamic_url}/protocol/{name}.json'
            
            yield scrapy.Request(url, callback=self.parse_json)
        
    def parse_json(self, response):
        """Extract the data I'm interested in"""
        
        # Response: 
        # {"pageProps":{"protocol":"curve","protocolData":
        # {"id":"3","name":"Curve","address":"0xD533a949740bb3306d119CC777fa900bA034cd52",
        # "symbol":"CRV","url":"https://curve.fi","description":"Curve is a...","chain":"Ethereum",
        # "logo":"https://icons.llama.fi/curve.png","audits":"2","audit_note":null,
        # "gecko_id":"curve-dao-token","cmcId":"6538","category":"Dexes",
        # "chains":["Optimism",
        # "Avalanche","Harmony","Ethereum","Gnosis","Polygon","Arbitrum","Fantom"],
        # "module":"curve/index.js","twitter":"CurveFinance","audit_links":["https://curve.fi/audits"],
        # "oracles":[],"language":"Vyper","misrepresentedTokens":true,"chainTvls":{"Optimism":446959.28555037425,
        # "Avalanche":1174724867.9220846,"Harmony":45007459.13696608,"Ethereum":15471177788.708889,
        # "Gnosis":115346032.80414289,"Ethereum-staking":852791930.3983748,"Polygon":329655701.7954085,
        # "Arbitrum":158055475.5184736,"Fantom":498316407.04694664,"staking":852791930.3983748},
        # "currentChainTvls":{"Optimism":446959.28555037425,"Avalanche":1174724867.9220846,
        # "Harmony":45007459.13696608,"Ethereum":15471177788.708889,"Gnosis":115346032.80414289,
        # "Ethereum-staking":852791930.3983748,"Polygon":329655701.7954085,"Arbitrum":158055475.5184736,
        # "Fantom":498316407.04694664,"staking":852791930.3983748},"tvl":17792731790.92742,"tokensInUsd":[{"date":1581206400,"tokens":
        
        text = json.loads(response.body)
        data = text['pageProps']['protocolData']
        
        # Now pass to ItemLoader 
        il = ItemLoader(item=Protocol())
        
        il.add_value('name', data.get('name', ''))
        il.add_value('address', data.get('address', ''))
        il.add_value('chains', data.get('chains', ''))
        il.add_value('twitter', data.get('twitter', ''))
        il.add_value('chain_tvls', data.get('chain_tvls', ''))
        il.add_value('tvl', data.get('tvl', ''))
        
        yield il.load_item()
        

        