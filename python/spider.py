import scrapy
import string

class GamesSpider(scrapy.Spider):
    file = open("test.txt","r")
    name = "Games"
    # start_urls = ["https://www.mobygames.com/browse/games/offset,0/so,0a/list-games/"]
    start_urls = file.read().splitlines()
    
    def parse(self, response):
        games = response.xpath("//div/table[@id=\"mof_object_list\"]/tbody/tr")
        for game in games:
            title = game.xpath(".//td[1]/a/text()").get()
            link = game.xpath(".//td[1]/a/@href").get()
            year = game.xpath(".//td[2]/a/text()").get()
            publisher = game.xpath(".//td[3]/a/text()").getall()
            genre = game.xpath(".//td[4]/a/text()").getall()
            platform = game.xpath(".//td[5]/a/text()").getall()
            yield response.follow(url=link, callback=self.parse_game, meta={'game_title': title,'game_link': link, 'game_year': year,'game_publisher': publisher,'game_genre': genre,'game_platform': platform})
        
    def parse_game(self,response):
        title = response.request.meta['game_title']
        link = response.request.meta['game_link']
        year = response.request.meta['game_year']
        publisher = response.request.meta['game_publisher']
        genre = response.request.meta['game_genre']
        platform = response.request.meta['game_platform']
        description = response.xpath(".//div[@class = \"col-md-8 col-lg-8\"]/text()").getall()
        yield{
            'game_title': title,
            'game_link': link,
            'game_year': year,
            'game_publisher': publisher,
            'game_genre': genre,
            'game_platform': platform,
            'game_description': "".join(description).replace("\n","")
        }
