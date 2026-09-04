import os
import requests
from dotenv import load_dotenv

load_dotenv()

image_url = "https://i.imgur.com/HBrB8p0.png"

import os
import requests
from dotenv import load_dotenv

load_dotenv()

image_url = "https://i.imgur.com/HBrB8p0.png"

response = requests.get(
    "https://api.openwebninja.com/reverse-image-search/reverse-image-search",
    params={"url": image_url},
    headers={
        "x-api-key": os.getenv("OPENWEBNINJA_API_KEY")
    }
)

print("Search:", response.status_code)
print(response.text)

# 2. Reverse image search
response = requests.get(
    "https://api.openwebninja.com/reverse-image-search/reverse-image-search",
    params={"url": image_url},
    headers={
        "x-api-key": os.getenv("OPENWEBNINJA_API_KEY")
    }
)

print("Search:", response.status_code)
print(response.text)