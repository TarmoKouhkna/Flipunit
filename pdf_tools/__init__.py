# Patch pdf_to_flipbook function on module import
def _patch_flipbook():
    try:
        import sys
        if 'pdf_tools.views' in sys.modules:
            views = sys.modules['pdf_tools.views']
            if not hasattr(views, 'pdf_to_flipbook'):
                # Read function from file
                import os
                views_path = os.path.join(os.path.dirname(__file__), 'views.py')
                with open(views_path, 'r') as f:
                    content = f.read()
                
                # Find the LAST occurrence (the one we appended)
                start = content.rfind('def pdf_to_flipbook(request):')
                if start >= 0:
                    func_code = content[start:]
                    # Execute in views namespace
                    exec(func_code, views.__dict__)
    except Exception:
        pass  # Silently fail if patch doesn't work

# Call patch when module is imported
_patch_flipbook()

