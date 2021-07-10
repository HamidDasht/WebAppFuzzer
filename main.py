import requests, os
from urllib.parse import urlparse
from urllib.parse import urljoin
from requests_html import HTMLSession
from bs4 import BeautifulSoup
from colorama import Fore
from packages.xss_fuzzer import Fuzzer


# Fill in keywords or urls that you want to exclude from crawling
illegals = ['setup','security','brute','csrf','logout','.pdf','.mp4']

ta_login_data = {
    'username'  : 'mmz',
    'password'  : '12345'
    }

dvwa_login_data = {
    'username'  : 'admin',
    'password'  : 'password',
    'Login'     : 'Login'
    }

custom_login_data = {

}

TA_ROOT = "http://127.0.0.1:8000/home/"
TA_LOGIN = "http://127.0.0.1:8000/home/"
DVWA_ROOT = "http://192.168.88.132/dvwa/index.php"
DVWA_LOGIN = "http://192.168.88.132/dvwa/login.php"
CRAWLER_LIMIT = 20 

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
        print(Fore.GREEN + "Targeting " + self.target_domain + " domain" + Fore.WHITE)

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
        
        print(Fore.GREEN + "Login Data:", end="")
        print( login_data,end="" )
        print(Fore.WHITE)
        r = self.session.post(self.login_url, data=login_data, headers=dict(Referer=self.login_url))

        # Change security to low for DVWA test
        if self.root_url in DVWA_ROOT:
            resp = self.session.get("http://192.168.88.132/dvwa/security.php")    
            data = dict(security='low', seclev_submit='Submit')
            self.session.post("http://192.168.88.132/dvwa/security.php", data=data, headers=dict(Referer=self.root_url))
        
        #print(self.session.cookies.get_dict())

    def handler(self):
        while len(self.visit_queue) > 0:
            url_to_visit = self.visit_queue.pop()
            if self.__engine(url_to_visit) != -1:
                self.visited.add(url_to_visit)
            if len(self.visited) > CRAWLER_LIMIT:
                break
        self.xss_fuzzer = Fuzzer(self.visited, self.session, self.has_csrf, self.csrf_token_name)
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
    
    # Get target website's urls and login information
    root_url, login_required, login_url, login_data, has_csrf, csrf_token_name = get_target_info()
    
    a = crawler(root_url, illegals, has_csrf, csrf_token_name, login_required, login_url, login_data)
    a.handler()


def get_target_info():
    while 1:
        try:
            target = int(input("Choose your target:\n\t1. DVWA\n\t2. TA\n\t3. Custom\n"))
        except:
            print("ERROR: Input must be an integer")
            continue
        if target == 1:
            root_url = DVWA_ROOT
            login_required = True
            login_url = DVWA_LOGIN
            login_data = dvwa_login_data
            break
        elif target == 2:
            root_url = TA_ROOT
            login_required = True
            login_url = TA_LOGIN
            login_data = ta_login_data
            break
        elif target == 3:
            root_url = input("Enter root url in [http(s)://*] format: ")
            login_required = input("Is login required?(y/n)")[0]
            login_data = custom_login_data

            if login_required == 'y':
                login_required = True
                login_url = input("Enter login url in [http(s)://*] format: ")
            else:
                login_required = False
                login_url = ""
            break
        else:
            print("ERROR: Input must be 1, 2 or 3")
            continue

    has_csrf = input("Do forms in the target website have CSRF tokens?(y/n)")[0]
    csrf_token_name = ""
    if has_csrf == 'y':
        has_csrf = True
        csrf_token_name = input("Enter name of the csrf tokens in the target website: ")
    else:
        has_csrf = False
    
    return root_url, login_required, login_url, login_data, has_csrf, csrf_token_name

if __name__ == '__main__':
    __main__()