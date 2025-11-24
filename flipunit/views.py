from django.shortcuts import render

def home(request):
    """Home page"""
    context = {
        'categories': [
            {
                'name': 'Unit Converters',
                'url': 'converters:index',
                'description': 'Convert between different units of measurement',
                'icon': 'unit-converters.svg'
            },
            {
                'name': 'Image Converters',
                'url': 'image_converter:index',
                'description': 'Convert images between different formats',
                'icon': 'image-converters.svg'
            },
            {
                'name': 'Media Converters',
                'url': 'media_converter:index',
                'description': 'Convert media files and download audio. YouTube to mp3 & etc.',
                'icon': 'media-converters.svg'
            },
            {
                'name': 'PDF Tools',
                'url': 'pdf_tools:index',
                'description': 'Merge, split, and convert PDF files',
                'icon': 'pdf-tools.svg'
            },
            {
                'name': 'Currency & Crypto',
                'url': 'currency_converter:index',
                'description': 'Convert between currencies and cryptocurrencies with real-time rates',
                'icon': 'currency-crypto.svg'
            },
            {
                'name': 'Utilities',
                'url': 'utilities:index',
                'description': 'Calculators, text utilities, color converter, QR codes and more',
                'icon': 'utilities.svg'
            },
        ]
    }
    return render(request, 'home.html', context)

