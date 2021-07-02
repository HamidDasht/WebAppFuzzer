import requests

"""
Result contains html in res.content among other 
things like status code (res.status_code), etc.
"""
res = requests.get("https://www.google.com")

print(res.status_code)