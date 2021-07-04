from bs4 import BeautifulSoup
class XSS_TEST:
    def __init__(self, urls: list, session) -> None:
        self.webpages = urls
        self.session = session
        self.payload = list()
        
    def handler(self):
        self.__check_xss()

    
    def __find_forms(self, page) -> list and str:
        try:
            resp = self.session.get(page, allow_redirects=True)
        except:
            return

        soup = BeautifulSoup(resp.content, 'lxml')
        forms = list(soup.find_all('form'))
        return forms, soup.title.text

    def __check_xss(self):
        for page in self.webpages:
            forms, title = self.__find_forms(page)
            self.__make_payload(title)
            for form in forms:
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
                self.__test_payload(page, inputs, form_action, form_method)
                
    
    def __make_payload(self, title):
        if title != "":
            new_title = "\'\';"
        else:
            new_title = "empty;"
        self.payloads = ["<script>document.title={}</script>".format(new_title)]
                         #"",
                         #""
                        #]
        

    def __test_payload(self, page: str, inputs: list, form_action: str, form_method: str) -> None:
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
                
                inputs_value[input_name] = payload

            # TODO: Submit form and check if the result show XSS vulnerability 
            # Make request and test the payload
            #r = self.session.post(self.root_url, data=inputs_value, headers=dict(Referer=self.root_url))
            print(inputs_value)

