from datetime import datetime
import re
import locale
import time

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import selenium
from selenium import webdriver
import undetected_chromedriver as uc
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait

# if it does not work, see answers here (last comment) -
# https://ru.stackoverflow.com/questions/623775/Форматирование-даты-прописью-на-русском-языке
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')  # setting russian language to format dates

def get_page(driver, url):
    driver.get(url)
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def gis_parser(company_name, city, driver, date_format):
    s = requests.Session()
    s.headers.update(
        {
            "User-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15"
        }
    )

    # getting page with search results
    url = f"https://2gis.ru/{city}/search/{company_name}"
    request = s.get(url)

    # getting link to the first place in search result
    soup = BeautifulSoup(request.text, 'html.parser')
    # places = soup.find_all("div", {"class": "_zjunba"})
    place = soup.find(
        "div",
        string = lambda text: text and re.compile(company_name).search(text.lower())
    )
    link = place.parent.parent.parent.find('a').get('href')
    company_id = re.search('\\d+', link).group(0)

    # getting page with reviews
    url = f"https://2gis.ru/{city}/firm/{company_id}/tab/reviews"
    get_page(driver, url)

    # Viewing all reviews
    try:
        while True:
            button_view_more = driver.find_element(By.XPATH, "//button[contains(text(), 'Загрузить ')]")
            driver.execute_script("arguments[0].click()", button_view_more)
            time.sleep(1)
    except selenium.common.exceptions.NoSuchElementException:
        pass

    # getting cell with all reviews
    time.sleep(1)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    reviews_cell = soup.find_all("div", string=re.compile(r"(\d+\s[a-яА-Я]+\s20\d+)|(сегодня)"))
    reviews_cell = reviews_cell[0].parent.parent.parent.parent.parent.parent

    # getting title of review class
    temp = reviews_cell.find_all("div", recursive=False)
    temp = list(map(lambda item: item.get("class"), temp))
    for i, tmp in enumerate(temp):
        if tmp is not None:
            temp[i] = tmp[0]
    review_class = max(set(temp), key=temp.count)

    # getting reviews
    reviews = soup.find_all("div", {"class": review_class})

    # getting reviews data
    reviews_data = []
    for i, review in enumerate(reviews):
        # getting date
        date = review.find("div", string=re.compile(r"(\d+\s[a-яА-Я]+\s20\d+)|(сегодня)")).string  # getting date
        # formatting date
        if "сегодня" in date:
            date = datetime.today().strftime(date_format)
        else:
            date = re.search(r'\d+\s[а-яА-Я]+\s20\d+', date).group(0)
            date = datetime.strptime(date, '%d %B %Y').strftime(date_format)
        cells = review.find_all(["div", "span"])

        # getting name and review's description
        counter = 0
        for c in cells:
            if c.string is None:
                continue
            if counter == 0 and len(c.string) == 2:
                continue
            counter += 1
            if counter == 1:
                name = c.string
            elif counter == 4:
                description = c.string

        # getting review's rating
        rating = len(review.find_all("span", {"fill" : "#ffb81c"}))

        reviews_data.append(
            {
                "source": "2gis",
                "date": date,
                "name": name,
                "rating": rating,
                "description": description
            }
        )

    return reviews_data

def yandex_parser(company_name, city, driver, date_format):
    # getting page with search results
    url = f"https://yandex.ru/maps/213/{city}/search/{company_name}"
    get_page(driver, url)
    html = driver.page_source

    # getting link to the first place in search result
    soup = BeautifulSoup(html, 'html.parser')
    link = soup.find("a", {"class": "link-overlay"}).get('href')
    company_id = re.search('\\d+', link).group(0)
    url = f"https://yandex.ru/maps/org/{company_id}/reviews"

    # getting page with reviews
    get_page(driver, url)

    # Viewing all reviews
    try:
        time.sleep(1)
        prev_last_item = None
        cur_last_item = driver.find_elements(By.CLASS_NAME, "business-reviews-card-view__review")[-1]
        while prev_last_item != cur_last_item:
            driver.execute_script("arguments[0].scrollIntoView();", cur_last_item)
            time.sleep(1)
            prev_last_item = cur_last_item
            cur_last_item = driver.find_elements(By.CLASS_NAME, "business-reviews-card-view__review")[-1]
    except selenium.common.exception.NoSuchElementException:
        pass

    # getting reviews
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    reviews = soup.find_all("div", {"class": "business-reviews-card-view__review"})

    # getting reviews data
    reviews_data = []
    cur_year = datetime.now().year
    for review in reviews:
        # getting date
        date = review.find("span", {"class": "business-review-view__date"}).text
        if len(date.split()) < 3:
            date += f" {cur_year}"
        # formatting date
        date = datetime.strptime(date, '%d %B %Y').strftime(date_format)

        # getting name
        name = review.find("span", attrs={"itemprop": "name"}).string

        # getting review's description
        description = review.find("div", {"class": "business-review-view__body"}).text

        # getting rating
        rating = review.find("div", {"class": "business-rating-badge-view__stars _spacing_normal"})
        if rating is None:  # some reviews do not have rating. Usually they are from company
            continue
        else:
            rating = rating.get('aria-label')[7]

        reviews_data.append(
            {
                "source": "yandex",
                "date": date,
                "name": name,
                "rating": rating,
                "description": description
            }
        )

    return reviews_data

