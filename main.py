from logging import config

from selenium import webdriver

from eucommission import EUCOMMISSION
from src.spp.types import SPP_document

config.fileConfig('dev.logger.conf')


def driver():
    """
    Selenium web driver
    """
    options = webdriver.ChromeOptions()

    # Параметр для того, чтобы браузер не открывался.
    options.add_argument('headless')

    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")

    return webdriver.Chrome(options)


def to_dict(doc: SPP_document) -> dict:
    return {
        'title': doc.title,
        'abstract': doc.abstract,
        'text': doc.text,
        'web_link': doc.web_link,
        'local_link': doc.local_link,
        'other_data': doc.other_data.get('category') if doc.other_data.get('category') else '',
        'pub_date': str(doc.pub_date.timestamp()) if doc.pub_date else '',
        'load_date': str(doc.load_date.timestamp()) if doc.load_date else '',
    }


policies = ["Banking and financial services",
            "Digital Economy and Society",
            "Economy, finance and the euro",
            "Fraud prevention"]
parser = EUCOMMISSION(driver(), max_count_documents=5, policies=policies)
docs: list[SPP_document] = parser.content()

print(*docs, sep='\n\r\n')
print(len(docs))
