import requests

BASE_URL = "http://localhost:8000/api/actor/auth/"  # Remplace par l'URL de ton serveur
PHONE_NUMBER = "+1234567890"  # Remplace par un vrai numéro

# 1️⃣ Envoyer un OTP à un utilisateur
send_otp_url = BASE_URL + "send-otp/"
send_otp_data = {"phone_number": PHONE_NUMBER}
response = requests.post(send_otp_url, json=send_otp_data)
print(response.json())
print("[Send OTP]", response.status_code, response.json())

# 2️⃣ Vérifier si un OTP est valide
check_otp_url = BASE_URL + "check-otp/"
OTP_CODE = 723317
check_otp_data = {"otp": OTP_CODE}
response = requests.post(check_otp_url, json=check_otp_data)
print("[Check OTP]", response.status_code, response.json())

# 3️⃣ Envoyer un OTP pour la connexion d'un utilisateur
send_login_otp_url = BASE_URL + "send-login-otp/"
send_login_otp_data = {"phone_number": PHONE_NUMBER}
response = requests.post(send_login_otp_url, json=send_login_otp_data)
print("[Send Login OTP]", response.status_code, response.json())

# 4️⃣ Enregistrer un nouvel utilisateur
register_url = BASE_URL + "register/"
register_data = {
    "username": "testuser",
    "phone_number": PHONE_NUMBER,
    "password": "StrongPass123"
}
response = requests.post(register_url, json=register_data)
print("[User Registration]", response.status_code, response.json())

# 5️⃣ Connexion d'un utilisateur via OTP
login_url = BASE_URL + "login/"
login_data = {
    "phone_number": PHONE_NUMBER,
    "otp": OTP_CODE
}
response = requests.post(login_url, json=login_data)
print("[User Login]", response.status_code, response.json())
