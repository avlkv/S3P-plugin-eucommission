"""
Нагрузка плагина SPP

1/2 документ плагина
"""
import logging
import time
import dateparser
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from src.spp.types import SPP_document
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class EUCOMMISSION:
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.


    """

    SOURCE_NAME = 'eucommission'

    HOST = "https://ec.europa.eu/commission/presscorner/home/en"
    _content_document: list[SPP_document]



    def __init__(self, webdriver: WebDriver, policies: tuple | list, last_document: SPP_document = None, max_count_documents: int = 100,
                 *args, **kwargs):
        """
        Конструктор класса парсера

        По умолчанию внего ничего не передается, но если требуется (например: driver селениума), то нужно будет
        заполнить конфигурацию
        """
        # Обнуление списка
        self._content_document = []

        self.driver = webdriver
        self.wait = WebDriverWait(self.driver, timeout=20)
        self.max_count_documents = max_count_documents
        self.last_document = last_document
        self.POLICIES = policies

        # Логер должен подключаться так. Вся настройка лежит на платформе
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Parser class init completed")
        self.logger.info(f"Set source: {self.SOURCE_NAME}")
        ...

    def content(self) -> list[SPP_document]:
        """
        Главный метод парсера. Его будет вызывать платформа. Он вызывает метод _parse и возвращает список документов
        :return:
        :rtype:
        """
        self.logger.debug("Parse process start")
        try:
            self._parse()
        except Exception as e:
            self.logger.debug(f'Parsing stopped with error: {e}')
        else:
            self.logger.debug("Parse process finished")
        return self._content_document

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self.HOST}")

        self.driver.get(self.HOST)
        time.sleep(3)

        more_btn = self.driver.find_element(By.XPATH, '//*[contains(text(),\'More criteria\')]')
        self.driver.execute_script('arguments[0].click()', more_btn)

        time.sleep(0.5)

        policy_list = self.driver.find_element(By.XPATH,
                                               '//label[@for = \'filter-parea\']/..//div[@class = \'ecl-select__multiple\']')

        self.driver.execute_script("arguments[0].scrollIntoView();", policy_list)
        time.sleep(0.5)

        self.driver.execute_script('arguments[0].click()', policy_list)
        policy_list.click()

        policies = self.driver.find_elements(By.XPATH, '//div[@class = \'ecl-checkbox\']')

        for policy in policies:
            self.logger.debug(policy.text)
            if policy.text in self.POLICIES:
                policy.click()
        self.driver.execute_script("arguments[0].scrollIntoView();", policy_list)
        time.sleep(0.5)

        self.driver.execute_script('arguments[0].click()', policy_list)

        submit_btn = self.driver.find_element(By.XPATH, '//button[@type = \'submit\']')

        self.driver.execute_script("arguments[0].scrollIntoView();", submit_btn)
        time.sleep(0.5)

        submit_btn.click()

        while True:

            time.sleep(3)

            list_items = self.driver.find_elements(By.CLASS_NAME, 'ecl-list-item')

            for item in list_items:
                title = item.find_element(By.TAG_NAME, 'h3').text
                pub_date = dateparser.parse(item.find_elements(By.CLASS_NAME, 'ecl-meta__item')[1].text)
                doc_type = item.find_elements(By.CLASS_NAME, 'ecl-meta__item')[0].text
                web_link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                try:
                    abstract = item.find_element(By.TAG_NAME, 'p').text
                except:
                    abstract = None

                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[1])

                self._initial_access_source(web_link, 3)
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'ecl-container')))

                self.logger.debug(f'Enter {web_link}')

                try:
                    text_content = self.driver.find_element(By.CLASS_NAME, 'ecl-paragraph-detail').text
                except:
                    self.logger.debug('No Text, skipping')
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    continue
                other_data = {'doc_type': doc_type}

                doc = SPP_document(
                    doc_id=None,
                    title=title,
                    abstract=abstract,
                    text=text_content,
                    web_link=web_link,
                    local_link=None,
                    other_data=other_data,
                    pub_date=pub_date,
                    load_date=datetime.now(),
                )

                self.find_document(doc)

                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

            try:
                next_pg = self.driver.find_element(By.XPATH, '//a[@title = \'Go to next page\']')
                self.driver.execute_script("arguments[0].scrollIntoView();", next_pg)
                time.sleep(0.5)

                next_pg.click()
            except:
                self.logger.debug('No Next page')
                break

        # ---
        # ========================================
        ...

    def _initial_access_source(self, url: str, delay: int = 2):
        self.driver.get(url)
        self.logger.debug('Entered on web page ' + url)
        time.sleep(delay)

    def _find_document_text_for_logger(self, doc: SPP_document):
        """
        Единый для всех парсеров метод, который подготовит на основе SPP_document строку для логера
        :param doc: Документ, полученный парсером во время своей работы
        :type doc:
        :return: Строка для логера на основе документа
        :rtype:
        """
        return f"Find document | name: {doc.title} | link to web: {doc.web_link} | publication date: {doc.pub_date}"

    def find_document(self, _doc: SPP_document):
        """
        Метод для обработки найденного документа источника
        """
        if self.last_document and self.last_document.hash == _doc.hash:
            raise Exception(f"Find already existing document ({self.last_document})")

        if self.max_count_documents and len(self._content_document) >= self.max_count_documents:
            raise Exception(f"Max count articles reached ({self.max_count_documents})")

        self._content_document.append(_doc)
        self.logger.info(self._find_document_text_for_logger(_doc))
