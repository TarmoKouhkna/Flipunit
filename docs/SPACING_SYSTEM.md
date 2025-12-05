# Unified Spacing System Documentation

## Overview

This document describes the unified horizontal spacing system implemented across the Flipunit project. The system provides consistent container widths, gap values, and list indentation to ensure a cohesive user experience.

## Table of Contents

1. [Container Classes](#container-classes)
2. [Gap Utility Classes](#gap-utility-classes)
3. [List Indentation](#list-indentation)
4. [Responsive Behavior](#responsive-behavior)
5. [Usage Guidelines](#usage-guidelines)
6. [Migration Guide](#migration-guide)

---

## Container Classes

Container classes control the maximum width and horizontal padding of content areas. All containers are centered using `margin: 0 auto`.

### Available Container Classes

#### `.container` (Default)
- **Max-width:** 1200px
- **Padding:** 1rem (16px) left/right
- **Usage:** Standard content width for most pages
- **Example:**
  ```html
  <div class="container">
    <!-- Main page content -->
  </div>
  ```

#### `.container-medium`
- **Max-width:** 1000px
- **Padding:** 1rem (16px) left/right
- **Usage:** Category grids, slightly narrower content
- **Example:**
  ```html
  <div class="container-medium">
    <!-- Category grid -->
  </div>
  ```

#### `.container-narrow`
- **Max-width:** 800px
- **Padding:** 1rem (16px) left/right
- **Usage:** Forms, search bars, focused content sections
- **Example:**
  ```html
  <form class="container-narrow">
    <!-- Search form -->
  </form>
  ```

#### `.container-extra-narrow`
- **Max-width:** 600px
- **Padding:** 1rem (16px) left/right
- **Usage:** Info sections, feedback forms, narrow content blocks
- **Example:**
  ```html
  <div class="container-extra-narrow">
    <!-- Info section -->
  </div>
  ```

### Container Selection Guide

| Content Type | Recommended Container |
|--------------|----------------------|
| Main page content | `.container` |
| Category grids | `.container-medium` |
| Search forms | `.container-narrow` |
| Converter forms | `.container-narrow` |
| Info sections | `.container-extra-narrow` |
| Feedback forms | `.container-extra-narrow` |

---

## Gap Utility Classes

Gap utility classes provide standardized spacing between flex and grid items. Use these classes instead of inline `gap` styles.

### Available Gap Classes

| Class | Value | Pixels | Usage |
|------|-------|--------|-------|
| `.gap-xs` | 0.5rem | 8px | Tight spacing (checkboxes, small buttons) |
| `.gap-sm` | 0.75rem | 12px | Small spacing (form elements) |
| `.gap-md` | 1rem | 16px | Medium spacing (grid items, form groups) |
| `.gap-lg` | 1.5rem | 24px | Large spacing (sections, card groups) |
| `.gap-xl` | 2rem | 32px | Extra large spacing (default grid gap) |

### Usage Examples

#### Flex Container
```html
<div style="display: flex;" class="gap-xs">
  <button>Button 1</button>
  <button>Button 2</button>
</div>
```

#### Grid Container
```html
<div class="grid grid-2 gap-md">
  <div>Item 1</div>
  <div>Item 2</div>
</div>
```

### Gap Selection Guide

| Element Type | Recommended Gap |
|--------------|-----------------|
| Checkboxes/radio buttons | `.gap-xs` |
| Form input groups | `.gap-sm` or `.gap-md` |
| Grid items | `.gap-md` or `.gap-xl` |
| Section spacing | `.gap-lg` or `.gap-xl` |
| Default grid | `.gap-xl` (2rem) |

---

## List Indentation

The `.list-indent` class provides standardized indentation for lists, replacing inline `padding-left` or `margin-left` styles.

### Usage

```html
<!-- Unordered list -->
<ul class="list-indent">
  <li>Item 1</li>
  <li>Item 2</li>
</ul>

<!-- Ordered list -->
<ol class="list-indent">
  <li>Item 1</li>
  <li>Item 2</li>
</ol>
```

### Implementation Details

- **Indentation:** 1.5rem (24px)
- **For `<ul>` and `<ol>`:** Uses `margin-left: 1.5rem` with `padding-left: 0`
- **For other elements:** Uses `padding-left: 1.5rem`

---

## Responsive Behavior

All container classes and utilities adapt to smaller screens:

### Mobile Breakpoint (≤ 480px)

**Container Padding:**
- Desktop: `1rem` (16px) left/right
- Mobile: `0.75rem` (12px) left/right

**Applied to:**
- `.container`
- `.container-medium`
- `.container-narrow`
- `.container-extra-narrow`

### Example

```css
/* Desktop */
.container {
  padding: 0 1rem;  /* 16px */
}

/* Mobile (≤ 480px) */
@media (max-width: 480px) {
  .container {
    padding: 0 0.75rem;  /* 12px */
  }
}
```

---

## Usage Guidelines

### Best Practices

1. **Always use container classes** instead of inline `max-width` styles
2. **Use gap utility classes** instead of inline `gap` styles
3. **Use `.list-indent`** instead of inline `padding-left` or `margin-left` for lists
4. **Maintain consistency** - use the same container class for similar content types
5. **Avoid mixing** inline styles with utility classes for the same property

### Anti-Patterns (Don't Do This)

❌ **Don't use inline max-width:**
```html
<div style="max-width: 800px; margin: 0 auto;">
  <!-- Use .container-narrow instead -->
</div>
```

❌ **Don't use inline gap:**
```html
<div style="display: flex; gap: 0.5rem;">
  <!-- Use class="gap-xs" instead -->
</div>
```

❌ **Don't use inline list indentation:**
```html
<ul style="padding-left: 1.5rem;">
  <!-- Use class="list-indent" instead -->
</ul>
```

### Correct Patterns (Do This)

✅ **Use container classes:**
```html
<div class="container-narrow">
  <!-- Content -->
</div>
```

✅ **Use gap utility classes:**
```html
<div style="display: flex;" class="gap-xs">
  <!-- Items -->
</div>
```

✅ **Use list-indent class:**
```html
<ul class="list-indent">
  <!-- Items -->
</ul>
```

---

## Migration Guide

### Migrating from Inline Styles

#### Step 1: Replace Container Styles

**Before:**
```html
<div style="max-width: 800px; margin: 0 auto;">
```

**After:**
```html
<div class="container-narrow">
```

#### Step 2: Replace Gap Styles

**Before:**
```html
<div style="display: flex; gap: 0.5rem;">
```

**After:**
```html
<div style="display: flex;" class="gap-xs">
```

#### Step 3: Replace List Indentation

**Before:**
```html
<ul style="padding-left: 1.5rem;">
```

**After:**
```html
<ul class="list-indent">
```

### Common Migration Patterns

| Inline Style | Replacement |
|--------------|-------------|
| `max-width: 1200px; margin: 0 auto;` | `.container` |
| `max-width: 1000px; margin: 0 auto;` | `.container-medium` |
| `max-width: 800px; margin: 0 auto;` | `.container-narrow` |
| `max-width: 600px; margin: 0 auto;` | `.container-extra-narrow` |
| `gap: 0.5rem` | `.gap-xs` |
| `gap: 1rem` | `.gap-md` |
| `gap: 1.5rem` | `.gap-lg` |
| `gap: 2rem` | `.gap-xl` |
| `padding-left: 1.5rem` (lists) | `.list-indent` |
| `margin-left: 1.5rem` (lists) | `.list-indent` |

---

## File Locations

- **CSS Definitions:** `static/css/style.css`
  - Container classes: Lines 61-85
  - Gap utilities: Lines 87-93
  - List indentation: Lines 95-103
  - Responsive overrides: Lines 585-590

---

## Examples

### Complete Page Example

```html
{% extends 'base.html' %}

{% block content %}
<!-- Main content uses standard container -->
<div class="container">
  <h1>Page Title</h1>
  
  <!-- Search form uses narrow container -->
  <form class="container-narrow">
    <div style="display: flex;" class="gap-xs">
      <input type="search" class="form-control">
      <button type="submit">Search</button>
    </div>
  </form>
  
  <!-- Category grid uses medium container -->
  <div class="container-medium">
    <div class="grid grid-2 gap-xl">
      <div class="category-card">Category 1</div>
      <div class="category-card">Category 2</div>
    </div>
  </div>
  
  <!-- Info section uses extra narrow container -->
  <div class="container-extra-narrow">
    <h2>Information</h2>
    <ul class="list-indent">
      <li>Point 1</li>
      <li>Point 2</li>
    </ul>
  </div>
</div>
{% endblock %}
```

---

## Maintenance

### Adding New Container Sizes

If you need a new container size, add it to `static/css/style.css` following the existing pattern:

```css
.container-custom {
    max-width: 900px;  /* Your custom width */
    margin: 0 auto;
    padding: 0 1rem;
    width: 100%;
}

/* Don't forget responsive override */
@media (max-width: 480px) {
    .container-custom {
        padding: 0 0.75rem;
    }
}
```

### Adding New Gap Sizes

If you need a new gap size, add it to `static/css/style.css`:

```css
.gap-xxl { gap: 3rem; }  /* 48px - for very large spacing */
```

---

## Support

For questions or issues with the spacing system, refer to this documentation or check the implementation in `static/css/style.css`.

---

**Last Updated:** 2024
**Version:** 1.0
