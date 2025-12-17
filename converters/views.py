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
            {'name': 'Time', 'url': 'time', 'description': 'Convert between seconds, minutes, hours, days, and more'},
            {'name': 'Data Storage', 'url': 'data-storage', 'description': 'Convert between bytes, KB, MB, GB, TB, and more'},
            {'name': 'Energy', 'url': 'energy', 'description': 'Convert between joules, calories, watt-hours, and more'},
            {'name': 'Power', 'url': 'power', 'description': 'Convert between watts, kilowatts, horsepower, and more'},
            {'name': 'Pressure', 'url': 'pressure', 'description': 'Convert between Pascal, bar, PSI, atmosphere, and more'},
            {'name': 'Force', 'url': 'force', 'description': 'Convert between newtons, pounds-force, kilogram-force, and more'},
            {'name': 'Angle', 'url': 'angle', 'description': 'Convert between degrees, radians, gradians, and turns'},
            {'name': 'Fuel Consumption', 'url': 'fuel-consumption', 'description': 'Convert between MPG, L/100km, km/L, and more'},
            {'name': 'Frequency', 'url': 'frequency', 'description': 'Convert between Hertz, kilohertz, megahertz, RPM, and more'},
            {'name': 'Data Transfer Rate', 'url': 'data-transfer', 'description': 'Convert between Mbps, MB/s, Gbps, and more'},
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
        'time': {
            'title': 'Time Converter',
            'units': [
                ('second', 's', 1.0),
                ('millisecond', 'ms', 0.001),
                ('microsecond', 'μs', 0.000001),
                ('nanosecond', 'ns', 0.000000001),
                ('minute', 'min', 60.0),
                ('hour', 'h', 3600.0),
                ('day', 'd', 86400.0),
                ('week', 'wk', 604800.0),
                ('month (30 days)', 'mo', 2592000.0),
                ('year (365 days)', 'yr', 31536000.0),
            ]
        },
        'data-storage': {
            'title': 'Data Storage Converter',
            'units': [
                ('byte', 'B', 1.0),
                ('kilobyte', 'KB', 1000.0),
                ('megabyte', 'MB', 1000000.0),
                ('gigabyte', 'GB', 1000000000.0),
                ('terabyte', 'TB', 1000000000000.0),
                ('petabyte', 'PB', 1000000000000000.0),
                ('kibibyte', 'KiB', 1024.0),
                ('mebibyte', 'MiB', 1048576.0),
                ('gibibyte', 'GiB', 1073741824.0),
                ('tebibyte', 'TiB', 1099511627776.0),
                ('bit', 'bit', 0.125),
                ('kilobit', 'Kb', 125.0),
                ('megabit', 'Mb', 125000.0),
                ('gigabit', 'Gb', 125000000.0),
            ]
        },
        'energy': {
            'title': 'Energy Converter',
            'units': [
                ('joule', 'J', 1.0),
                ('kilojoule', 'kJ', 1000.0),
                ('calorie', 'cal', 4.184),
                ('kilocalorie', 'kcal', 4184.0),
                ('watt-hour', 'Wh', 3600.0),
                ('kilowatt-hour', 'kWh', 3600000.0),
                ('electronvolt', 'eV', 1.602176634e-19),
                ('british thermal unit', 'BTU', 1055.06),
                ('foot-pound', 'ft-lb', 1.35582),
            ]
        },
        'power': {
            'title': 'Power Converter',
            'units': [
                ('watt', 'W', 1.0),
                ('kilowatt', 'kW', 1000.0),
                ('megawatt', 'MW', 1000000.0),
                ('horsepower (mechanical)', 'hp', 745.7),
                ('horsepower (metric)', 'PS', 735.5),
                ('BTU per hour', 'BTU/h', 0.293071),
                ('foot-pound per second', 'ft-lb/s', 1.35582),
            ]
        },
        'pressure': {
            'title': 'Pressure Converter',
            'units': [
                ('pascal', 'Pa', 1.0),
                ('kilopascal', 'kPa', 1000.0),
                ('bar', 'bar', 100000.0),
                ('atmosphere', 'atm', 101325.0),
                ('pound per square inch', 'PSI', 6894.76),
                ('torr', 'torr', 133.322),
                ('millimeter of mercury', 'mmHg', 133.322),
                ('inch of mercury', 'inHg', 3386.39),
            ]
        },
        'force': {
            'title': 'Force Converter',
            'units': [
                ('newton', 'N', 1.0),
                ('kilonewton', 'kN', 1000.0),
                ('pound-force', 'lbf', 4.44822),
                ('kilogram-force', 'kgf', 9.80665),
                ('dyne', 'dyn', 0.00001),
                ('ounce-force', 'ozf', 0.278014),
            ]
        },
        'angle': {
            'title': 'Angle Converter',
            'units': [
                ('degree', '°', 1.0),
                ('radian', 'rad', 57.2958),
                ('gradian', 'grad', 0.9),
                ('turn', 'turn', 360.0),
                ('arcminute', "'", 0.0166667),
                ('arcsecond', '"', 0.000277778),
            ]
        },
        'fuel-consumption': {
            'title': 'Fuel Consumption Converter',
            'units': [
                ('liter per 100 km', 'L/100km', 1.0),
                ('kilometer per liter', 'km/L', 'inverse'),
                ('mile per gallon (US)', 'MPG (US)', 235.215),
                ('mile per gallon (UK)', 'MPG (UK)', 282.481),
                ('mile per liter', 'mi/L', 'inverse_miles'),
            ],
            'special': True  # Fuel consumption needs special conversion
        },
        'frequency': {
            'title': 'Frequency Converter',
            'units': [
                ('hertz', 'Hz', 1.0),
                ('kilohertz', 'kHz', 1000.0),
                ('megahertz', 'MHz', 1000000.0),
                ('gigahertz', 'GHz', 1000000000.0),
                ('revolution per minute', 'RPM', 0.0166667),
                ('revolution per second', 'RPS', 1.0),
            ]
        },
        'data-transfer': {
            'title': 'Data Transfer Rate Converter',
            'units': [
                ('bit per second', 'bps', 1.0),
                ('kilobit per second', 'Kbps', 1000.0),
                ('megabit per second', 'Mbps', 1000000.0),
                ('gigabit per second', 'Gbps', 1000000000.0),
                ('byte per second', 'B/s', 8.0),
                ('kilobyte per second', 'KB/s', 8000.0),
                ('megabyte per second', 'MB/s', 8000000.0),
                ('gigabyte per second', 'GB/s', 8000000000.0),
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
            elif converter.get('special') and tool_name == 'fuel-consumption':
                # Fuel consumption conversion (special inverse relationships)
                from_type = next((u[2] for u in converter['units'] if u[0] == from_unit), None)
                to_type = next((u[2] for u in converter['units'] if u[0] == to_unit), None)
                
                # Get the symbol for the target unit
                result_unit_symbol = next((u[1] for u in converter['units'] if u[0] == to_unit), '')
                
                # Convert to L/100km first (base unit)
                if from_type == 'inverse':  # km/L
                    if value != 0:
                        l_per_100km = 100 / value
                    else:
                        l_per_100km = 0
                elif from_type == 'inverse_miles':  # mi/L
                    if value != 0:
                        l_per_100km = 100 / (value / 1.60934)
                    else:
                        l_per_100km = 0
                elif isinstance(from_type, (int, float)):  # MPG
                    if value != 0:
                        l_per_100km = from_type / value
                    else:
                        l_per_100km = 0
                else:  # L/100km
                    l_per_100km = value
                
                # Convert from L/100km to target
                if to_type == 'inverse':  # km/L
                    if l_per_100km != 0:
                        result = 100 / l_per_100km
                    else:
                        result = 0
                elif to_type == 'inverse_miles':  # mi/L
                    if l_per_100km != 0:
                        result = (100 / l_per_100km) * 1.60934
                    else:
                        result = 0
                elif isinstance(to_type, (int, float)):  # MPG
                    if l_per_100km != 0:
                        result = to_type / l_per_100km
                    else:
                        result = 0
                else:  # L/100km
                    result = l_per_100km
            else:
                # Standard conversion
                from_factor = next((u[2] for u in converter['units'] if u[0] == from_unit), 1.0)
                to_factor = next((u[2] for u in converter['units'] if u[0] == to_unit), 1.0)
                result = value * from_factor / to_factor
                
                # Get the symbol for the target unit
                result_unit_symbol = next((u[1] for u in converter['units'] if u[0] == to_unit), '')
            
            result = round(result, 6)
        except (ValueError, TypeError, ZeroDivisionError):
            result = None
            result_unit_symbol = None
    
    # Handle range calculation for fuel consumption
    range_result = None
    range_unit = None
    fuel_display = None
    consumption_display = None
    
    if tool_name == 'fuel-consumption' and request.method == 'POST' and request.POST.get('action') == 'range':
        try:
            fuel_amount = float(request.POST.get('fuel_amount', 0))
            fuel_unit = request.POST.get('fuel_unit')
            consumption_value = float(request.POST.get('consumption_value', 0))
            consumption_unit = request.POST.get('consumption_unit')
            distance_unit = request.POST.get('distance_unit', 'km')
            
            # Convert fuel to liters
            fuel_in_liters = fuel_amount
            if fuel_unit == 'gallon_us':
                fuel_in_liters = fuel_amount * 3.78541
                fuel_display = f"{fuel_amount} gallons (US)"
            elif fuel_unit == 'gallon_uk':
                fuel_in_liters = fuel_amount * 4.54609
                fuel_display = f"{fuel_amount} gallons (UK)"
            else:
                fuel_display = f"{fuel_amount} liters"
            
            # Convert consumption to L/100km
            l_per_100km = consumption_value
            if consumption_unit == 'kilometer per liter':
                if consumption_value != 0:
                    l_per_100km = 100 / consumption_value
                consumption_display = f"{consumption_value} km/L"
            elif consumption_unit == 'mile per gallon (US)':
                if consumption_value != 0:
                    l_per_100km = 235.215 / consumption_value
                consumption_display = f"{consumption_value} MPG (US)"
            elif consumption_unit == 'mile per gallon (UK)':
                if consumption_value != 0:
                    l_per_100km = 282.481 / consumption_value
                consumption_display = f"{consumption_value} MPG (UK)"
            else:
                consumption_display = f"{consumption_value} L/100km"
            
            # Calculate range in km
            if l_per_100km != 0:
                range_km = (fuel_in_liters / l_per_100km) * 100
                
                # Convert to requested unit
                if distance_unit == 'miles':
                    range_result = round(range_km / 1.60934, 2)
                    range_unit = 'miles'
                else:
                    range_result = round(range_km, 2)
                    range_unit = 'km'
            else:
                range_result = 0
                range_unit = distance_unit
                
        except (ValueError, TypeError, ZeroDivisionError):
            range_result = None
            range_unit = None
    
    context = {
        'converter': converter,
        'tool_name': tool_name,
        'result': result,
        'result_unit_symbol': result_unit_symbol,
        'range_result': range_result,
        'range_unit': range_unit,
        'fuel_display': fuel_display,
        'consumption_display': consumption_display,
    }
    
    # Use custom template for fuel consumption converter
    if tool_name == 'fuel-consumption':
        return render(request, 'converters/fuel_consumption.html', context)
    
    return render(request, 'converters/converter_tool.html', context)
