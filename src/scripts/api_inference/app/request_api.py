import requests

url = "http://127.0.0.1:8000/predict/model_logreg/"

data = {
    "Culmen_Length": 45.2,
    "Culmen_Depth": 14.8,
    "Flipper_Length": 210.0,
    "Body_Mass": 3800.0
}

response = requests.post(url, json=data)

print(response.status_code)
print(response.json())
