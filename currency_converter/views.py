from django.shortcuts import render
from django.http import JsonResponse
import requests
import json

# Major world currencies
CURRENCIES = {
    'USD': {'name': 'US Dollar', 'symbol': '$', 'flag': '🇺🇸'},
    'EUR': {'name': 'Euro', 'symbol': '€', 'flag': '🇪🇺'},
    'GBP': {'name': 'British Pound', 'symbol': '£', 'flag': '🇬🇧'},
    'JPY': {'name': 'Japanese Yen', 'symbol': '¥', 'flag': '🇯🇵'},
    'AUD': {'name': 'Australian Dollar', 'symbol': 'A$', 'flag': '🇦🇺'},
    'CAD': {'name': 'Canadian Dollar', 'symbol': 'C$', 'flag': '🇨🇦'},
    'CHF': {'name': 'Swiss Franc', 'symbol': 'Fr', 'flag': '🇨🇭'},
    'CNY': {'name': 'Chinese Yuan', 'symbol': '¥', 'flag': '🇨🇳'},
    'INR': {'name': 'Indian Rupee', 'symbol': '₹', 'flag': '🇮🇳'},
    'BRL': {'name': 'Brazilian Real', 'symbol': 'R$', 'flag': '🇧🇷'},
    'RUB': {'name': 'Russian Ruble', 'symbol': '₽', 'flag': '🇷🇺'},
    'ZAR': {'name': 'South African Rand', 'symbol': 'R', 'flag': '🇿🇦'},
    'MXN': {'name': 'Mexican Peso', 'symbol': '$', 'flag': '🇲🇽'},
    'SGD': {'name': 'Singapore Dollar', 'symbol': 'S$', 'flag': '🇸🇬'},
    'HKD': {'name': 'Hong Kong Dollar', 'symbol': 'HK$', 'flag': '🇭🇰'},
    'NZD': {'name': 'New Zealand Dollar', 'symbol': 'NZ$', 'flag': '🇳🇿'},
    'SEK': {'name': 'Swedish Krona', 'symbol': 'kr', 'flag': '🇸🇪'},
    'NOK': {'name': 'Norwegian Krone', 'symbol': 'kr', 'flag': '🇳🇴'},
    'DKK': {'name': 'Danish Krone', 'symbol': 'kr', 'flag': '🇩🇰'},
    'PLN': {'name': 'Polish Zloty', 'symbol': 'zł', 'flag': '🇵🇱'},
    'TRY': {'name': 'Turkish Lira', 'symbol': '₺', 'flag': '🇹🇷'},
    'KRW': {'name': 'South Korean Won', 'symbol': '₩', 'flag': '🇰🇷'},
    'THB': {'name': 'Thai Baht', 'symbol': '฿', 'flag': '🇹🇭'},
    'AED': {'name': 'UAE Dirham', 'symbol': 'د.إ', 'flag': '🇦🇪'},
    'SAR': {'name': 'Saudi Riyal', 'symbol': '﷼', 'flag': '🇸🇦'},
}

# Major cryptocurrencies
CRYPTOCURRENCIES = {
    'BTC': {'name': 'Bitcoin', 'symbol': '₿'},
    'ETH': {'name': 'Ethereum', 'symbol': 'Ξ'},
    'BNB': {'name': 'Binance Coin', 'symbol': 'BNB'},
    'SOL': {'name': 'Solana', 'symbol': 'SOL'},
    'XRP': {'name': 'Ripple', 'symbol': 'XRP'},
    'ADA': {'name': 'Cardano', 'symbol': 'ADA'},
    'DOGE': {'name': 'Dogecoin', 'symbol': 'DOGE'},
    'DOT': {'name': 'Polkadot', 'symbol': 'DOT'},
    'MATIC': {'name': 'Polygon', 'symbol': 'MATIC'},
    'LTC': {'name': 'Litecoin', 'symbol': 'Ł'},
    'AVAX': {'name': 'Avalanche', 'symbol': 'AVAX'},
    'LINK': {'name': 'Chainlink', 'symbol': 'LINK'},
    'UNI': {'name': 'Uniswap', 'symbol': 'UNI'},
    'ATOM': {'name': 'Cosmos', 'symbol': 'ATOM'},
    'ETC': {'name': 'Ethereum Classic', 'symbol': 'ETC'},
}

