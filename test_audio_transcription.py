#!/usr/bin/env python3
"""
Test script to verify audio transcription implementation
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required imports work"""
    print("Testing imports...")
    try:
        from openai import OpenAI
        print("✓ OpenAI import successful")
    except ImportError as e:
        print(f"✗ OpenAI import failed: {e}")
        return False
    
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flipunit.settings')
        django.setup()
        print("✓ Django setup successful")
    except Exception as e:
        print(f"✗ Django setup failed: {e}")
        return False
    
    return True

def test_settings():
    """Test that settings are configured correctly"""
    print("\nTesting settings...")
    from django.conf import settings
    
    # Check if OPENAI_API_KEY setting exists
    if hasattr(settings, 'OPENAI_API_KEY'):
        print("✓ OPENAI_API_KEY setting exists")
        if settings.OPENAI_API_KEY:
            print(f"✓ OPENAI_API_KEY is set (length: {len(settings.OPENAI_API_KEY)})")
        else:
            print("⚠ OPENAI_API_KEY is not set in environment (this is OK if .env is not loaded)")
    else:
        print("✗ OPENAI_API_KEY setting not found")
        return False
    
    return True

def test_view_imports():
    """Test that view functions can be imported"""
    print("\nTesting view imports...")
    try:
        from text_converter import views
        print("✓ text_converter.views imported successfully")
        
        # Check if functions exist
        if hasattr(views, 'audio_transcription'):
            print("✓ audio_transcription view function exists")
        else:
            print("✗ audio_transcription view function not found")
            return False
        
        if hasattr(views, '_transcribe_audio'):
            print("✓ _transcribe_audio helper function exists")
        else:
            print("✗ _transcribe_audio helper function not found")
            return False
        
        if hasattr(views, '_get_audio_duration'):
            print("✓ _get_audio_duration helper function exists")
        else:
            print("✗ _get_audio_duration helper function not found")
            return False
        
        if hasattr(views, 'OPENAI_AVAILABLE'):
            print(f"✓ OPENAI_AVAILABLE flag: {views.OPENAI_AVAILABLE}")
        else:
            print("✗ OPENAI_AVAILABLE flag not found")
            return False
        
    except Exception as e:
        print(f"✗ View import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_urls():
    """Test that URLs are configured correctly"""
    print("\nTesting URL configuration...")
    try:
        from django.urls import reverse
        from django.conf import settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flipunit.settings')
        import django
        django.setup()
        
        # Try to reverse the URL
        try:
            url = reverse('text_converter:audio_transcription')
            print(f"✓ URL route exists: {url}")
        except Exception as e:
            print(f"✗ URL route not found: {e}")
            return False
        
    except Exception as e:
        print(f"✗ URL test failed: {e}")
        return False
    
    return True

def test_template():
    """Test that template exists"""
    print("\nTesting template...")
    template_path = os.path.join(
        os.path.dirname(__file__),
        'templates',
        'text_converter',
        'audio_transcription.html'
    )
    
    if os.path.exists(template_path):
        print(f"✓ Template exists: {template_path}")
        # Check file size
        size = os.path.getsize(template_path)
        print(f"  Template size: {size} bytes")
    else:
        print(f"✗ Template not found: {template_path}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Audio Transcription Implementation Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Settings", test_settings()))
    results.append(("View Functions", test_view_imports()))
    results.append(("URL Configuration", test_urls()))
    results.append(("Template", test_template()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        print("\nNext steps:")
        print("1. Make sure OPENAI_API_KEY is set in your .env file")
        print("2. Install openai package: pip install openai")
        print("3. Start the Django server and test the tool at:")
        print("   http://localhost:8000/text-converter/audio-transcription/")
    else:
        print("✗ Some tests failed. Please review the errors above.")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())

