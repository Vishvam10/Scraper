import os
import re
import time
import random
# import pickle

from datetime import datetime

import pandas as pd

from joblib import Parallel, delayed

# from functools import lru_cache
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# from bs4 import BeautifulSoup
from googlesearch import search, get_random_user_agent

COUNT = 1
DRIVER_OPTIONS = Options()

PATTERNS = {
    # Parse the author, date, answer, etc from here itself
    # document.querySelectorAll([class*="dom_annotate_question_answer_item"])
    "qa_card_box" : "dom_annotate_question_answer_item",

    # Generic patterns
    "qa_card_author_description" : "",
    "all_links" : "puppeteer_test_link",


    # Someother questions (Related, Promoted, etc) 
    "qa_card_question" : "puppeteer_test_question_title",

    "qa_card_answer" : "puppeteer_test_answer_content",
    "qa_card_answer_timestamp" : "answer_timestamp",

    "read_more_button" : "puppeteer_test_read_more_button",
    "login_card" : "q-box qu-p--large qu-pt--huge qu-bg--gray_ultralight qu-borderRadius--medium qu-boxShadow--small"

}

SEARCH_QUERY = "niit university quora"

class COLOR:
    DEFAULT = '\033[0m'

    BOLD = '\033[1m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    UNDERLINE_THICK = '\033[21m'
    HIGHLIGHTED = '\033[7m'
    HIGHLIGHTED_BLACK = '\033[40m'
    HIGHLIGHTED_RED = '\033[41m'
    HIGHLIGHTED_GREEN = '\033[42m'
    HIGHLIGHTED_YELLOW = '\033[43m'
    HIGHLIGHTED_BLUE = '\033[44m'
    HIGHLIGHTED_PURPLE = '\033[45m'
    HIGHLIGHTED_CYAN = '\033[46m'
    HIGHLIGHTED_GREY = '\033[47m'

    HIGHLIGHTED_GREY_LIGHT = '\033[100m'
    HIGHLIGHTED_RED_LIGHT = '\033[101m'
    HIGHLIGHTED_GREEN_LIGHT = '\033[102m'
    HIGHLIGHTED_YELLOW_LIGHT = '\033[103m'
    HIGHLIGHTED_BLUE_LIGHT = '\033[104m'
    HIGHLIGHTED_PURPLE_LIGHT = '\033[105m'
    HIGHLIGHTED_CYAN_LIGHT = '\033[106m'
    HIGHLIGHTED_WHITE_LIGHT = '\033[107m'

    STRIKE_THROUGH = '\033[9m'
    MARGIN_1 = '\033[51m'
    MARGIN_2 = '\033[52m' 
    
    # colors
    BLACK = '\033[30m'
    RED_DARK = '\033[31m'
    GREEN_DARK = '\033[32m'
    YELLOW_DARK = '\033[33m'
    BLUE_DARK = '\033[34m'
    PURPLE_DARK = '\033[35m'
    CYAN_DARK = '\033[36m'
    GREY_DARK = '\033[37m'

    BLACK_LIGHT = '\033[90m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[96m'

    ENDC = '\033[0m'

def bold(msg) :
    return "{}{}{}".format(COLOR.BOLD, msg, COLOR.ENDC)

def underline(msg) :
    return "{}{}{}".format(COLOR.UNDERLINE, msg, COLOR.ENDC)

def green(msg) :
    return "{}{}{}".format(COLOR.GREEN, msg, COLOR.ENDC)

def blue(msg) :
    return "{}{}{}".format(COLOR.BLUE, msg, COLOR.ENDC)

def cyan(msg) :
    return "{}{}{}".format(COLOR.CYAN, msg, COLOR.ENDC)

def red(msg) :
    return "{}{}{}".format(COLOR.RED, msg, COLOR.ENDC)

def yellow(msg) :
    return "{}{}{}".format(COLOR.YELLOW, msg, COLOR.ENDC)

def purple(msg) :
    return "{}{}{}".format(COLOR.PURPLE, msg, COLOR.ENDC)

def now() :
    now = datetime.now()
    timestamp = now.strftime("%d/%m/%Y %H:%M:%S")
    timestamp = timestamp.replace("/", "-").replace("\\", "-").replace(" ", "_").replace(":", "-")
    return timestamp

def write_to_file(content, filename="output.txt", mode="w") :
    fname = "{}".format(filename)
    file = open(fname, mode)
    file.write(content)
    file.close()

def get_google_results(keyword, num=50, stop=50, pause=2) :
    results = []

    # search() is a generator. So, it had yield instead of return.
    for res in search(query=keyword, user_agent=get_random_user_agent(), num=num, stop=stop, pause=pause) :
        results.append(res)

    return results

def file_exists(file_path) :
    return os.path.isfile(file_path)

def remove_unwanted_scripts() :
    script = """
        // Remove all script tags
        let scripts = document.getElementsByTagName("script");
        let c = 0
        for (let i = scripts.length - 1; i >= 0; i--) {
            scripts[i].parentNode.removeChild(scripts[i]);
            c += 1
        } 
        return c
        
    """

    return script

def remove_unwanted_html_tags() :

    script = """
        // Remove selected HTML tags
        let unwantedTags = ['iframe', 'object', 'embed', 'img', 'canvas', 'noscript'];
        let c = 0;
        for (let i = 0; i < unwantedTags.length; i++) {
            let tags = document.getElementsByTagName(unwantedTags[i]);
            for (let j = tags.length - 1; j >= 0; j--) {
                tags[j].parentNode.removeChild(tags[j]);
                c += 1;
            }
        }
        return c
    """

    return script

def click_buttons() :

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

def extract_name_from_profile_url(url) :

    # Sample : https://www.quora.com/profile/username

    if(len(url) == 0) :
        return
    
    return " ".join(url.split("/profile/")[1].replace("-", " ").split(" ")[:-1]).strip()

def extract_question_from_url(url) :
    if(len(url) == 0 or "quora.com" not in url) :
        return
    
    return url.split("quora.com/")[1].lower().replace("-", " ").capitalize() 

def filter_results(urls, patterns) :
    results = []
    for pattern in patterns :
        results = [url for url in urls if re.match(pattern, url)]
    
    return results


def scrape(url, index, debug=True) :

    global DRIVER_OPTIONS
    scraped_data = []

    driver = webdriver.Chrome(options=DRIVER_OPTIONS)

    if("www.quora.com" in url and 
        "/profile" not in url and 
        "/about" not in url and 
        "/careers" not in url and 
        "/contact" not in url and 
        "/press" not in url and 
        "/unanswered" not in url and 
        (
            "niit" in url.lower() or
            "nu" in url
        )
    ) : 
    
        # We want multiple answers for the same question
        if("/answers/" in url) :
            url = url.split("/answers")[0]

        driver.get(url)

        question = extract_question_from_url(url)

        print(bold(green("\n------------------------- Scraping -------------------------\n")))
        print(bold(green("Index : {} : {} : \n{}".format(index, url, question))))
        print(bold(green("--------------------------------------------------------------\n")))

        c = 0

        # Scroll down
        while(c < 10) :
            height = driver.execute_script("return document.documentElement.scrollHeight")
            # if(debug) :
                # print("scroll : ", height)
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            c += 1

        num_read_more_buttons = driver.execute_script(click_buttons())
        
        if(debug) :
            msg = "Index : {} --- read more buttons clicked : {}".format(index, num_read_more_buttons)
            print(msg)

        time.sleep(2)

        # Scroll down again 
        while(c < 10) :
            # height = driver.execute_script("return document.documentElement.scrollHeight")
            # if(debug) :
                # print("scroll : ", height)
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            c += 1


        num_removed_scripts = driver.execute_script(remove_unwanted_scripts())
        if(debug) :
            msg = "Index : {} --- scripts removed : {}".format(index, num_removed_scripts)
            print(msg)

        time.sleep(1)

        num_removed_tags = driver.execute_script(remove_unwanted_html_tags())
        if(debug) :
            msg = "Index : {} --- tags removed : {}".format(index, num_removed_tags)
            print(msg)

        time.sleep(1)

        cards = driver.find_elements(By.XPATH, "//*[contains(@class, 'dom_annotate_question_answer_item')]")

        if(debug) :
            msg = "Index : {} --- number of QA cards : {}".format(index, len(cards))
            print(msg)

        if(len(cards) == 0) :
            msg = red("Index : {} --- No QA cards found. Exiting ...".format(index))
            print(msg)
            
            driver.close()
            driver.quit()
            return []

        n_answers = 0

        for card in cards :

            links = card.find_elements(By.TAG_NAME, "a")
            if(len(links) > 1) :
                url = str(links[1].get_attribute("href"))
                
                if("profile" in url) :

                    author_profile_url = url
                    author_name = extract_name_from_profile_url(author_profile_url)
                    # author_description = card.find_elements(By.XPATH, "//span[contains(@class, 'CssComponent')]")[1].get_attribute("innerText")

                    answer_timestamp = str(links[2].get_attribute("innerText"))
                    answer_timestamp_pattern = r"(\d+mo|\d+y)"

                    for temp in links :
                        link = temp.get_attribute("innerText").strip()
                        if(len(link) > 0) :
                            check = re.search(answer_timestamp_pattern, link)
                            if(check is not None) :
                                answer_timestamp = check.group() 
                                break
                                        
                    
                    answer = card.find_element(By.CLASS_NAME, PATTERNS["qa_card_answer"]).get_attribute("textContent")

                    temp = {
                        "question" : question,
                        "author_name" : author_name,
                        "answer_timestamp" : answer_timestamp,
                        "answer" : answer,
                    }
                    n_answers += 1
                    scraped_data.append(temp)

        msg = "Index : {} --- Number of answers added : {}".format(index, n_answers)
        print(bold(cyan(msg)))

        driver.close();
        driver.quit();

        return scraped_data
    
    else :
        driver.close()
        driver.quit()
        return []


def distributed_scrape(arr, top_k=5, max_workers=3) :

    data = []
    
    # Create a ThreadPoolExecutor with a maximum of 3 workers
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        
        # submit() takes : fn, fn_arg1, fn_arg2, ... as parameters
        jobs = [executor.submit(scrape, url, i) for (i, url) in enumerate(arr[:top_k])]
        c = 1

        for job in futures.as_completed(jobs):
            res = job.result()
            if(len(res) > 0) :
                for link in res :                    
                    data.append(link)
                
            msg = "\nIteration : {} --- Total number of answers : {}".format(c, len(data))
            print(bold(cyan(msg)))

            c += 1
    
    return data


if __name__ == "__main__" :

    SEARCH_QUERY = input("Enter the search query : ").strip()
    SEARCH_QUERY += " quora"
    SEED_LIMIT = int(input("Enter the seed limit : ").strip())
    BRANCHING_FACTOR = int(input("Enter the branching factor : ").strip())
    
    print(bold(blue("\n------------------------- Scraping -------------------------\n")))
    print(bold(blue("Search Query : {}".format(SEARCH_QUERY))))
    print(bold(blue("Seed limit : {}".format(SEED_LIMIT))))
    print(bold(blue("Branching factor : {}".format(BRANCHING_FACTOR))))
    print(bold(blue("--------------------------------------------------------------\n")))

    p_start = time.time()

    DRIVER_OPTIONS.add_argument("log-level=3")
    DRIVER_OPTIONS.add_argument("--incognito")
    DRIVER_OPTIONS.add_argument("--no-sandbox")
    DRIVER_OPTIONS.add_argument("--disable-dev-shm-usage")
    DRIVER_OPTIONS.add_argument("--headless")
    DRIVER_OPTIONS.add_argument("start-maximized");
    DRIVER_OPTIONS.add_experimental_option("detach", True)


    GOOGLE_SEARCH_CACHE_FILEPATH = "./quora_cache/google_search_cache.txt"  
    QUORA_CRAWLED_LINKS_CACHE_FILEPATH = "./quora_cache/quora_crawled_links.txt"
    GOOGLE_SEARCH_URL_PATTERN = r"\bhttps:\/\/www.quora.com\b/"


    URL_FILTER_CHAIN = [
        GOOGLE_SEARCH_URL_PATTERN,
        # Can add multiple filters here
    ] 
    CRAWLABLE_LINKS = []
    
    if(not file_exists(QUORA_CRAWLED_LINKS_CACHE_FILEPATH)) :

        if(file_exists(GOOGLE_SEARCH_CACHE_FILEPATH)) :
            f = open(GOOGLE_SEARCH_CACHE_FILEPATH, "r")
            CRAWLABLE_LINKS = f.readlines()
            f.close()

            CRAWLABLE_LINKS = filter_results(CRAWLABLE_LINKS, URL_FILTER_CHAIN)
            
            msg = "\nUsing google search cache \nNo. of CRAWLABLE_LINKS : {}\n".format(len(CRAWLABLE_LINKS))
            print(bold(purple(msg)))

        else :
            msg = "\nUsing google search API \nFetching the first 50 search CRAWLABLE_LINKS\n"
            print(bold(purple(msg)))

            try :

                # Fetch first 50 google search CRAWLABLE_LINKS
                start = time.time()
                CRAWLABLE_LINKS = get_google_results(SEARCH_QUERY)
                end = time.time()

            except Exception as e :

                if hasattr(e, "message"):
                    print(red(e.message))
                else:
                    print(red(e))

                exit(0)
            
            else :

                msg = "\nTime taken to fetch {} results : {}\n".format(len(CRAWLABLE_LINKS), end-start)
                print(bold(msg))

                content = "\n".join(CRAWLABLE_LINKS)
                write_to_file(content, GOOGLE_SEARCH_CACHE_FILEPATH)

            CRAWLABLE_LINKS = list(set(CRAWLABLE_LINKS))

    else :
        
        f = open(QUORA_CRAWLED_LINKS_CACHE_FILEPATH, "r")
        content = f.read()
        f.close()
        
        CRAWLABLE_LINKS = content.split("\n")

    SEED_LIMIT = min(len(CRAWLABLE_LINKS), SEED_LIMIT)
    print(bold(blue("\nNumber of links : {}".format(len(CRAWLABLE_LINKS[:SEED_LIMIT])))))

    data = distributed_scrape(CRAWLABLE_LINKS[:SEED_LIMIT], BRANCHING_FACTOR, 9)
    
    # data = []
    # for (i, link) in enumerate(CRAWLABLE_LINKS) :
    #     data.append(scrape(link, i))

    filename = "{}_{}".format("quora_data", now())
    csv_filename = filename + ".csv"

    msg = "\nWriting to CSV ... "
    print(bold(purple(msg)))

    df = pd.DataFrame(data)
    df.to_csv(csv_filename)

    p_end = time.time()

    msg = "\n\nProcess finished. Total time taken : {}\n\n".format(p_end - p_start)
    print(bold(green(msg)))

    exit(0)