def get_exchange_rate(from_currency, to_currency):
    """Get exchange rate from API"""
    try:
        # Using exchangerate-api.com free endpoint (no API key needed for basic usage)
        url = f'https://api.exchangerate-api.com/v4/latest/{from_currency}'
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            rates = data.get('rates', {})
            if to_currency in rates:
                return rates[to_currency]
        
        # Fallback: try reverse conversion
        url = f'https://api.exchangerate-api.com/v4/latest/{to_currency}'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            rates = data.get('rates', {})
            if from_currency in rates:
                return 1 / rates[from_currency]
        
        return None
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return None

# Crypto ID mapping for CoinGecko API
CRYPTO_IDS = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'BNB': 'binancecoin',
    'SOL': 'solana',
    'XRP': 'ripple',
    'ADA': 'cardano',
    'DOGE': 'dogecoin',
    'DOT': 'polkadot',
    'MATIC': 'matic-network',
    'LTC': 'litecoin',
    'AVAX': 'avalanche-2',
    'LINK': 'chainlink',
    'UNI': 'uniswap',
    'ATOM': 'cosmos',
    'ETC': 'ethereum-classic',
}

def get_crypto_rate(crypto, currency='USD'):
    """Get cryptocurrency rate"""
    try:
        crypto_id = CRYPTO_IDS.get(crypto)
        if not crypto_id:
            return None
        
        # Using CoinGecko free API (no API key needed)
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies={currency.lower()}'
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if crypto_id in data and currency.lower() in data[crypto_id]:
                return data[crypto_id][currency.lower()]
        
        return None
    except Exception as e:
        print(f"Error fetching crypto rate: {e}")
        return None

def index(request):
    """Currency and crypto converter main page"""
    all_currencies = {**CURRENCIES, **CRYPTOCURRENCIES}
    
    context = {
        'currencies': CURRENCIES,
        'cryptocurrencies': CRYPTOCURRENCIES,
        'all_currencies': all_currencies,
    }
    return render(request, 'currency_converter/index.html', context)

def convert(request):
    """Handle currency/crypto conversion"""
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount', 0))
            from_currency = request.POST.get('from_currency', 'USD')
            to_currency = request.POST.get('to_currency', 'EUR')
            
            if amount <= 0:
                return JsonResponse({'error': 'Amount must be greater than 0'}, status=400)
            
            # Check currency types
            from_is_fiat = from_currency in CURRENCIES
            to_is_fiat = to_currency in CURRENCIES
            from_is_crypto = from_currency in CRYPTOCURRENCIES
            to_is_crypto = to_currency in CRYPTOCURRENCIES
            
            rate = None
            
            # Fiat to Fiat
            if from_is_fiat and to_is_fiat:
                rate = get_exchange_rate(from_currency, to_currency)
            # Crypto to Fiat
            elif from_is_crypto and to_is_fiat:
                crypto_rate = get_crypto_rate(from_currency, to_currency)
                if crypto_rate:
                    rate = crypto_rate
            # Fiat to Crypto
            elif from_is_fiat and to_is_crypto:
                crypto_rate = get_crypto_rate(to_currency, from_currency)
                if crypto_rate:
                    rate = 1 / crypto_rate
            # Crypto to Crypto (convert via USD)
            elif from_is_crypto and to_is_crypto:
                from_rate = get_crypto_rate(from_currency, 'USD')
                to_rate = get_crypto_rate(to_currency, 'USD')
                if from_rate and to_rate:
                    rate = from_rate / to_rate
            
            if rate is None:
                return JsonResponse({'error': 'Unable to fetch exchange rate. Please try again.'}, status=500)
            
            converted_amount = amount * rate
            
            return JsonResponse({
                'success': True,
                'amount': amount,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'rate': rate,
                'converted_amount': converted_amount,
            })
            
        except ValueError:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)
