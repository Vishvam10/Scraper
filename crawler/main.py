import time

from collections import deque

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def sc_all_button_click() :
    script = """
    let buttons = Array.from(document.querySelectorAll(".puppeteer_test_read_more_button"));
    let c = 0;
    buttons.forEach((ele) => {
        if(ele.innerText == "Continue Reading") {
            c += 1;
            ele.click()
        }
    })
    return c;

    """

    return script

class Scraper:

    def __init__(self, options) -> None:
        self.options = options
        self.driver = webdriver.Chrome(options=self.options)
        self.debug_level = 0

        self.visited_links = set()

    def scroll_down(self, counter=4) :
        c = 0

        while(c < counter) :
            height = self.driver.execute_script("return document.documentElement.scrollHeight")
            print("scroll : ", height)
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            c += 1

    def link_filter(self, url) :
        if("www.quora.com" in url and 
        "/profile" not in url and 
        "/about" not in url and 
        "/careers" not in url and 
        "/contact" not in url and 
        "/press" not in url and 
        "/answer" not in url and 
        "/unanswered" not in url and 
        "university" in url.lower() and
        (
            "niit-university" in url.lower() or
            "niit" in url.lower() or
            "NU" in url
        )
        ) :
            return True
        
        return False

    def get_all_links(self) :

        tags = self.driver.find_elements(By.TAG_NAME, "a")
        links = [tag.get_attribute("href") for tag in tags]
        links = [link for link in links if self.link_filter(link)]
        
        return links

    def scrape(self, url) :

        self.driver.get(url)
        self.scroll_down()

        links = self.get_all_links()
        print(len(links))

        return links

    def crawl(self, url, depth=1, max_depth=2):
        queue = deque([(url, 1)])  # Initialize the queue with the starting URL and depth 1
        while queue:
            current_url, depth = queue.popleft()  # Get the next URL and depth from the queue
            print("Depth:", depth, "URL:", current_url)

            if depth > max_depth:
                return

            links = self.scrape(current_url)

            for link in links:
                if link not in self.visited_links:
                    self.visited_links.add(link)
                    queue.append((link, depth + 1))


    def finish(self) :
        self.driver.close() 
        self.driver.quit() 


def write_to_file(content, filename="output.txt", mode="w") :
    fname = "{}".format(filename)
    file = open(fname, mode)
    file.write(content)
    file.close()


if __name__ == "__main__" :

    seed_url = "https://www.quora.com/What-is-NIIT-University-like"
    DRIVER_OPTIONS = Options()
    DRIVER_OPTIONS.add_argument("log-level=3")
    DRIVER_OPTIONS.add_argument("--incognito")
    DRIVER_OPTIONS.add_argument("--no-sandbox")
    DRIVER_OPTIONS.add_argument("--disable-dev-shm-usage")
    DRIVER_OPTIONS.add_argument("--headless")
    DRIVER_OPTIONS.add_argument("start-maximized");
    DRIVER_OPTIONS.add_experimental_option("detach", True)

    scr = Scraper(DRIVER_OPTIONS)
    scr.crawl(url=seed_url, max_depth=4)
    scr.finish()

    crawled_links = list(scr.visited_links)

    print("************** NO. OF CRAWLED LINKS ************** : ", len(crawled_links))

    for (i, val) in enumerate(scr.visited_links) :
        print(i, " : ", val)

    content = "\n".join(crawled_links)
    write_to_file(content, "quora_crawled_links_1.txt")
