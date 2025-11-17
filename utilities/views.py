from django.shortcuts import render

def index(request):
    """Utilities index page"""
    context = {
        'utilities': [
            {'name': 'PDF Tools', 'url': 'pdf-tools', 'description': 'Merge, split, and compress PDF files'},
            {'name': 'Calculator', 'url': 'calculator', 'description': 'Simple online calculator'},
            {'name': 'Text Tools', 'url': 'text-tools', 'description': 'Word count, character count, and text utilities'},
        ]
    }
    return render(request, 'utilities/index.html', context)

def calculator(request):
    """Simple calculator"""
    result = None
    error = None
    
    if request.method == 'POST':
        try:
            expression = request.POST.get('expression', '').strip()
            if expression:
                # Basic safety check - only allow numbers, operators, and parentheses
                allowed_chars = set('0123456789+-*/.() ')
                if all(c in allowed_chars for c in expression):
                    result = eval(expression)
                else:
                    error = 'Invalid characters in expression'
        except Exception as e:
            error = f'Error: {str(e)}'
    
    context = {
        'result': result,
        'error': error,
    }
    return render(request, 'utilities/calculator.html', context)

def pdf_tools(request):
    """PDF tools placeholder"""
    return render(request, 'utilities/pdf_tools.html', {
        'message': 'PDF tools require additional libraries (PyPDF2, pdf2image, etc.). This is a placeholder.'
    })

def text_tools(request):
    """Text utilities"""
    word_count = None
    char_count = None
    char_count_no_spaces = None
    text = ''
    
    if request.method == 'POST':
        text = request.POST.get('text', '')
        if text:
            word_count = len(text.split())
            char_count = len(text)
            char_count_no_spaces = len(text.replace(' ', ''))
    
    context = {
        'text': text,
        'word_count': word_count,
        'char_count': char_count,
        'char_count_no_spaces': char_count_no_spaces,
    }
    return render(request, 'utilities/text_tools.html', context)
