import requests

BASE_URL = "http://127.0.0.1:8000"
LOGIN_RESOURCE = "/api/actor/auth/login/"
TRANSACTION_RESOURCE = "/api/transaction/history"

def get_access_token():
    url = BASE_URL + LOGIN_RESOURCE
    payload = {
        "pin": "1111",
        "phone_number": "+221775004578"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data.get("access")
    else:
        print("Erreur lors de l'authentification:", response.text)
        return None

def get_transaction_history(access_token):
    url = BASE_URL + TRANSACTION_RESOURCE
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Erreur lors de la récupération de l'historique:", response.text)
        return None

def main():
    access_token = get_access_token()
    print(access_token)
    

if __name__ == "__main__":
    main()
