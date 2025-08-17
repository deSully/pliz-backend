# merchants/factory.py
from transaction.merchants.processors.canalplus import SampleMerchantPaymentProcessor


class MerchantPaymentFactory:
    @staticmethod
    def get_merchant_processor(merchant):
        if merchant == 'M2201':
            return SampleMerchantPaymentProcessor(merchant)
        elif merchant == 'YYY':
            pass
        else:
            raise ValueError(f"Le code marchand {merchant} est inconnu.")
