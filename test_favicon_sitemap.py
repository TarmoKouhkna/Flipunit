#!/usr/bin/env python3
"""
Test script to verify favicon and sitemap setup.

This script checks:
1. Favicon files exist
2. Favicon view code is correct
3. Sitemap file structure
"""
import os
from pathlib import Path

def test_favicon_files():
    """Test that favicon files exist"""
    print("=" * 60)
    print("Testing Favicon Files")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    images_dir = project_root / 'static' / 'images'
    
    required_files = [
        'favicon.ico',
        'favicon.png',
        'favicon.svg',
        'apple-touch-icon.png'
    ]
    
    all_exist = True
    for filename in required_files:
        filepath = images_dir / filename
        exists = filepath.exists()
        if exists:
            size = filepath.stat().st_size
            status = "✓"
            print(f"{status} {filename:25} EXISTS ({size:,} bytes)")
        else:
            status = "✗"
            print(f"{status} {filename:25} MISSING")
            all_exist = False
    
    return all_exist


def test_favicon_view():
    """Test that favicon view code exists and is correct"""
    print("\n" + "=" * 60)
    print("Testing Favicon View")
    print("=" * 60)
    
    views_file = Path(__file__).parent / 'flipunit' / 'views.py'
    
    if not views_file.exists():
        print("✗ views.py not found")
        return False
    
    with open(views_file, 'r') as f:
        content = f.read()
    
    checks = {
        'favicon_view function': 'def favicon_view' in content,
        'HttpResponse import': 'from django.http import HttpResponse' in content,
        'os import': 'import os' in content,
        'settings import': 'from django.conf import settings' in content,
        'favicon.ico path check': 'favicon.ico' in content and 'STATICFILES_DIRS' in content,
    }
    
    all_pass = True
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"{status} {check_name}")
        if not passed:
            all_pass = False
    
    return all_pass


def test_favicon_url():
    """Test that favicon URL route exists"""
    print("\n" + "=" * 60)
    print("Testing Favicon URL Route")
    print("=" * 60)
    
    urls_file = Path(__file__).parent / 'flipunit' / 'urls.py'
    
    if not urls_file.exists():
        print("✗ urls.py not found")
        return False
    
    with open(urls_file, 'r') as f:
        content = f.read()
    
    checks = {
        'favicon.ico route': "path('favicon.ico'" in content or "path(\"favicon.ico\"" in content,
        'favicon_view reference': 'favicon_view' in content or 'views.favicon_view' in content,
    }
    
    all_pass = True
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"{status} {check_name}")
        if not passed:
            all_pass = False
    
    return all_pass


def test_sitemap_structure():
    """Test that sitemap file exists and has correct structure"""
    print("\n" + "=" * 60)
    print("Testing Sitemap Structure")
    print("=" * 60)
    
    sitemap_file = Path(__file__).parent / 'flipunit' / 'sitemaps.py'
    
    if not sitemap_file.exists():
        print("✗ sitemaps.py not found")
        return False
    
    with open(sitemap_file, 'r') as f:
        content = f.read()
    
    checks = {
        'StaticViewSitemap class': 'class StaticViewSitemap' in content,
        'items method': 'def items(self)' in content,
        'location method': 'def location(self' in content,
        'priority set': 'priority =' in content,
        'changefreq set': 'changefreq =' in content,
        'protocol set': 'protocol =' in content,
    }
    
    all_pass = True
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"{status} {check_name}")
        if not passed:
            all_pass = False
    
    # Count URLs in sitemap
    if 'def items(self)' in content:
        # Simple count of return items
        items_section = content[content.find('def items(self)'):content.find('def location', content.find('def items(self)'))]
        url_count = items_section.count("'") // 2  # Rough estimate
        print(f"\n  Estimated URLs in sitemap: ~{url_count}")
    
    return all_pass


def test_html_favicon_links():
    """Test that HTML has proper favicon links"""
    print("\n" + "=" * 60)
    print("Testing HTML Favicon Links")
    print("=" * 60)
    
    base_template = Path(__file__).parent / 'templates' / 'base.html'
    
    if not base_template.exists():
        print("✗ base.html not found")
        return False
    
    with open(base_template, 'r') as f:
        content = f.read()
    
    checks = {
        'SVG favicon link': 'favicon.svg' in content and 'image/svg+xml' in content,
        'PNG favicon link': 'favicon.png' in content and 'image/png' in content,
        'ICO favicon link': 'favicon.ico' in content and 'image/x-icon' in content,
        'Apple touch icon': 'apple-touch-icon' in content,
    }
    
    all_pass = True
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"{status} {check_name}")
        if not passed:
            all_pass = False
    
    return all_pass


def main():
    print("Favicon and Sitemap Verification Test")
    print("=" * 60)
    
    results = {
        'Favicon Files': test_favicon_files(),
        'Favicon View Code': test_favicon_view(),
        'Favicon URL Route': test_favicon_url(),
        'Sitemap Structure': test_sitemap_structure(),
        'HTML Favicon Links': test_html_favicon_links(),
    }
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! Setup looks good.")
        print("\nNext steps:")
        print("1. Deploy the changes to production")
        print("2. Verify https://flipunit.eu/favicon.ico is accessible")
        print("3. Request indexing in Google Search Console")
        print("4. Wait for Google to crawl and update (may take days/weeks)")
        return 0
    else:
        print("✗ Some tests failed. Please review the issues above.")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
