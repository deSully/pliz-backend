def identify_wallet_owner(wallet):
    if hasattr(wallet, 'merchant'):
        return 'merchant', wallet.merchant
    if hasattr(wallet, 'bank'):
        return 'bank', wallet.bank
    if hasattr(wallet, 'provider'):
        return 'provider', wallet.provider
    return 'client', None
