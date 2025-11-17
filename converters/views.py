from django.shortcuts import render
from django.conf import settings

def index(request):
    """Unit converters index page"""
    context = {
        'converters': [
            {'name': 'Length', 'url': 'length', 'description': 'Convert between meters, feet, inches, and more'},
            {'name': 'Weight', 'url': 'weight', 'description': 'Convert between kilograms, pounds, ounces, and more'},
            {'name': 'Temperature', 'url': 'temperature', 'description': 'Convert between Celsius, Fahrenheit, and Kelvin'},
            {'name': 'Volume', 'url': 'volume', 'description': 'Convert between liters, gallons, cups, and more'},
            {'name': 'Area', 'url': 'area', 'description': 'Convert between square meters, square feet, acres, and more'},
            {'name': 'Speed', 'url': 'speed', 'description': 'Convert between km/h, mph, m/s, and more'},
        ]
    }
    return render(request, 'converters/index.html', context)

def converter_tool(request, tool_name):
    """Generic converter tool view"""
    converters = {
        'length': {
            'title': 'Length Converter',
            'units': [
                ('meter', 'm', 1.0),
                ('kilometer', 'km', 1000.0),
                ('centimeter', 'cm', 0.01),
                ('millimeter', 'mm', 0.001),
                ('mile', 'mi', 1609.34),
                ('foot', 'ft', 0.3048),
                ('inch', 'in', 0.0254),
                ('yard', 'yd', 0.9144),
            ]
        },
        'weight': {
            'title': 'Weight Converter',
            'units': [
                ('kilogram', 'kg', 1.0),
                ('gram', 'g', 0.001),
                ('pound', 'lb', 0.453592),
                ('ounce', 'oz', 0.0283495),
                ('ton', 't', 1000.0),
                ('stone', 'st', 6.35029),
            ]
        },
        'temperature': {
            'title': 'Temperature Converter',
            'units': [
                ('celsius', '°C', 'celsius'),
                ('fahrenheit', '°F', 'fahrenheit'),
                ('kelvin', 'K', 'kelvin'),
            ],
            'special': True  # Temperature needs special conversion
        },
        'volume': {
            'title': 'Volume Converter',
            'units': [
                ('liter', 'L', 1.0),
                ('milliliter', 'mL', 0.001),
                ('gallon (US)', 'gal (US)', 3.78541),
                ('gallon (UK)', 'gal (UK)', 4.54609),
                ('quart (US)', 'qt (US)', 0.946353),
                ('quart (UK)', 'qt (UK)', 1.13652),
                ('pint (US)', 'pt (US)', 0.473176),
                ('pint (UK)', 'pt (UK)', 0.568261),
                ('cup', 'cup', 0.236588),
                ('fluid ounce (US)', 'fl oz (US)', 0.0295735),
                ('fluid ounce (UK)', 'fl oz (UK)', 0.0284131),
            ]
        },
        'area': {
            'title': 'Area Converter',
            'units': [
                ('square meter', 'm²', 1.0),
                ('square kilometer', 'km²', 1000000.0),
                ('square centimeter', 'cm²', 0.0001),
                ('square mile', 'mi²', 2589988.11),
                ('square foot', 'ft²', 0.092903),
                ('square inch', 'in²', 0.00064516),
                ('acre', 'ac', 4046.86),
                ('hectare', 'ha', 10000.0),
            ]
        },
        'speed': {
            'title': 'Speed Converter',
            'units': [
                ('meter per second', 'm/s', 1.0),
                ('kilometer per hour', 'km/h', 0.277778),
                ('mile per hour', 'mph', 0.44704),
                ('foot per second', 'ft/s', 0.3048),
                ('knot', 'kn', 0.514444),
            ]
        },
    }
    
    converter = converters.get(tool_name)
    if not converter:
        from django.http import Http404
        raise Http404("Converter not found")
    
    result = None
    result_unit_symbol = None
    if request.method == 'POST':
        try:
            value = float(request.POST.get('value', 0))
            from_unit = request.POST.get('from_unit')
            to_unit = request.POST.get('to_unit')
            
            if converter.get('special') and tool_name == 'temperature':
                # Temperature conversion
                from_type = next((u[2] for u in converter['units'] if u[0] == from_unit), None)
                to_type = next((u[2] for u in converter['units'] if u[0] == to_unit), None)
                
                # Get the symbol for the target unit
                result_unit_symbol = next((u[1] for u in converter['units'] if u[0] == to_unit), '')
                
                # Convert to Celsius first
                if from_type == 'fahrenheit':
                    celsius = (value - 32) * 5/9
                elif from_type == 'kelvin':
                    celsius = value - 273.15
                else:
                    celsius = value
                
                # Convert from Celsius to target
                if to_type == 'fahrenheit':
                    result = celsius * 9/5 + 32
                elif to_type == 'kelvin':
                    result = celsius + 273.15
                else:
                    result = celsius
            else:
                # Standard conversion
                from_factor = next((u[2] for u in converter['units'] if u[0] == from_unit), 1.0)
                to_factor = next((u[2] for u in converter['units'] if u[0] == to_unit), 1.0)
                result = value * from_factor / to_factor
                
                # Get the symbol for the target unit
                result_unit_symbol = next((u[1] for u in converter['units'] if u[0] == to_unit), '')
            
            result = round(result, 6)
        except (ValueError, TypeError):
            result = None
            result_unit_symbol = None
    
    context = {
        'converter': converter,
        'tool_name': tool_name,
        'result': result,
        'result_unit_symbol': result_unit_symbol,
    }
    return render(request, 'converters/converter_tool.html', context)
