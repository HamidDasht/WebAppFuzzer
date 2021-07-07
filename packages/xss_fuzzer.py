from bs4 import BeautifulSoup
from urllib.parse import urljoin

class XSS_TEST:
    def __init__(self, urls: list, session) -> None:
        self.webpages = urls
        self.session = session
        self.payload = list()
        
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
        print("\tFound {} number(s) of forms".format(len(forms)))
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
                inputs = form.find_all('input')
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
                inputs = form.find_all('input')
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
                
                if input['type'] == 'text':
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
                    resp = self.session.post(req_url, data=inputs_value,allow_redirects=True)
                except:
                    print("Connection error at {}".format(req_url))
                    print(inputs_value)
                    return
            elif form_method.lower() == "get":
                try:
                    resp = self.session.get(req_url, data=inputs_value,allow_redirects=True)
                except:
                    print("Connection error at {}".format(req_url))
                    print(inputs_value)
                    return

            #print(resp.content)
            soup = BeautifulSoup(resp.content, 'lxml')
            print("\t\t\tResponses title is: ", soup.title.text)

            try:
                soup = BeautifulSoup(resp.content, 'lxml')
                if soup.title.text == "emp" or soup.title.text == "empty":
                    print("FOUND XSS VULNERABILITY AT {}\nIN FORM {}".format(page, form))
            except:
                print(resp)
                print("error")
                exit()