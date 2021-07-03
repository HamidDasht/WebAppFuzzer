import requests, os
from urllib.parse import urlparse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import http.cookiejar
from http.cookiejar import LWPCookieJar
from requests_html import HTMLSession


#INPUT = "https://www.google.com"
INPUT = "http://127.0.0.1:8000/home/"
class crawler:
    def __init__(self, root_url, login_required=False, login_username=None, login_password=None, logout_url="\\\\") -> None:
        self.root_url = root_url
        self.logout_url = logout_url
        self.visited = set()
        self.visit_queue = set()
        self.visit_queue.add(root_url)
        self.target_domain = str()
        self.session = HTMLSession()

        # Parse the target url so we know what domain we are targeting
        target_url_parsed = urlparse(self.root_url)
        if (target_url_parsed.netloc[:4] == 'www.'):
            self.target_domain = target_url_parsed.netloc[4:]
        else:
            self.target_domain = target_url_parsed.netloc
        print(self.target_domain)

        # Login if the web app requires login
        if login_required:
            self.__login(login_username, login_password)

    def __login(self, username, password, email=""):
        #self.session = requests.Session()
        self.session.get(self.root_url)
        if 'csrftoken' in self.session.cookies:
            csrftoken = self.session.cookies['csrftoken']
        elif 'csrf':
            csrftoken = self.session.cookies['csrf']
        login_data = dict(username=username, password=password, csrfmiddlewaretoken=csrftoken)
        r = self.session.post(self.root_url, data=login_data, headers=dict(Referer=self.root_url))
        print(self.session.cookies.get_dict())


    def handler(self):
        while len(self.visit_queue) > 0:
            url_to_visit = self.visit_queue.pop()
            self.__engine(url_to_visit)
            self.visited.add(url_to_visit)


    def __engine(self, cur_url):
        # Do not visit logout url
        if self.logout_url in cur_url:
            return
        print("visitng url {}".format(cur_url))
        """
        Result contains html in res.content among other 
        things like status code (res.status_code), etc. """
        try:
            res = self.session.get(cur_url, allow_redirects=True)
            self.visited.add(cur_url)
        except:
            print("bad url: " + cur_url)
            return
        #Save the content as soup object.
        soup = BeautifulSoup(res.content, 'lxml')
        """
        We can look for specific objects and tags and 
        elements in the requested page code for example:
            - links = soup.find_all("a")
            - videos = soup.find_all("div", {"class":"thumb-title"}) """
        urls = set(soup.find_all("a", href=True))
        urls.union(set(soup.find_all("link", href=True)))

        for url in urls:
            #print(url['href'])
            new_url = url['href']
            new_url_domain = urlparse(new_url).netloc
            new_url_scheme = urlparse(new_url).scheme
            new_url = urljoin(cur_url, new_url)

            """ 
            If the url is relevant to our target domain add it to the queue
            Also if the url is a relative url starting with /, #, etc 
            add it to the queue """
            #print("new url {}".format(new_url))
            if new_url in self.visited:
                continue

            if self.target_domain in new_url_domain:
                self.visit_queue.add(new_url)
            elif not new_url_scheme:
                self.visit_queue.add(new_url)
            else:
                continue

        #visit_queue = list(urls)
        #print(len(self.visit_queue))
        #print(res.status_code)
    


def __main__():
    a = crawler(INPUT,True,"hamid","12345","logout")
    a.handler()

__main__()