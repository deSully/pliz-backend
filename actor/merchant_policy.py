from collections import namedtuple
# Policy = règles par marchand

MerchantPolicy = namedtuple("MerchantPolicy", ["required_fields", "public"])

MERCHANT_POLICIES = {
    "rapido": MerchantPolicy(required_fields=["cardNumber"], public=True),
    "woyofal": MerchantPolicy(
        required_fields=["meterNumber", "phoneNumber"], public=True
    ),
    "airtime": MerchantPolicy(required_fields=["phoneNumber", "operator"], public=True),
}
