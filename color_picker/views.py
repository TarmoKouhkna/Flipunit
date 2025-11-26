from django.shortcuts import render

def index(request):
    """Color Picker index page"""
    return render(request, 'color_picker/index.html')

def color_picker(request):
    """Color Picker tool page"""
    return render(request, 'color_picker/picker.html')

def pick_from_image(request):
    """Pick color from image tool page"""
    return render(request, 'color_picker/from_image.html')
