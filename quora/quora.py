import re
import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from bs4 import BeautifulSoup

PATTERNS = {
    # Parse the author, date, answer, etc from here itself
    # document.querySelectorAll([class*="dom_annotate_question_answer_item"])
    "qa_card_box" : "dom_annotate_question_answer_item",

    # Generic patterns
    "qa_card_author" : "puppeteer_test_link",
    "qa_card_author_description" : "",


    # Someother questions (Related, Promoted, etc) 
    "qa_card_question" : "puppeteer_test_question_title",

    "qa_card_answer" : "puppeteer_test_answer_content",
    "qa_card_answer_timestamp" : "answer_timestamp",

    "read_more_button" : "puppeteer_test_read_more_button",

    # Related questions
    # document.querySelectorAll([class*="dom_annotate_related_questions"])
    "related_questions" : "dom_annotate_related_questions"
}

SAMPLE_URL = "https://www.quora.com/How-good-is-NIIT-Neemrana-for-CSE"

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

def extract_name_from_profile_url(url) :

    # Sample : https://www.quora.com/profile/username

    if(len(url) == 0) :
        return
    
    return " ".join(url.split("/profile/")[1].replace("-", " ").split(" ")[:-1]).strip()


if __name__ == "__main__" :

    options = Options()
    options.add_argument("log-level=3")
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    driver.get(SAMPLE_URL)

    c = 0

    while(c < 5) :
        height = driver.execute_script("return document.documentElement.scrollHeight")
        print("scroll : ", height)
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        c += 1

    num_removed_scripts = driver.execute_script(remove_unwanted_scripts())
    print("scripts removed : ", num_removed_scripts)
    time.sleep(1)

    num_removed_tags = driver.execute_script(remove_unwanted_html_tags())
    print("tags removed : ", num_removed_tags)
    time.sleep(1)


    read_more_buttons = driver.find_elements(By.CLASS_NAME, PATTERNS["read_more_button"])
    print("read more buttons : ", len(read_more_buttons), type(read_more_buttons[0]))

    # for btn in read_more_buttons :
    #     btn.click()

    cards = driver.find_elements(By.XPATH, "//*[contains(@class, 'dom_annotate_question_answer_item')]")

    print("number of qa cards : ", len(cards))

    data = []
    related_or_promoted_questions = []

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
                    "author_name" : author_name,
                    "answer_timestamp" : answer_timestamp,
                    "answer" : answer,
                }

                data.append(temp)

            else :

                # Could be Related or Promoted questions
                related_or_promoted_questions.append(url)


    df = pd.DataFrame(data)
    df.to_csv("quora.csv")

    for link in related_or_promoted_questions :
        print("other link : ", link)

    time.sleep(4)

    driver.quit()





