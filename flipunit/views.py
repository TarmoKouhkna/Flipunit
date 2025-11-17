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
                'description': 'Convert media files and download audio',
                'icon': '🎵'
            },
            {
                'name': 'Utilities',
                'url': 'utilities:index',
                'description': 'PDF tools, calculators, and text utilities',
                'icon': '🛠️'
            },
        ]
    }
    return render(request, 'home.html', context)

