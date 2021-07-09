import requests, os
from urllib.parse import urlparse
from urllib.parse import urljoin
from requests_html import HTMLSession
from bs4 import BeautifulSoup
from packages.xss_fuzzer import XSS_TEST


#INPUT = "https://www.google.com"
#INPUT = "http://127.0.0.1:8000/home/"
INPUT = "http://192.168.88.132/dvwa/index.php"
class crawler:
    def __init__(self, root_url, illegal_urls, has_csrf, csrf_token_name="", login_required=False, login_url="", login_data=None) -> None:
        self.root_url = root_url
        self.login_url = login_url
        self.illegal_urls = illegal_urls
        self.has_csrf = has_csrf
        self.csrf_token_name = csrf_token_name
        self.visited = set()
        self.visit_queue = set()
        self.visit_queue.add(root_url)
        self.target_domain = str()
        self.session = HTMLSession()

        self.xss_fuzzer = None

        # Parse the target url so we know what domain we are targeting
        target_url_parsed = urlparse(self.root_url)
        if (target_url_parsed.netloc[:4] == 'www.'):
            self.target_domain = target_url_parsed.netloc[4:]
        else:
            self.target_domain = target_url_parsed.netloc
        print(self.target_domain)

        # Login if the web app requires login
        if login_required:
            self.__login(login_data)

    def __login(self, login_data):
        resp = self.session.get(self.login_url)

        if self.has_csrf:
            soup = BeautifulSoup(resp.content, 'lxml')
            forms = soup.find_all('form')
            for form in forms:
                inputs = form.find_all('input')
                for input in inputs:
                    try:
                        input_name = str(input["name"])
                    except:
                        continue
                    if self.csrf_token_name in input_name:
                        form_csrf = input["value"]
                        csrftoken = form_csrf
                        break
            login_data[self.csrf_token_name] = csrftoken
        
        """
        if 'csrftoken' in self.session.cookies:
            csrftoken = self.session.cookies['csrftoken']
        elif 'csrf' in self.session.cookies:
            csrftoken = self.session.cookies['csrf']
        elif 'user_token' in self.session.cookies:
            csrftoken = self.session.cookies['user_token']
        if 'csrftoken' in self.session.cookies or 'csrf' in self.session.cookies:
            login_data = dict(username=username, password=password, csrfmiddlewaretoken=csrftoken)
        elif 'user_token' in self.session.cookies:
            login_data = dict(username=username, password=password, user_token=csrftoken, Login="Login")
        else:
            login_data = dict(username=username, password=password)
        """
        print(login_data)
        r = self.session.post(self.login_url, data=login_data, headers=dict(Referer=self.login_url))

        # Change security to low
        resp = self.session.get("http://192.168.88.132/dvwa/security.php")
        
        soup = BeautifulSoup(resp.content, 'lxml')
        forms = soup.find_all('form')
        for form in forms:
            inputs = form.find_all('input')
            for input in inputs:
                try:
                    input_name = str(input["name"])
                except:
                    continue
                if "token" in input_name or "csrf" in input_name:
                    form_csrf = input["value"]
                    csrftoken = form_csrf
                    break
            
        login_data = dict(security='low', seclev_submit='Submit')
        self.session.post("http://192.168.88.132/dvwa/security.php", data=login_data, headers=dict(Referer=self.root_url))
        print(self.session.cookies.get_dict())

    def handler(self):
        while len(self.visit_queue) > 0:
            url_to_visit = self.visit_queue.pop()
            if self.__engine(url_to_visit) != -1:
                self.visited.add(url_to_visit)
            if len(self.visited) > 20:
                break
        print(self.visited)
        self.xss_fuzzer = XSS_TEST(self.visited, self.session, self.has_csrf, self.csrf_token_name)
        self.xss_fuzzer.handler()

    def __engine(self, cur_url):
        # Do not visit illegal url
        if any(illegal_url in cur_url for illegal_url in self.illegal_urls):
            return -1
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
        return 1
    

def __main__():
    login_data = {
        'username'  : 'admin',
        'password'  : 'password',
        'Login'     : 'Login,',
    }

    # Fill in keywords or urls that you want to exclude from crawling
    illegals = ['setup','security','brute','csrf','logout']


    has_csrf = input("Do forms in the target website have CSRF tokens?(y/n)")[0]
    csrf_token_name = ""
    if has_csrf == 'y':
        has_csrf = True
        csrf_token_name = input("What's the name of the csrf tokens in the target website?")
    else:
        has_csrf = False
    
    a = crawler(INPUT, illegals, has_csrf, csrf_token_name, True, "http://192.168.88.132/dvwa/login.php", login_data)
    a.handler()

if __name__ == '__main__':
    __main__()