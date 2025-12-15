# Per-Image Rectangular Frequency Mixing API

## Overview
The API now supports **per-image independent rectangular frequency region selection** with binary masking.

## Key Changes

### ✅ What Changed

1. **Removed**: `images_base64` from request body
2. **Removed**: Single `rectangle` parameter
3. **Added**: `rectangles: List[Optional[Dict]]` - one per image

### ✅ Backend Responsibilities

- **FourierTransformer.mix_components()**:
  - Accepts `components_list`, `weights`, `rectangles`
  - No dependency on `self.image_data` or `self.MAX_IMAGES`
  - Creates per-image binary masks
  - Applies masks element-wise
  - Performs weighted mixing
  - Returns IFFT result

- **ImageManager.mix_ft_components()**:
  - Coordinator only
  - Collects FT components
  - Passes everything to FourierTransformer
  - No mask creation here

## API Endpoint: POST /api/ft/mix

### Request Body

```json
{
  "weights": [0.25, 0.25, 0.25, 0.25],
  "rectangles": [
    {"x": 100, "y": 100, "width": 200, "height": 150, "type": "inner"},
    {"x": 50, "y": 75, "width": 250, "height": 200, "type": "inner"},
    {"x": 120, "y": 110, "width": 180, "height": 160, "type": "outer"},
    null
  ],
  "component_mode": "magnitude_phase",
  "preserve_energy": false
}
```

### Request Fields

#### weights (Required)
- **Type**: `List[float]` with exactly 4 values
- **Description**: Weight for each image
- **Example**: `[1, 1, 1, 1]` or `[0.25, 0.25, 0.25, 0.25]`

#### rectangles (Required)
- **Type**: `List[Optional[RectangleRegion]]` with exactly 4 elements
- **Description**: Rectangle definition per image
- **null means**: Use full region (no mask) for that image

#### RectangleRegion
```json
{
  "x": 100,
  "y": 100,
  "width": 200,
  "height": 150,
  "type": "inner"
}
```

**Fields**:
- `x` (int, ≥ 0): Top-left X coordinate
- `y` (int, ≥ 0): Top-left Y coordinate  
- `width` (int, > 0): Rectangle width
- `height` (int, > 0): Rectangle height
- `type` (string): `"inner"` or `"outer"`
  - **inner**: 1 inside rectangle, 0 outside
  - **outer**: 0 inside rectangle, 1 outside

#### component_mode (Optional)
- **Type**: `string`
- **Options**: `"magnitude_phase"` or `"real_imaginary"`
- **Default**: `"magnitude_phase"`

#### preserve_energy (Optional)
- **Type**: `boolean`
- **Default**: `false`

### Response

```json
{
  "success": true,
  "base64": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
  "shape": {
    "height": 512,
    "width": 512
  },
  "weights": [0.25, 0.25, 0.25, 0.25],
  "mode": "magnitude_phase",
  "preserve_energy": false,
  "rectangles": [
    {"x": 100, "y": 100, "width": 200, "height": 150, "type": "inner"},
    ...
  ],
  "raw_stats": {
    "min": -50.2,
    "max": 200.5,
    "mean": 85.3,
    "std": 32.1
  }
}
```

## Usage Examples

### Example 1: Per-Image Rectangles

```bash
curl -X POST http://localhost:8000/api/ft/mix \
  -H "Content-Type: application/json" \
  -d '{
    "weights": [1, 1, 1, 1],
    "rectangles": [
      {"x": 100, "y": 100, "width": 200, "height": 200, "type": "inner"},
      {"x": 50, "y": 150, "width": 300, "height": 180, "type": "inner"},
      {"x": 120, "y": 80, "width": 250, "height": 220, "type": "inner"},
      {"x": 75, "y": 110, "width": 280, "height": 190, "type": "inner"}
    ],
    "component_mode": "magnitude_phase",
    "preserve_energy": false
  }'
```

### Example 2: Mixed Inner/Outer

```bash
curl -X POST http://localhost:8000/api/ft/mix \
  -H "Content-Type: application/json" \
  -d '{
    "weights": [1, 1, 0, 0],
    "rectangles": [
      {"x": 100, "y": 100, "width": 300, "height": 300, "type": "inner"},
      {"x": 100, "y": 100, "width": 300, "height": 300, "type": "outer"},
      null,
      null
    ],
    "component_mode": "magnitude_phase"
  }'
```

