from django.shortcuts import render
from django.contrib import messages
from .models import Feedback

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def home(request):
    """Home page"""
    if request.method == 'POST' and 'feedback' in request.POST:
        feedback_text = request.POST.get('feedback', '').strip()
        if feedback_text:
            # Validate length (1000 characters max)
            if len(feedback_text) > 1000:
                messages.error(request, 'Feedback is too long. Maximum 1000 characters allowed.')
            else:
                # Save feedback to database
                Feedback.objects.create(
                    message=feedback_text,
                    ip_address=get_client_ip(request)
                )
                messages.success(request, 'Thank you for your feedback!')
        else:
            messages.error(request, 'Please enter your feedback.')
    
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

