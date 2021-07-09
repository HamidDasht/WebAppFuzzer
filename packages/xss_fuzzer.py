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
    def __init__(self, urls: list, session, has_csrf: bool, csrf_token_name: str) -> None:
        self.webpages = urls
        self.session = session
        self.has_csrf = has_csrf
        self.csrf_token_name = csrf_token_name
        self.payload = list()

        # Initialize Selenium driver (capable of running JavaScript)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.headless = True # also works
        chrome_options.add_argument("--enable-javascript")
        self.driver = Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        self.driver.get("http://192.168.88.132/dvwa/")
        self.driver.delete_all_cookies()

        # Export current session cookies to Selenium
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
            forms, title = self.__find_forms(page)
            # If the page has no forms continue to the next one
            if forms == None:
                continue

            self.__make_payload(title)
            
            print("\tChecking all the forms for {}".format(page))
            
            for form in forms:
                # Extract method and action attributes
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

                # If has no inputs continue to the next form
                if len(inputs) == 0:
                    continue

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
        for payload in self.payloads:
            self.driver.get(page)
            # Referesh inputs to update CSRF tokens
            if self.has_csrf:
                resp = self.driver.page_source
                soup = BeautifulSoup(resp, 'lxml')
                form = soup.find('form', form.attrs)
                inputs = form.find_all('input') + form.find_all('textarea')

            inputs_value = dict() # Used to save input tags' name and value

            # Parse input fields and put vulnebrable payload
            for input in inputs:
                try:
                    input_name = str(input["name"])
                except:
                    continue
                if self.has_csrf and self.csrf_token_name in input_name:
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
            
            req_url = urljoin(page, form_action)
            print("\t\tForm at {} with {} inputs".format(req_url, inputs_value))

            if form_method.lower() == "post":
                sub_btn = ""
                print(inputs_value.items())
                for key,value in inputs_value.items():
                    item = self.driver.find_element_by_name(key)
                    # If Payload is larger than input's size
                    # put small payload instead of payload
                    try:
                        if (int(item.get_attribute('maxlength') )< len(payload)):
                            item.send_keys('a')
                            continue
                    except:
                        pass
                        
                    # If the element is a submit btn or a submit-type btn 
                    # save it for submission and continue to the next input.
                    # Otherwise fill input with appropriate value.
                    if 'submit' in key.lower().strip():
                        sub_btn = key
                        continue
                    elif item.get_attribute("type").lower().strip() == "submit":
                        sub_btn = key
                        continue
                    else:
                        item.send_keys(value)

                # If a submit btn was found submit the form and save the response
                # Otherwise issue an error and ignore the form.
                try:
                    if len(sub_btn):
                        self.driver.find_element_by_name(sub_btn).click()
                        resp = self.driver.page_source
                    else:
                        print(Fore.YELLOW + "Couldn't find form submit btn" + Fore.WHITE)
                        return
                # An error occured during submission
                except:
                    print(Fore.YELLOW + "Connection error at {}".format(req_url) + Fore.WHITE)
                    print(inputs_value)
                    return
            
            elif form_method.lower() == "get":
                try:
                    # Append GET parameters to the page's url
                    req_url_with_params =req_url+"?" + urlencode(inputs_value)
                    print(Fore.GREEN + req_url_with_params + Fore.WHITE)
                    self.driver.get(req_url_with_params)
                    resp = self.driver.page_source
                # An error occured during submission
                except:
                    print("Connection error at {}".format(req_url))
                    print(inputs_value)
                    return


            soup = BeautifulSoup(resp, 'lxml')
            # Check form submission's response for Vulnerability or failure
            try:
                soup = BeautifulSoup(resp, 'lxml')
                print("\t\t\tResponses title is: ", soup.title.text)
                if soup.title.text == "emp" or soup.title.text == "empty": # XSS IS PRESENT
                    print(Fore.RED + "FOUND XSS VULNERABILITY AT {}\nIN FORM {}".format(page, form) + Fore.WHITE)
            except:
                print(Fore.YELLOW + "ERROR AT FORM Submission" + Fore.WHITE)