def otzovik_parser(company_name, city, driver, date_format):
    # getting page with search results
    if "передовые платежные решения" in company_name:
        company_name = "петрол плюс"
    url = f"https://otzovik.com/?search_text={company_name}&x=0&y=0"
    get_page(driver, url)

    # getting link to the first place in search
    time.sleep(15)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    print(html)
    products_container = soup.find("div", {"class" : "product-list"})
    url = f"https://otzovik.com{products_container.find("a", {"class" : "product-name"}).get("href")}"

    # getting page with reviews
    page_id = 1
    reviews_data = []
    while True:
        time.sleep(15)
        get_page(driver, url + f"/{page_id}")
        driver.execute_script("window.scrollTo(0, 1000);")
        html = driver.page_source

        soup = BeautifulSoup(html, "html.parser")
        reviews = soup.find_all("div", {"itemprop" : "review"})
        print(reviews)
        if len(reviews) == 0:  # case the page does not exist
            break
        for review in reviews:
            # getting date
            date = review.find("div", {"class" : "review-postdate"}).text # find("span").string

            # getting name
            name = review.find("span", {"itemprop" : "name"}).text

            # getting description
            description = review.find("div", {"class" : "review-body-wrap"}).text

            # getting rating
            rating = review.find("div", {"class" : "rating-score tooltip-right"}).text #find("span").string

            reviews_data.append(
                {
                    "source": "otzovik",
                    "date": date,
                    "name": name,
                    "rating": rating,
                    "description": description
                }
            )

        page_id += 1

    return reviews_data

def yell_parser(company_name, city, driver, date_format):
    # getting page with search results
    url = f"https://www.yell.ru/{city}/top/?text={company_name}"
    get_page(driver, url)
    html = driver.page_source

    # getting link to the first place in search result
    soup = BeautifulSoup(html, "html.parser")
    url = (
        "https://www.yell.ru/"
        f"{soup.find("a", {"class" : "companies__item-title-text"}).get("href")}/reviews"
    )

    # getting page with reviews
    get_page(driver, url)

    # Viewing all reviews
    try:
        while True:
            cur_last_item = driver.find_elements(By.CLASS_NAME, "reviews__item")[-1]
            driver.execute_script("arguments[0].scrollIntoView();", cur_last_item)
            time.sleep(1)
            button_view_more = driver.find_element(By.CLASS_NAME, "button_theme_red-linear")
            driver.execute_script("arguments[0].click();", button_view_more)
    except selenium.common.exceptions.NoSuchElementException:
        pass


    # try:
    #     time.sleep(1)
    #     prev_last_item = None
    #     cur_last_item = driver.find_elements(By.CLASS_NAME, "business-reviews-card-view__review")[-1]
    #     while prev_last_item != cur_last_item:
    #         driver.execute_script("arguments[0].scrollIntoView();", cur_last_item)
    #         time.sleep(1)
    #         prev_last_item = cur_last_item
    #         cur_last_item = driver.find_elements(By.CLASS_NAME, "business-reviews-card-view__review")[-1]
    # except selenium.common.exception.NoSuchElementException:
    #     pass



    # getting reviews
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    reviews = soup.find_all("div", {"class" : "reviews__item"})

    # getting reviews data
    reviews_data = []
    for review in reviews:
        # getting date
        date = review.find("span", {"class" : "reviews__item-added"}).get("content")
        date = re.search(r'\d+-\d+-\d+', date).group(0)
        # formatting date
        date = datetime.strptime(date, '%Y-%m-%d').strftime(date_format)

        # getting name
        name = review.find("div", {"class" : "reviews__item-user-name"}).text

        # getting description
        description = review.find("div", {"itemprop" : "reviewBody"}).text

        # getting rating
        rating = review.find("span", {"class" : "rating__value"}).text.strip()

        reviews_data.append(
            {
                "source": "yell",
                "date": date,
                "name": name,
                "rating": rating,
                "description": description
            }
        )

    return reviews_data

