import requests

# Define the API endpoint
url = 'https://api.scrapingrobot.com/'

# Set up the query parameters
params = {
    'token': '3ca19568-2493-4e1c-8d2a-49d4e44ca883',
    'url': 'https://nust.edu.pk'
}

# Make the GET request
response = requests.get(url, params=params)

# Print the response content
print(response.text)
