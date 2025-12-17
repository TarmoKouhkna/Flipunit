# Fuel Range Calculator Feature

## Overview

Added a **Driving Range Calculator** to the Fuel Consumption converter that calculates how far you can drive with a given amount of fuel based on your car's consumption rate.

## Location

URL: `/converters/fuel-consumption/`

The page now has TWO sections:
1. **Unit Converter** - Convert between L/100km, MPG, km/L, etc.
2. **Driving Range Calculator** - Calculate driving distance with given fuel amount

## How It Works

### User Inputs

1. **Fuel Amount** - How much fuel you have (e.g., 50)
2. **Fuel Unit** - What unit (Liters, Gallons US, Gallons UK)
3. **Fuel Consumption** - Your car's consumption rate (e.g., 7)
4. **Consumption Unit** - What unit (L/100km, km/L, MPG US, MPG UK)
5. **Display Range In** - Output unit (Kilometers or Miles)

### Calculation Process

1. Convert fuel amount to liters (base unit)
2. Convert consumption rate to L/100km (base unit)
3. Calculate range: `(fuel_in_liters / L_per_100km) × 100`
4. Convert result to requested output unit (km or miles)

### Formula

```
Range (km) = (Fuel Amount in Liters / L per 100km) × 100
```

## Real-World Examples

### Example 1: Your Question! 🚗
**Question**: Car consumes 7 L/100km, just fueled with 50L, how far can I drive?

**Input**:
- Fuel Amount: 50
- Fuel Unit: Liters
- Consumption: 7
- Consumption Unit: L/100km
- Output: Kilometers

**Result**: **714.29 km**

**Explanation**: 
- With 7 L/100km, you use 7 liters per 100 km
- With 50 liters: 50 ÷ 7 = 7.14 "hundreds of km"
- 7.14 × 100 = 714 km

---

### Example 2: American Car
**Scenario**: 15-gallon tank, car does 30 MPG

**Input**:
- Fuel Amount: 15
- Fuel Unit: Gallons (US)
- Consumption: 30
- Consumption Unit: MPG (US)
- Output: Miles

**Result**: **450 miles**

---

### Example 3: Efficient European Car
**Scenario**: 60-liter tank, very efficient car at 4.5 L/100km

**Input**:
- Fuel Amount: 60
- Fuel Unit: Liters
- Consumption: 4.5
- Consumption Unit: L/100km
- Output: Kilometers

**Result**: **1,333 km**

---

### Example 4: Using km/L
**Scenario**: 40-liter tank, car does 18 km per liter

**Input**:
- Fuel Amount: 40
- Fuel Unit: Liters
- Consumption: 18
- Consumption Unit: km/L
- Output: Kilometers

**Result**: **720 km**

**Explanation**:
- 18 km/L = 5.56 L/100km (100 ÷ 18)
- Range = (40 ÷ 5.56) × 100 = 720 km

## Conversion Reference

### Fuel Units to Liters
- 1 Gallon (US) = 3.78541 liters
- 1 Gallon (UK) = 4.54609 liters
- 1 Liter = 1 liter

### Consumption to L/100km
- **L/100km**: Already in base unit
- **km/L**: `L/100km = 100 / km_per_L`
- **MPG (US)**: `L/100km = 235.215 / MPG`
- **MPG (UK)**: `L/100km = 282.481 / MPG`

### Distance Conversion
- 1 kilometer = 0.621371 miles
- 1 mile = 1.60934 kilometers

## Technical Implementation

### Files
- `converters/views.py` - Backend calculation logic (lines 330-398)
- `templates/converters/fuel_consumption.html` - Custom UI with range calculator

### Key Code Logic

```python
# Convert fuel to liters
if fuel_unit == 'gallon_us':
    fuel_in_liters = fuel_amount * 3.78541
elif fuel_unit == 'gallon_uk':
    fuel_in_liters = fuel_amount * 4.54609
else:
    fuel_in_liters = fuel_amount

# Convert consumption to L/100km
if consumption_unit == 'kilometer per liter':
    l_per_100km = 100 / consumption_value
elif consumption_unit == 'mile per gallon (US)':
    l_per_100km = 235.215 / consumption_value
# ... etc

# Calculate range
range_km = (fuel_in_liters / l_per_100km) * 100

# Convert to miles if requested
if distance_unit == 'miles':
    range_result = range_km / 1.60934
```

## User Experience Features

1. ✅ **Clear Labels** - Every field explains what to enter
2. ✅ **Flexible Units** - Support for metric and imperial
3. ✅ **Detailed Result** - Shows full explanation: "With X fuel at Y consumption, you can drive Z"
4. ✅ **Separate Forms** - Unit conversion and range calculation don't interfere
5. ✅ **Error Handling** - Handles zero values and edge cases gracefully

## Testing

All calculations verified:
```
Test 1: 50L at 7 L/100km = 714.29 km ✓
Test 2: 15 US gal at 30 MPG = 450.00 mi ✓
Test 3: 40L at 18 km/L = 720.00 km ✓
```

## Benefits

### For Users
- **Practical tool** - Answers real-world question: "How far can I drive?"
- **Trip planning** - Calculate if you have enough fuel for a journey
- **Fuel budgeting** - Understand your car's range capabilities
- **Cross-unit support** - Works with any fuel/consumption unit combination

### For Site
- **Unique feature** - Most converters only do unit conversion, not range calculation
- **Higher engagement** - Users spend more time on the page
- **Return visits** - Practical tool people bookmark and reuse
- **SEO boost** - Targets queries like "fuel range calculator", "how far can I drive"

## Future Enhancements (Optional)

Could add:
- [ ] Save favorite car profiles (consumption rates)
- [ ] Multiple fuel stops calculation
- [ ] Cost calculator (fuel price × consumption)
- [ ] Compare two vehicles side-by-side
- [ ] Real-time fuel price integration
- [ ] Trip planner with distance input