def flamp_parser(company_name, city, driver, date_format):
    # getting page with reviews
    url = f"https://{city}.flamp.ru/search/{company_name}"
    get_page(driver, url)

    # Viewing all reviews
    reviews = set()
    try:
        while True:
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            new_reviews = soup.find_all("li", {"class": "js-ugc-list-item"})
            reviews = reviews.union(new_reviews)
            # button_view_more = driver.find_element(By.CLASS_NAME, "js-cat-elements-button--next")
            button_view_more = driver.find_element(By.XPATH, '//*[text()="Показать ещё отзывы"]')
            driver.execute_script("arguments[0].click();", button_view_more)
            cur_last_item = driver.find_elements(By.CLASS_NAME, "js-ugc-list-item")[-1]
            driver.execute_script("arguments[0].scrollIntoView();", cur_last_item)
            time.sleep(1)
    except selenium.common.exceptions.NoSuchElementException:
        pass


    # getting reviews
    # html = driver.page_source
    # soup = BeautifulSoup(html, "html.parser")
    # revs = soup.find_all("li", {"class": "js-ugc-list-item"})
    # reviews = revs

    # getting reviews data
    reviews_data = []
    for review in reviews:
        # getting date
        date = review.find("a", {"class" : "ugc-date"}).text.strip()
        # formatting date
        date = datetime.strptime(date, '%d %B %Y').strftime(date_format)

        # getting name
        name = review.find("cat-brand-name").get("name").strip()

        # getting description
        description_container = review.find(
            "div", {"class" : "t-text t-rich-text ugc-item__text ugc-item__text--full js-ugc-item-text-full"}
        ) # .text.strip()
        description = " ".join([
            item.text.strip() for item in description_container.find_all("p", {"class" : "t-rich-text__p"})]
        )

        # getting rating
        rating = review.find("li", {"class" : "review-estimation__item--checked"}).text.strip()

        reviews_data.append(
            {
                "source": "flamp",
                "date": date,
                "name": name,
                "rating": rating,
                "description": description
            }
        )


    # getting reviews
    # html = driver.page_source
    # soup = BeautifulSoup(html, "html.parser")
    # reviews = soup.find_all("li", {"class" : "js-ugc-list__item"})
    # print(html)
    # url = soup.find("a", {"class" : "card__link"}).get("href")
    # print(url)
    return reviews_data

def get_reviews(company_name, city, date_format, sources=("all",), save_data=False):
    """ Function for getting list of reviews from multiple sources
    """
    # creating Chromeoptions instance
    options = uc.ChromeOptions()
    # options.add_argument(
    #     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    # )
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--window_size=1920,1080')
    # todo: options for docker container
    # options.add_argument('--disable-gpu')
    # options.add_argument('--headless=new')

    # setting the driver path and requesting a page
    driver = uc.Chrome(options=options)

    # changing navigator.webdriver property to undefined to avoid bot detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        """
    })

    reviews_data = []

    parsers = {
        "2gis" : gis_parser,
        "yandex" : yandex_parser,
        "otzovik" : otzovik_parser,
        "yell" : yell_parser,
        "flamp" : flamp_parser
    }

    if "all" in sources:
        sources = list(parsers.keys())

    for source in sources:
        data_from_1_source = parsers[source](company_name.lower(), city.lower(), driver, date_format)
        reviews_data.extend(data_from_1_source)
        if save_data:
            pd.DataFrame(data_from_1_source).to_csv(f"{source}_reviews.csv")

    driver.quit()

    return reviews_data

if __name__ == "__main__":
    time_start = time.time()
    date_format = "%d-%m-%Y"
    city = "moscow"
    company_name = "передовые платежные решения"
    while True:
        try:
            data = get_reviews(company_name, city, date_format, (
                "2gis",
                "yandex",
                "yell",
                # "otzovik",
                "flamp",
            ), True)
            break
        except selenium.common.exceptions.NoSuchWindowException:
            pass

    data = pd.DataFrame(data)

    print(data)
    print(time.time() - time_start)

