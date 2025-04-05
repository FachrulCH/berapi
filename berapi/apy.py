import logging
import os
from urllib.parse import urljoin

import curlify
import requests

from berapi.responder import Responder
from berapi.utils import format_console

MAX_TIMEOUT = int(os.getenv("MAX_TIMEOUT", 3))
MAX_RESPONSE_TIME = int(os.getenv("MAX_RESPONSE_TIME", 5))

class berAPI(requests.Session):
    def __init__(self, base_url=None, base_headers=None, *args, **kwargs):
        super(berAPI, self).__init__(*args, **kwargs)
        self.timeout = MAX_TIMEOUT
        self.hooks["response"].append(self._logging)
        if base_url:
            self.base_url = base_url
        if base_headers:
            self.headers.update(base_headers)

    def url_handling(self, url):
        if url.startswith("http"):
            return url
        else:
            return urljoin(self.base_url, url)

    @staticmethod
    def _logging(response: requests.Response, *args, **kwargs):
        """Logging Request and response to log"""

        logging.warning("----------- Request ----------->")
        logging.info(format_console(response.request.method, response.request.url))
        logging.info(format_console("HEADERS", response.request.headers))
        logging.info(format_console("DEBUG", curlify.to_curl(response.request)))
        if response.request.body is not None:
            logging.info(format_console("BODY", response.request.body))

        logging.warning("<----------- Response -----------")
        logging.info(
            format_console(
                "STATUS",
                f"{response.status_code}, elapsed: {response.elapsed.total_seconds()}s",
            )
        )
        logging.info(format_console("HEADER", response.headers))
        if response.text != "":
            logging.info(format_console("BODY", response.text))
            # print(format_console("BODY", response.text))

    def request(self, method, url, *args, **kwargs):
        response = super(berAPI, self).request(method, url, *args, **kwargs)
        response_time = response.elapsed.total_seconds()
        if response_time > MAX_RESPONSE_TIME:
            raise requests.Timeout
        return response

    def get(self, url, *args, **kwargs) -> Responder:
        url = self.url_handling(url)
        return Responder(self.request("GET", url, *args, **kwargs))

    def post(self, url, *args, **kwargs):
        url = self.url_handling(url)
        return Responder(self.request("POST", url, *args, **kwargs))

    def put(self, url, *args, **kwargs):
        url = self.url_handling(url)
        return Responder(self.request("PUT", url, *args, **kwargs))

    def patch(self, url, *args, **kwargs):
        url = self.url_handling(url)
        return Responder(self.request("PATCH", url, *args, **kwargs))

    def delete(self, url, *args, **kwargs):
        url = self.url_handling(url)
        return Responder(self.request("DELETE", url, *args, **kwargs))