"""
Парсер плагина SPP

1/2 документ плагина
"""
import logging
import os
import time
from datetime import datetime

from selenium.webdriver.common.by import By

from src.spp.types import SPP_document


class W3C:
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.


    """

    SOURCE_NAME = 'w3c'
    _content_document: list[SPP_document]
    HOST = 'https://www.w3.org/TR/'

    def __init__(self, driver, *args, **kwargs):
        """
        Конструктор класса парсера

        По умолчанию внего ничего не передается, но если требуется (например: driver селениума), то нужно будет
        заполнить конфигурацию
        """
        # Обнуление списка
        self._content_document = []

        # Установка selenium driver
        self.driver = driver

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
        self._parse()
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

        # ========================================
        # Тут должен находится блок кода, отвечающий за парсинг конкретного источника
        # -
        self.driver.get('https://www.w3.org/TR/')
        doc_list = self.driver.find_elements(By.CLASS_NAME, 'tr-list__item__header')
        for doc in doc_list:

            # Ссылка на документ
            __doc_link = doc.find_element(By.TAG_NAME, 'a').get_attribute('href')

            try:
                __title = doc.find_element(By.TAG_NAME, 'a').text
            except:
                # завершение обработки документа, переход к следующему
                self.logger.exception(f'Ошибка при обработке документа {__doc_link}')
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                continue


            # pub_date
            __pub_date = datetime.strptime(doc.find_element(By.XPATH, '..//time').get_attribute('datetime'), '%Y-%m-%d')

            # tags
            tags_el = doc.find_elements(By.XPATH, '..//*[contains(text(), \'Tags\')]/../dd')
            __tags = [x.text for x in tags_el]

            # deliverers (workgroup)
            deliverers_el = doc.find_elements(By.XPATH, '..//*[contains(text(), \'Deliverers\')]/../dd')
            __devilverers = [x.text for x in deliverers_el]

            # family
            __family = doc.find_element(By.XPATH, '../../h2').text

            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.get(__doc_link)
            time.sleep(0.5)

            # abstract
            try:
                __abstract = self.driver.find_element(By.ID, 'abstract').text
            except:
                # Удален np.nan
                __abstract = None

            # text_content
            __text_content = self.driver.find_element(By.TAG_NAME, 'body').text

            # web_link
            try:
                __web_link = self.driver.find_element(By.XPATH,
                                                    '//dt[contains(text(), \'This version\')]/following-sibling::dd[1]//a').get_attribute(
                    'href')
            except:
                self.logger.exception(
                    f'Не удалось получить веб-ссылку на версию документа за определенную дату. В web_link вносится общая ссылка {__doc_link}')
                __web_link = __doc_link

            # doc_type
            try:
                __doc_type = self.driver.find_element(By.XPATH, '//p[@id = \'w3c-state\']/a').text
            except:
                # удален np.nan
                __doc_type = None

            # authors
            authors_el = self.driver.find_elements(By.XPATH,
                                                   '//dt[contains(text(), \'Authors\')]/following-sibling::dd[@class=\'editor p-author h-card vcard\']')
            __authors = [x.text for x in authors_el]

            # authors
            editors_el = self.driver.find_elements(By.XPATH,
                                                   '//dt[contains(text(), \'Editors\')]/following-sibling::dd[@class=\'editor p-author h-card vcard\']')
            __editors = [x.text for x in editors_el]

            # commit
            commit_links = self.driver.find_elements(By.XPATH, '//a[contains(text(), \'Commit history\')]')
            if len(commit_links) > 0:
                self.driver.get(commit_links[0].get_attribute('href'))
                time.sleep(1)
                commit_el = self.driver.find_elements(By.XPATH,
                                                      '//div[@class=\'TimelineItem TimelineItem--condensed pt-0 pb-2\']//p[contains(@class,\'mb-1\')]')
                __commits = [x.text for x in commit_el]
            else:
                # удален np.nan
                __commits = None

            __spp_doc = SPP_document(
                doc_id=None,
                title=__title,
                abstract=__abstract,
                text=__text_content,
                web_link=__web_link,
                local_link=None,
                other_data={
                    'doc_type': __doc_type,
                    'devilverers': __devilverers,
                    'authors': __authors,
                    'tags': __tags,
                    'commits': __commits,
                    'family': __family,
                    'editors': __editors,
                },
                pub_date=__pub_date,
                load_date=None,
            )

            self._content_document.append(__spp_doc)

            self.logger.info(self._find_document_text_for_logger(__spp_doc))

            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

        # Логирование найденного документа
        # self.logger.info(self._find_document_text_for_logger(document))

        # ---
        # ========================================
        ...

    @staticmethod
    def _find_document_text_for_logger(doc: SPP_document):
        """
        Единый для всех парсеров метод, который подготовит на основе SPP_document строку для логера
        :param doc: Документ, полученный парсером во время своей работы
        :type doc:
        :return: Строка для логера на основе документа
        :rtype:
        """
        return f"Find document | name: {doc.title} | link to web: {doc.web_link} | publication date: {doc.pub_date}"

    @staticmethod
    def some_necessary_method():
        """
        Если для парсинга нужен какой-то метод, то его нужно писать в классе.

        Например: конвертация дат и времени, конвертация версий документов и т. д.
        :return:
        :rtype:
        """
        ...

    @staticmethod
    def nasty_download(driver, path: str, url: str) -> str:
        """
        Метод для "противных" источников. Для разных источника он может отличаться.
        Но основной его задачей является:
            доведение driver селениума до файла непосредственно.

            Например: пройти куки, ввод форм и т. п.

        Метод скачивает документ по пути, указанному в driver, и возвращает имя файла, который был сохранен
        :param driver: WebInstallDriver, должен быть с настроенным местом скачивания
        :_type driver: WebInstallDriver
        :param url:
        :_type url:
        :return:
        :rtype:
        """

        with driver:
            driver.set_page_load_timeout(40)
            driver.get(url=url)
            time.sleep(1)

            # ========================================
            # Тут должен находится блок кода, отвечающий за конкретный источник
            # -
            # ---
            # ========================================

            # Ожидание полной загрузки файла
            while not os.path.exists(path + '/' + url.split('/')[-1]):
                time.sleep(1)

            if os.path.isfile(path + '/' + url.split('/')[-1]):
                # filename
                return url.split('/')[-1]
            else:
                return ""
