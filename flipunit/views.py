from django.shortcuts import render

def home(request):
    """Home page"""
    context = {
        'categories': [
            {
                'name': 'Unit Converters',
                'url': 'converters:index',
                'description': 'Convert between different units of measurement',
                'icon': '📏'
            },
            {
                'name': 'Image Converters',
                'url': 'image_converter:index',
                'description': 'Convert images between different formats',
                'icon': '🖼️'
            },
            {
                'name': 'Media Converters',
                'url': 'media_converter:index',
                'description': 'Convert media files and download audio. YouTube to mp3 & etc.',
                'icon': '🎵'
            },
            {
                'name': 'PDF Tools',
                'url': 'pdf_tools:index',
                'description': 'Merge, split, and convert PDF files',
                'icon': '📄'
            },
            {
                'name': 'Currency & Crypto',
                'url': 'currency_converter:index',
                'description': 'Convert between currencies and cryptocurrencies with real-time rates',
                'icon': '💱'
            },
            {
                'name': 'Utilities',
                'url': 'utilities:index',
                'description': 'Calculators, text utilities, color converter, QR codes and more',
                'icon': '🛠️'
            },
        ]
    }
    return render(request, 'home.html', context)

