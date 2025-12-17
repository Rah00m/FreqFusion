# Dual Weights API Documentation

## Overview
The API now supports **dual weights per image** - one weight for each frequency component.

## Weight Structure

### For `magnitude_phase` mode:
```json
{
  "weights": [
    [mag_weight_0, phase_weight_0],
    [mag_weight_1, phase_weight_1],
    [mag_weight_2, phase_weight_2],
    [mag_weight_3, phase_weight_3]
  ],
  "component_mode": "magnitude_phase"
}
```

### For `real_imaginary` mode:
```json
{
  "weights": [
    [real_weight_0, imag_weight_0],
    [real_weight_1, imag_weight_1],
    [real_weight_2, imag_weight_2],
    [real_weight_3, imag_weight_3]
  ],
  "component_mode": "real_imaginary"
}
```

## Mixing Formula

### Magnitude/Phase Mode
For each image i with weights `[mag_w, phase_w]`:
```python
magnitude_i = comp.magnitude_raw ** mag_w
phase_i = comp.phase_raw ** phase_w
FT_i = magnitude_i × exp(j × phase_i)
```

### Real/Imaginary Mode
For each image i with weights `[real_w, imag_w]`:
```python
FT_i = (comp.real_raw ** real_w) + j × (comp.imaginary_raw ** imag_w)
```

## Complete API Request Example

```json
{
  "weights": [
    [1.0, 0.5],
    [0.8, 1.0],
    [1.2, 0.7],
    [0.9, 1.1]
  ],
  "rectangles": [
    {"x": 100, "y": 100, "width": 200, "height": 200, "type": "inner"},
    {"x": 50, "y": 150, "width": 300, "height": 180, "type": "inner"},
    null,
    {"x": 75, "y": 110, "width": 280, "height": 190, "type": "outer"}
  ],
  "component_mode": "magnitude_phase",
  "preserve_energy": false
}
```

## cURL Example

```bash
curl -X POST http://localhost:8000/api/ft/mix \
  -H "Content-Type: application/json" \
  -d '{
    "weights": [[1.0, 0.5], [0.8, 1.0], [1.2, 0.7], [0.9, 1.1]],
    "rectangles": [
      {"x": 100, "y": 100, "width": 200, "height": 200, "type": "inner"},
      null,
      null,
      null
    ],
    "component_mode": "magnitude_phase"
  }'
```

## JavaScript/Frontend Example

```javascript
async function mixImages() {
  const response = await fetch('http://localhost:8000/api/ft/mix', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      weights: [
        [magnitudeSlider0.value, phaseSlider0.value],
        [magnitudeSlider1.value, phaseSlider1.value],
        [magnitudeSlider2.value, phaseSlider2.value],
        [magnitudeSlider3.value, phaseSlider3.value]
      ],
      rectangles: [
        rect0 ? {
          x: rect0.x,
          y: rect0.y,
          width: rect0.width,
          height: rect0.height,
          type: 'inner'
        } : null,
        rect1 ? {
          x: rect1.x,
          y: rect1.y,
          width: rect1.width,
          height: rect1.height,
          type: 'inner'
        } : null,
        rect2 ? {
          x: rect2.x,
          y: rect2.y,
          width: rect2.width,
          height: rect2.height,
          type: 'inner'
        } : null,
        rect3 ? {
          x: rect3.x,
          y: rect3.y,
          width: rect3.width,
          height: rect3.height,
          type: 'inner'
        } : null
      ],
      component_mode: componentMode.value,
      preserve_energy: false
    })
  });
  
  const result = await response.json();
  if (result.success) {
    displayImage(result.base64);
  }
}
```

## Validation Rules

1. **weights** must be a list of exactly **4** sublists
2. Each sublist must contain exactly **2** float values
3. **rectangles** must be a list of exactly **4** elements (can be null)
4. **component_mode** must be either `"magnitude_phase"` or `"real_imaginary"`

## Error Examples

### Wrong number of weight pairs
```json
{
  "weights": [[1.0, 0.5], [0.8, 1.0]],  // ❌ Only 2, need 4
  ...
}
```
Response: `400 Bad Request - "Weights must have 4 values"`

### Wrong number of values in weight pair
```json
{
  "weights": [[1.0], [0.8, 1.0], [1.2, 0.7], [0.9, 1.1]],  // ❌ First has 1 value
  ...
}
```
Response: `400 Bad Request - "Weight for image 0 must have exactly 2 values"`

### Missing FT components
```json
// If image 2 hasn't had calculate_ft called
```
Response: `400 Bad Request - "Image 2 missing FT components"`

## Use Cases

### Example 1: Emphasize Magnitude, Reduce Phase
```json
{
  "weights": [
    [2.0, 0.5],  // Strong magnitude, weak phase
    [1.5, 0.7],
    [1.8, 0.3],
    [2.2, 0.4]
  ],
  "component_mode": "magnitude_phase"
}
```

### Example 2: Real/Imaginary Balance
```json
{
  "weights": [
    [1.0, 1.0],  // Equal real and imaginary
    [1.5, 0.5],  // More real, less imaginary
    [0.5, 1.5],  // Less real, more imaginary
    [1.0, 1.0]
  ],
  "component_mode": "real_imaginary"
}
```

### Example 3: Single Component Only
```json
{
  "weights": [
    [1.0, 0.0],  // Magnitude only, no phase
    [1.0, 0.0],
    [1.0, 0.0],
    [1.0, 0.0]
  ],
  "component_mode": "magnitude_phase"
}
```

## Response Format

```json
{
  "success": true,
  "base64": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
  "shape": {
    "height": 512,
    "width": 512
  },
  "weights": [[1.0, 0.5], [0.8, 1.0], [1.2, 0.7], [0.9, 1.1]],
  "mode": "magnitude_phase",
  "preserve_energy": false,
  "rectangles": [...],
  "raw_stats": {
    "min": -50.2,
    "max": 200.5,
    "mean": 85.3,
    "std": 32.1
  }
}
```
