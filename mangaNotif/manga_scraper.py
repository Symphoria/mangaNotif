import scrapy
from scrapy.crawler import CrawlerProcess


class MangaSpider(scrapy.Spider):
    name = "updates"
    start_urls = [
        'http://www.mangareader.net/',
    ]

    def parse(self, response):
        base_url = 'http://www.mangareader.net'

        for manga in response.css('div#latestchapters table.updates tr'):
            if manga.css('td.c5::text').extract_first() == 'Today':
                yield {
                    'name': manga.css('a.chapter strong::text').extract_first(),
                    'link_manga': base_url + manga.css('a.chapter::attr(href)').extract_first(),
                    'chapter_name': manga.css('a.chaptersrec::text').extract_first()
                    # 'chapter_link': base_url + manga.css('a.chaptersrec::attr(href)').extract_first()
                }


if __name__ == "__main__":
    process = CrawlerProcess({
        'USER_AGENT': "Mozilla/5.0 (X11; Linux x86_64; rv:7.0.1) Gecko/20100101 Firefox/7.7",
        'FEED_FORMAT': 'json',
        'FEED_URI': 'mangaNotif/result.json'
    })

    process.crawl(MangaSpider)
    process.start()
