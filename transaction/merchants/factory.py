# merchants/factory.py
from transaction.merchants.processors.samir_pay import SamirPayMerchantPaymentProcessor


class MerchantPaymentFactory:
    @staticmethod
    def get_merchant_processor(merchant_code):
        if merchant_code in ["airtime", "woyofal", "rapido"]:
            return SamirPayMerchantPaymentProcessor(merchant_code)
        elif merchant_code == "YYY":
            pass
        else:
            raise ValueError(f"Le code marchand {merchant_code} est inconnu.")
