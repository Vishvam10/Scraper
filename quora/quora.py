# import os
# import sys
# import json
# import argparse
# import random
# from datetime import datetime, timedelta

# import urllib.request
# from bs4 import BeautifulSoup

PATTERNS = {
    # Parse the author, date, answer, etc from here itself
    "qa_card_box" : "q-box qu-hover--bg--darken",

    # Generic patterns
    "qa_card_author" : "puppeteer_test_link",
    "qa_card_author_description" : "q-text qu-dynamicFontSize--small qu-color--gray qu-passColorToLinks qu-truncateLines--3",


    # Someother questions (Related, Promoted, etc) 
    "qa_card_question" : "puppeteer_test_question_title",

    "qa_card_answer" : "q-click-wrapper qu-display--block qu-tapHighlight",
    "qa_card_answer_timestamp" : "answer_timestamp",

    # The main question
    "main_question_title" : "q-text puppeteer_test_question_title",

    "read_more_button" : "puppeteer_test_read_more_button",
}

SAMPLE_URL = "https://www.quora.com/How-good-is-NIIT-Neemrana-for-CSE"