### Example 3: Some Full Regions

```bash
curl -X POST http://localhost:8000/api/ft/mix \
  -H "Content-Type: application/json" \
  -d '{
    "weights": [0.5, 0.5, 0, 0],
    "rectangles": [
      {"x": 110, "y": 120, "width": 180, "height": 160, "type": "inner"},
      null,
      null,
      null
    ],
    "component_mode": "real_imaginary"
  }'
```

## Frontend Integration

### JavaScript Example

```javascript
async function mixImages() {
  const response = await fetch('http://localhost:8000/api/ft/mix', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      weights: [
        parseFloat(slider0.value),
        parseFloat(slider1.value),
        parseFloat(slider2.value),
        parseFloat(slider3.value)
      ],
      rectangles: [
        rectangle0 ? {
          x: rectangle0.x,
          y: rectangle0.y,
          width: rectangle0.width,
          height: rectangle0.height,
          type: regionType0.value
        } : null,
        rectangle1 ? {
          x: rectangle1.x,
          y: rectangle1.y,
          width: rectangle1.width,
          height: rectangle1.height,
          type: regionType1.value
        } : null,
        rectangle2 ? {
          x: rectangle2.x,
          y: rectangle2.y,
          width: rectangle2.width,
          height: rectangle2.height,
          type: regionType2.value
        } : null,
        rectangle3 ? {
          x: rectangle3.x,
          y: rectangle3.y,
          width: rectangle3.width,
          height: rectangle3.height,
          type: regionType3.value
        } : null
      ],
      component_mode: componentMode.value,
      preserve_energy: preserveEnergy.checked
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    displayMixedImage(result.base64);
    console.log('Stats:', result.raw_stats);
  } else {
    console.error('Error:', result.error || result.detail);
  }
}
```

## Implementation Details

### Binary Mask Creation

For rectangle at (x, y) with (width, height):

```python
mask = np.zeros((h, w), dtype=bool)
mask[y1:y2, x1:x2] = True

if type == "inner":
    return mask  # 1 inside, 0 outside
else:
    return ~mask  # 0 inside, 1 outside
```

### Mixing Algorithm

```
For each image i:
  1. Extract FT components (magnitude/phase or real/imaginary)
  2. Create mask from rectangle_i
  3. Apply: masked_FT_i = FT_i × mask_i
  4. Weight: weighted_FT_i = weight_i × masked_FT_i
  5. Accumulate: mixed_FT += weighted_FT_i

Final: result = IFFT(mixed_FT)
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Weights must have 4 values` | Wrong count | Provide exactly 4 weights |
| `Rectangles must have 4 values` | Wrong count | Provide exactly 4 rectangles (or null) |
| `Image N missing FT components` | FT not calculated | Call `/api/ft/calculate/{image_id}` first |
| `FT component shapes differ` | Images not resized | Call `/api/resize` |
| `Weights sum to zero` | All zeros | Provide non-zero weights |

## Workflow

1. **Upload 4 images**: `POST /api/upload/{image_id}`
2. **Calculate FT**: `POST /api/ft/calculate-all`
3. **Mix with rectangles**: `POST /api/ft/mix`

## Testing

```bash
# Health check
curl http://localhost:8000/api/health

# Upload images
curl -X POST http://localhost:8000/api/upload/0 -F "file=@image0.jpg"
curl -X POST http://localhost:8000/api/upload/1 -F "file=@image1.jpg"
curl -X POST http://localhost:8000/api/upload/2 -F "file=@image2.jpg"
curl -X POST http://localhost:8000/api/upload/3 -F "file=@image3.jpg"

# Calculate FT
curl -X POST http://localhost:8000/api/ft/calculate-all

# Mix
curl -X POST http://localhost:8000/api/ft/mix \
  -H "Content-Type: application/json" \
  -d '{
    "weights": [1,1,1,1],
    "rectangles": [
      {"x":100,"y":100,"width":200,"height":200,"type":"inner"},
      null, null, null
    ],
    "component_mode": "magnitude_phase"
  }'
```
