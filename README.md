# Defillama Scraper
```bash
├── defi
│   ├── data.json
│   ├── defi
│   │   ├── __init__.py
│   │   ├── items.py
│   │   ├── middlewares.py
│   │   ├── pipelines.py
│   │   ├── settings.py
│   │   └── spiders
│   │       ├── __init__.py
│   │       ├── scraper.py
│   │       └── test.json
│   └── scrapy.cfg
├── postgres_loader.py
├── postgres_tables.txt
```
This scraper grabs DeFi protocol data from https://defillama.com/ and writes to an AWS Postgres DB.
![image](https://user-images.githubusercontent.com/62268115/159244693-828fae04-26c1-42d7-a371-fbf3da8b82ef.png)


It's probably a good sign whenever you're greeted with a price chart like that on the homepage as there should be json data that got loaded behind it. After inspecting the Network tab in the dev tools I confirmed there was a backend call being made.  Playwright was used to intercept a session-specific URL from that AJAX call when the homepage is loaded. 

![image](https://user-images.githubusercontent.com/62268115/159244955-c8ee8bf3-c448-41f6-a41f-8c480ab4f8f1.png)

To create the specific URLs needed for the protocol data, I had to scrape the protocol names from the table that's visible in the first photo.  Those are then used in combination with the intercepted URL to query data directly from the server.

![image](https://user-images.githubusercontent.com/62268115/159245704-e347d638-03e4-4dc5-9fde-6acff2436316.png)

Doing data cleaning like that within a spider seems out of place, however I couldn't find a better place to do it in Scrapy's middlewares.  And since it's specifically for URL generation it's probably fine.

The json data that get's returned is then parsed using Scrapy’s ItemLoader.  Admittedly, there wasn't a real need for ItemLoader in this case. It's a nice feature though and I wanted to include it just to learn more about it - which I did.

![image](https://user-images.githubusercontent.com/62268115/159249723-129f40bf-eb03-4302-b046-0d2abd974447.png)

From there it's almost a straight shot into Postgres. While there is support for S3 as an endpoint for Scrapy’s export feed, there isn’t for Postgres. So the json data is saved locally to a temporary file before being written to the database.

The amount of data being uploaded is minimal. The purpose of this project was to gain more experience with different tools rather than actually accumulate DeFi data (and expenses).
