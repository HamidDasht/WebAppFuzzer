from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlencode
from colorama import Fore

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumrequests import Chrome

class XSS_TEST:
    def __init__(self, urls: list, session) -> None:
        self.webpages = urls
        self.session = session
        self.payload = list()

        # Initialize selenium driver capable of running JavaScript 
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        #chrome_options.headless = True # also works
        chrome_options.add_argument("--enable-javascript")
        self.driver = Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        self.driver.get("http://192.168.88.132/dvwa/")
        self.driver.delete_all_cookies()
        cookie_dict = self.session.cookies.get_dict()
        for key, value in cookie_dict.items():
            print('name', key, 'value',value)
            self.driver.add_cookie({'name' : key, 'value' : value})
        print(self.session.cookies.get_dict())
        
    def handler(self):
        self.__check_xss()

    
    def __find_forms(self, page) -> list and str:
        print("Gathering forms at {}".format(page))
        try:
            resp = self.session.get(page, allow_redirects=True)
            soup = BeautifulSoup(resp.content, 'lxml')
            page_title = soup.title.text
        except:
            return None, None

        
        forms = list(soup.find_all('form'))
        print("\tFound {} number of form(s)".format(len(forms)))
        return forms, page_title

    def __check_xss(self):
        for page in self.webpages:
            # If has CSRF
            """
            checked_forms = set()
            forms, title = self.__find_forms(page)
            self.__make_payload(title)
            forms = list(set(forms).difference(checked_forms))
            for i in range(len(forms)):
                form = forms[0]
                print("========================================================================================================")
                try:
                    form_method = form["method"]
                    form_action = form["action"]
                    print(form_action,form_method)
                except:
                    continue
                print(title)
                inputs = form.find_all('input')  + form.find_all('textarea')
                print(inputs)
                self.__test_payload(form, page, inputs, form_action, form_method)
                checked_forms.add(form)
                forms, title = self.__find_forms(page)
                forms = list(set(forms).difference(checked_forms))

            continue"""
            # If no CSRF
            forms, title = self.__find_forms(page)
            if forms == None:
                continue
            self.__make_payload(title)
            print("\tChecking all the forms for {}".format(page))
            for form in forms:
                try:
                    form_method = form["method"]
                except:
                    continue
                try:
                    form_action = form["action"]
                except:
                    form_action = ""
                print("\tChecking a form with action: {} and method: {}".format(form_action, form_method))
                inputs = form.find_all('input') + form.find_all('textarea')
                if len(inputs) == 0:
                    continue
                #print(inputs)
                self.__test_payload(form, page, inputs, form_action, form_method)
            print("\t{} is Done\n".format(page))
                
    
    def __make_payload(self, title):
        if title != "empty":
            new_title = "\'empty\';"
        else:
            new_title = "\'emp\'"
        self.payloads = ["<script>document.title={}</script>".format(new_title)]
                         #"",
                         #""
                        #]
        

    def __test_payload(self, form, page: str, inputs: list, form_action: str, form_method: str) -> None:
        self.driver.get(page)
        for payload in self.payloads:
            inputs_value = dict()
            # Parse input fields and put vulnebrable payload
            for input in inputs:
                try:
                    input_name = str(input["name"])
                except:
                    continue
                if "csrf" in input_name:
                    form_csrf = input["value"]
                    inputs_value[input_name] = form_csrf
                    continue
                
                if  input.name == 'textarea' or input['type'] == 'text':
                    inputs_value[input_name] = payload
                else:
                    try:
                        inputs_value[input_name] = input["value"]
                    except:
                        continue
            
            #print(page, form_action)
            req_url = urljoin(page, form_action)
            
            if 'logout' in req_url:
                return

            print("\t\tForm at {} with {} inputs".format(req_url, inputs_value))
            if form_method.lower() == "post":
                try:
                    sub_btn = ""
                    print(inputs_value.items())
                    for key,value in inputs_value.items():
                        item = self.driver.find_element_by_name(key)
                        if 'submit' in key.lower().strip():
                            sub_btn = key
                            continue
                        elif item.get_attribute("type").lower().strip() == "submit":
                            sub_btn = key
                            continue
                        item.send_keys(value)
                    if len(sub_btn):
                        self.driver.find_element_by_name(sub_btn).click()
                        resp = self.driver.page_source
                    else:
                        print(Fore.YELLOW + "Couldn't find form submit btn" + Fore.WHITE)
                        return
                except:
                    print("Connection error at {}".format(req_url))
                    print(inputs_value)
                    return
            elif form_method.lower() == "get":
                try:
                    req_url_with_params =req_url+"?" + urlencode(inputs_value)
                    print(Fore.GREEN + req_url_with_params + Fore.WHITE)
                    self.driver.get(req_url_with_params)

                    resp = self.driver.page_source
                except:
                    print("Connection error at {}".format(req_url))
                    print(inputs_value)
                    return

            #print(Fore.CYAN + resp + Fore.WHITE)
            soup = BeautifulSoup(resp, 'lxml')

            try:
                soup = BeautifulSoup(resp, 'lxml')
                print("\t\t\tResponses title is: ", soup.title.text)
                if soup.title.text == "emp" or soup.title.text == "empty":
                    print(Fore.RED + "FOUND XSS VULNERABILITY AT {}\nIN FORM {}".format(page, form) + Fore.WHITE)
            except:
                print(Fore.YELLOW + "ERROR AT FORM Submission" + Fore.WHITE)