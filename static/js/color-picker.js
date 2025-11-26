(function() {
    'use strict';
    
    // Color conversion utilities
    const ColorConverter = {
        // HEX to RGB
        hexToRgb(hex) {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? {
                r: parseInt(result[1], 16),
                g: parseInt(result[2], 16),
                b: parseInt(result[3], 16)
            } : null;
        },
        
        // RGB to HEX
        rgbToHex(r, g, b) {
            return "#" + [r, g, b].map(x => {
                const hex = x.toString(16);
                return hex.length === 1 ? "0" + hex : hex;
            }).join("");
        },
        
        // RGB to HSL
        rgbToHsl(r, g, b) {
            r /= 255;
            g /= 255;
            b /= 255;
            const max = Math.max(r, g, b);
            const min = Math.min(r, g, b);
            let h, s, l = (max + min) / 2;
            
            if (max === min) {
                h = s = 0;
            } else {
                const d = max - min;
                s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
                switch (max) {
                    case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
                    case g: h = ((b - r) / d + 2) / 6; break;
                    case b: h = ((r - g) / d + 4) / 6; break;
                }
            }
            
            return {
                h: Math.round(h * 360),
                s: Math.round(s * 100),
                l: Math.round(l * 100)
            };
        },
        
        // HSL to RGB
        hslToRgb(h, s, l) {
            h /= 360;
            s /= 100;
            l /= 100;
            let r, g, b;
            
            if (s === 0) {
                r = g = b = l;
            } else {
                const hue2rgb = (p, q, t) => {
                    if (t < 0) t += 1;
                    if (t > 1) t -= 1;
                    if (t < 1/6) return p + (q - p) * 6 * t;
                    if (t < 1/2) return q;
                    if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
                    return p;
                };
                
                const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
                const p = 2 * l - q;
                r = hue2rgb(p, q, h + 1/3);
                g = hue2rgb(p, q, h);
                b = hue2rgb(p, q, h - 1/3);
            }
            
            return {
                r: Math.round(r * 255),
                g: Math.round(g * 255),
                b: Math.round(b * 255)
            };
        },
        
        // RGB to CMYK
        rgbToCmyk(r, g, b) {
            r /= 255;
            g /= 255;
            b /= 255;
            const k = 1 - Math.max(r, g, b);
            if (k === 1) return { c: 0, m: 0, y: 0, k: 100 };
            const c = (1 - r - k) / (1 - k);
            const m = (1 - g - k) / (1 - k);
            const y = (1 - b - k) / (1 - k);
            return {
                c: Math.round(c * 100),
                m: Math.round(m * 100),
                y: Math.round(y * 100),
                k: Math.round(k * 100)
            };
        },
        
        // RGB to XYZ
        rgbToXyz(r, g, b) {
            r = r / 255;
            g = g / 255;
            b = b / 255;
            
            r = r > 0.04045 ? Math.pow((r + 0.055) / 1.055, 2.4) : r / 12.92;
            g = g > 0.04045 ? Math.pow((g + 0.055) / 1.055, 2.4) : g / 12.92;
            b = b > 0.04045 ? Math.pow((b + 0.055) / 1.055, 2.4) : b / 12.92;
            
            r *= 100;
            g *= 100;
            b *= 100;
            
            const x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375;
            const y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750;
            const z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041;
            
            return {
                x: Math.round(x * 10) / 10,
                y: Math.round(y * 10) / 10,
                z: Math.round(z * 10) / 10
            };
        },
        
        // XYZ to LAB
        xyzToLab(x, y, z) {
            x /= 95.047;
            y /= 100.000;
            z /= 108.883;
            
            x = x > 0.008856 ? Math.pow(x, 1/3) : (7.787 * x + 16/116);
            y = y > 0.008856 ? Math.pow(y, 1/3) : (7.787 * y + 16/116);
            z = z > 0.008856 ? Math.pow(z, 1/3) : (7.787 * z + 16/116);
            
            const l = (116 * y) - 16;
            const a = 500 * (x - y);
            const b = 200 * (y - z);
            
            return {
                l: Math.round(l),
                a: Math.round(a),
                b: Math.round(b)
            };
        },
        
        // RGB to LAB
        rgbToLab(r, g, b) {
            const xyz = this.rgbToXyz(r, g, b);
            return this.xyzToLab(xyz.x, xyz.y, xyz.z);
        },
        
        // RGB to LUV
        rgbToLuv(r, g, b) {
            const xyz = this.rgbToXyz(r, g, b);
            const x = xyz.x / 100;
            const y = xyz.y / 100;
            const z = xyz.z / 100;
            
            const u = (4 * x) / (x + 15 * y + 3 * z);
            const v = (9 * y) / (x + 15 * y + 3 * z);
            
            const yn = y > 0.008856 ? Math.pow(y, 1/3) : (7.787 * y + 16/116);
            const l = (116 * yn) - 16;
            
            const un = 0.197839824213;
            const vn = 0.468336302932;
            
            const u2 = 13 * l * (u - un);
            const v2 = 13 * l * (v - vn);
            
            return {
                l: Math.round(l),
                u: Math.round(u2),
                v: Math.round(v2)
            };
        },
        
        // RGB to HWB
        rgbToHwb(r, g, b) {
            const hsl = this.rgbToHsl(r, g, b);
            const w = Math.min(r, g, b) / 255;
            const bl = 1 - (Math.max(r, g, b) / 255);
            return {
                h: hsl.h,
                w: Math.round(w * 100),
                b: Math.round(bl * 100)
            };
        }
    };
    
    // Color name database (simplified - you can expand this)
    const colorNames = {
        '#780101': 'Japanese Maple',
        '#000000': 'Black',
        '#ffffff': 'White',
        '#ff0000': 'Red',
        '#00ff00': 'Green',
        '#0000ff': 'Blue',
        // Add more as needed
    };
    
    function getColorName(hex) {
        // Try exact match first
        if (colorNames[hex.toLowerCase()]) {
            return colorNames[hex.toLowerCase()];
        }
        
        // Try to find closest match (simplified)
        const rgb = ColorConverter.hexToRgb(hex);
        if (!rgb) return '';
        
        // Simple approximation - in production, use a proper color name library
        return '';
    }
    
    // Main Color Picker Class
    class ColorPicker {
        constructor() {
            // Start with a red color (like in the screenshot)
            this.hue = 0;
            this.saturation = 98;
            this.brightness = 24;
            this.isDragging = false;
            this.isHueDragging = false;
            
            this.init();
        }
        
        init() {
            this.colorSquareCanvas = document.getElementById('colorSquare');
            this.hueSliderCanvas = document.getElementById('hueSlider');
            this.colorHandle = document.getElementById('colorHandle');
            this.hueHandle = document.getElementById('hueHandle');
            this.hexInput = document.getElementById('hexInput');
            this.selectedColorDisplay = document.getElementById('selectedColorDisplay');
            this.colorHexLarge = document.getElementById('colorHexLarge');
            this.colorName = document.getElementById('colorName');
            this.colorFormatsGrid = document.getElementById('colorFormatsGrid');
            this.refreshBtn = document.getElementById('refreshBtn');
            
            if (!this.colorSquareCanvas) return;
            
            this.setupCanvases();
            this.setupEventListeners();
            this.updateColor();
        }
        
        setupCanvases() {
            // Setup color square
            const size = this.colorSquareCanvas.offsetWidth;
            this.colorSquareCanvas.width = size;
            this.colorSquareCanvas.height = size;
            this.drawColorSquare();
            
            // Setup hue slider
            const sliderWidth = this.hueSliderCanvas.offsetWidth;
            this.hueSliderCanvas.width = sliderWidth;
            this.hueSliderCanvas.height = 40;
            this.drawHueSlider();
        }
        
        drawColorSquare() {
            const ctx = this.colorSquareCanvas.getContext('2d');
            const size = this.colorSquareCanvas.width;
            
            // Draw saturation/brightness gradient
            for (let y = 0; y < size; y++) {
                for (let x = 0; x < size; x++) {
                    const s = (x / size) * 100;
                    const v = 100 - (y / size) * 100;
                    const rgb = ColorConverter.hslToRgb(this.hue, s, v);
                    ctx.fillStyle = `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`;
                    ctx.fillRect(x, y, 1, 1);
                }
            }
        }
        
        drawHueSlider() {
            const ctx = this.hueSliderCanvas.getContext('2d');
            const width = this.hueSliderCanvas.width;
            
            for (let x = 0; x < width; x++) {
                const hue = (x / width) * 360;
                const rgb = ColorConverter.hslToRgb(hue, 100, 50);
                ctx.fillStyle = `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`;
                ctx.fillRect(x, 0, 1, 40);
            }
        }
        
        setupEventListeners() {
            // Color square interaction
            this.colorSquareCanvas.addEventListener('mousedown', (e) => this.startDrag(e, true));
            this.colorSquareCanvas.addEventListener('mousemove', (e) => this.onDrag(e, true));
            this.colorSquareCanvas.addEventListener('mouseup', () => this.stopDrag());
            this.colorSquareCanvas.addEventListener('mouseleave', () => this.stopDrag());
            
            // Touch events
            this.colorSquareCanvas.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.startDrag(e.touches[0], true);
            });
            this.colorSquareCanvas.addEventListener('touchmove', (e) => {
                e.preventDefault();
                this.onDrag(e.touches[0], true);
            });
            this.colorSquareCanvas.addEventListener('touchend', () => this.stopDrag());
            
            // Hue slider interaction
            this.hueSliderCanvas.addEventListener('mousedown', (e) => this.startDrag(e, false));
            this.hueSliderCanvas.addEventListener('mousemove', (e) => this.onDrag(e, false));
            this.hueSliderCanvas.addEventListener('mouseup', () => this.stopDrag());
            this.hueSliderCanvas.addEventListener('mouseleave', () => this.stopDrag());
            
            // Touch events for hue slider
            this.hueSliderCanvas.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.startDrag(e.touches[0], false);
            });
            this.hueSliderCanvas.addEventListener('touchmove', (e) => {
                e.preventDefault();
                this.onDrag(e.touches[0], false);
            });
            this.hueSliderCanvas.addEventListener('touchend', () => this.stopDrag());
            
            // HEX input
            this.hexInput.addEventListener('input', (e) => {
                const hex = e.target.value;
                if (/^#[0-9A-Fa-f]{6}$/.test(hex)) {
                    this.setColorFromHex(hex);
                }
            });
            
            // Refresh button
            this.refreshBtn.addEventListener('click', () => {
                this.updateColor();
            });
            
            // Window resize
            window.addEventListener('resize', () => {
                this.setupCanvases();
                this.updateHandlePositions();
            });
        }
        
        startDrag(e, isColorSquare) {
            if (isColorSquare) {
                this.isDragging = true;
            } else {
                this.isHueDragging = true;
            }
            this.onDrag(e, isColorSquare);
        }
        
        onDrag(e, isColorSquare) {
            if (isColorSquare && this.isDragging) {
                const rect = this.colorSquareCanvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const size = this.colorSquareCanvas.width;
                
                this.saturation = Math.max(0, Math.min(100, (x / size) * 100));
                this.brightness = Math.max(0, Math.min(100, 100 - (y / size) * 100));
                this.updateColor();
            } else if (!isColorSquare && this.isHueDragging) {
                const rect = this.hueSliderCanvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const width = this.hueSliderCanvas.width;
                
                this.hue = Math.max(0, Math.min(360, (x / width) * 360));
                this.drawColorSquare();
                this.updateColor();
            }
        }
        
        stopDrag() {
            this.isDragging = false;
            this.isHueDragging = false;
        }
        
        setColorFromHex(hex) {
            const rgb = ColorConverter.hexToRgb(hex);
            if (!rgb) return;
            
            const hsl = ColorConverter.rgbToHsl(rgb.r, rgb.g, rgb.b);
            this.hue = hsl.h;
            this.saturation = hsl.s;
            this.brightness = hsl.l;
            
            this.drawColorSquare();
            this.updateColor();
        }
        
        updateHandlePositions() {
            const size = this.colorSquareCanvas.width;
            const x = (this.saturation / 100) * size;
            const y = (1 - this.brightness / 100) * size;
            this.colorHandle.style.left = x + 'px';
            this.colorHandle.style.top = y + 'px';
            
            const hueX = (this.hue / 360) * this.hueSliderCanvas.width;
            this.hueHandle.style.left = hueX + 'px';
        }
        
        updateColor() {
            const rgb = ColorConverter.hslToRgb(this.hue, this.saturation, this.brightness);
            const hex = ColorConverter.rgbToHex(rgb.r, rgb.g, rgb.b);
            
            // Update displays
            this.hexInput.value = hex.toUpperCase();
            this.colorHexLarge.textContent = hex.toUpperCase();
            
            // Update color display
            this.selectedColorDisplay.style.backgroundColor = hex;
            const isLight = (rgb.r + rgb.g + rgb.b) / 3 > 128;
            this.selectedColorDisplay.classList.toggle('light', isLight);
            
            // Update color name
            const name = getColorName(hex);
            this.colorName.textContent = name ? `≈ ${name}` : '';
            
            // Update formats
            this.updateFormats(rgb, hex);
            
            // Update handle positions
            this.updateHandlePositions();
        }
        
        updateFormats(rgb, hex) {
            const hsl = ColorConverter.rgbToHsl(rgb.r, rgb.g, rgb.b);
            const cmyk = ColorConverter.rgbToCmyk(rgb.r, rgb.g, rgb.b);
            const xyz = ColorConverter.rgbToXyz(rgb.r, rgb.g, rgb.b);
            const lab = ColorConverter.rgbToLab(rgb.r, rgb.g, rgb.b);
            const luv = ColorConverter.rgbToLuv(rgb.r, rgb.g, rgb.b);
            const hwb = ColorConverter.rgbToHwb(rgb.r, rgb.g, rgb.b);
            
            const formats = [
                { label: 'HEX', value: hex.toUpperCase() },
                { label: 'HSL', value: `${hsl.h}, ${hsl.s}, ${hsl.l}` },
                { label: 'RGB', value: `${rgb.r}, ${rgb.g}, ${rgb.b}` },
                { label: 'XYZ', value: `${xyz.x}, ${xyz.y}, ${xyz.z}` },
                { label: 'CMYK', value: `${cmyk.c}, ${cmyk.m}, ${cmyk.y}, ${cmyk.k}` },
                { label: 'LUV', value: `${luv.l}, ${luv.u}, ${luv.v}` },
                { label: 'LAB', value: `${lab.l}, ${lab.a}, ${lab.b}` },
                { label: 'HWB', value: `${hwb.h}, ${hwb.w}, ${hwb.b}` }
            ];
            
            this.colorFormatsGrid.innerHTML = formats.map(format => `
                <div class="format-item">
                    <div>
                        <div class="format-label">${format.label}</div>
                        <div class="format-value">${format.value}</div>
                    </div>
                    <button class="copy-btn" data-value="${format.value}" title="Copy">
                        📋
                    </button>
                </div>
            `).join('');
            
            // Add copy functionality
            this.colorFormatsGrid.querySelectorAll('.copy-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const value = btn.getAttribute('data-value');
                    navigator.clipboard.writeText(value).then(() => {
                        btn.textContent = '✓';
                        setTimeout(() => {
                            btn.textContent = '📋';
                        }, 1000);
                    });
                });
            });
        }
        
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            new ColorPicker();
        });
    } else {
        new ColorPicker();
    }
})();

