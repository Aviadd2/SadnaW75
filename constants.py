MAX_RETRIES = 3

TIMEOUT = 15

ORDER_NUMBER_LENGTH = 6

# Unified source of truth for options and pricing
OPTIONS_DETAILS = {
    'size': {"1": ("S", 0.2), "2": ("M", 0.3), "3": ("L", 0.4), "4": ("XL", 0.5)},
    'amount': {"1": ("12", 6), "2": ("30", 15)},
    'pack': {"1": ("ארוז", 1), "2": ("לא ארוז", 0.5)},
    'type': {"1": ("אומגה 3", 1.5), "2": ("חופש", 1.2), "3": ("אורגני", 1.2), "4": ("רגיל", 0.7)},
    'restart': "0"
}

SALES_FORCE_ACCOUNT = {
    'username': "aviad@sadna.sandbox",
    'password': "Abc123456",
    'consumer_key': "3MVG9YFqzc_KnL.xEj9zNTrtNJ1njZOks_hquOujIPOP0o1NyoB9EOomUvCN_n9BDh4wfThMxlpJXw3vw.yBH",
    'consumer_secret': "6C4F9466E471F9CE5ACD1D7ED993745FAB9F22328B08A63D90CE9819021F799D",
    'security_token': "wgghtuA1MWPSJ35Q2k1SAwcJ"
}

ORDER_STAGES = {
    'ACCEPTED': 'Accepted',
    'DELIVERY': 'Delivery',
    'DELIVERED': 'Delivered'
}

BASE_ICOUNT_URL = "https://api.icount.co.il/api/v3.php"

CHECK_INTERVAL = 5

AUTH_TOKEN = 'ZFy52DvqWzTafOdyCOg6FbJ640u2UYyR'

API_URL = 'https://gate.whapi.cloud/messages'

STORE_NAME = "אור השחר בע״מ"

ICOUNT_ACCOUNT = {
    'username': "Galovadia186",
    'password': "Gg123456",
    'cid': "G123456789"
}
