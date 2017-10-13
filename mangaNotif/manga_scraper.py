import scrapy
from scrapy.crawler import CrawlerProcess


class MangaSpider(scrapy.Spider):
    name = "updates"
    start_urls = [
        'http://mangafox.me/',
    ]

    def parse(self, response):
        for manga in response.css('ul#updates li div'):
            update_time = manga.css('h3 em::text').extract_first().split()
            if len(update_time) == 3 and (
                            update_time[1] == 'minutes' or (update_time[1] == 'hours' and int(update_time[0]) <= 1)):
                yield {
                    'name': manga.css('h3.title a.series_preview::text').extract_first(),
                    'link_manga': manga.css('h3.title a.series_preview::attr(href)').extract_first(),
                    'chapter_name': manga.css('span.chapter a.chapter::text').extract_first(),
                    'chapter_link': manga.css('span.chapter a.chapter::attr(href)').extract_first(),
                }


if __name__ == "__main__":
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'FEED_FORMAT': 'json',
        'FEED_URI': 'mangaNotif/result.json'
    })

    process.crawl(MangaSpider)
    process.start()
