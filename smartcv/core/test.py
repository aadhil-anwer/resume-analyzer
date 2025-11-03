import requests

url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-company-by-linkedinurl"

querystring = {"linkedin_url":"https://www.linkedin.com/company/apple/"}

headers = {"x-rapidapi-host": "fresh-linkedin-profile-data.p.rapidapi.com"}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())