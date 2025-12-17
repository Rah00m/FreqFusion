"""
FastAPI app exposing endpoints to test the Fourier Transformer pipeline via Postman.
Endpoints: upload, calculate FT, get component, mix, cache info.
"""

import json
import os
from typing import Dict, List, Optional
import uuid 
from typing import Literal

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .image_manager import ImageManager
from .utils import JsonEncoder


app = FastAPI(
    title="Fourier Transform Mixer API",
    description="Upload images, compute Fourier components, and mix them",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

image_manager = ImageManager()


def json_response(data: Dict):
    return JSONResponse(content=json.loads(json.dumps(data, cls=JsonEncoder)))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Prevent UnicodeDecodeError by scrubbing binary content in validation errors."""
    def scrub(obj):
        if isinstance(obj, bytes):
            return f"<binary {len(obj)} bytes>"
        if isinstance(obj, list):
            return [scrub(x) for x in obj]
        if isinstance(obj, dict):
            return {k: scrub(v) for k, v in obj.items()}
        return obj

    sanitized = scrub(exc.errors())
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(sanitized)})


class RectangleRegion(BaseModel):
    """Rectangle definition for frequency domain selection."""
    x: int = Field(..., ge=0, description="Top-left X coordinate")
    y: int = Field(..., ge=0, description="Top-left Y coordinate")
    width: int = Field(..., gt=0, description="Rectangle width")
    height: int = Field(..., gt=0, description="Rectangle height")
    type: str = Field("inner", pattern="^(inner|outer)$", description="inner or outer")


class WeightPair(BaseModel):
    """A pair of weights for a single image's two components."""
    weights: List[float] = Field(..., min_length=2, max_length=2)
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, list):
            if len(v) != 2:
                raise ValueError(f"Weight pair must have exactly 2 values, got {len(v)}")
            return [float(w) for w in v]
        return v


class MixRequest(BaseModel):
    """Request model for mixing FT components.
    
    weights: List of 4 lists, each with 2 floats:
        - For magnitude_phase mode: [magnitude_weight, phase_weight]
        - For real_imaginary mode: [real_weight, imaginary_weight]
    """
    weights: List[List[float]] = Field(
        ..., 
        min_length=4, 
        max_length=4, 
        description="4 images, each with [component1_weight, component2_weight]"
    )
    rectangles: List[Optional[RectangleRegion]] = Field(
        ..., 
        min_length=4, 
        max_length=4, 
        description="Rectangle per image (null = full region)"
    )
    component_mode: str = Field(
        "magnitude_phase", 
        pattern="^(magnitude_phase|real_imaginary)$"
    )
    preserve_energy: bool = False

@app.get("/")
async def root():
    return {"message": "Fourier Mixer Backend"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "fourier-mixer-api", "version": "1.0.0"}


@app.post("/api/upload/{image_id}")
async def upload_image(image_id: int, file: UploadFile = File(...)):
    try:
        if image_id not in [0, 1, 2, 3]:
            raise HTTPException(status_code=400, detail="Image ID must be 0-3")
        
        contents = await file.read()
        result = image_manager.load_image(image_id, contents)
        
        if not result.get('success', False):
            raise HTTPException(status_code=400, detail=result.get('error', 'Upload failed'))
        
        # Save file locally with unique name
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(contents)
        
        result['filename'] = file.filename
        result['saved_as'] = filename
        
        return json_response(result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/images/{image_id}/grayscale")
async def convert_image_to_grayscale(image_id: int):
    """Convert the uploaded image to grayscale immediately (before display)."""
    try:
        if image_id not in [0, 1, 2, 3]:
            raise HTTPException(status_code=400, detail="Image ID must be 0-3")

        result = image_manager.convert_to_grayscale(image_id)
        if not result.get('success', False):
            raise HTTPException(status_code=400, detail=result.get('error', 'Conversion failed'))

        return json_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/images")
async def get_all_images():
    try:
        result = image_manager.get_all_images()
        return json_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/images/{image_id}")
async def get_image(image_id: int):
    try:
        if image_id not in [0, 1, 2, 3]:
            raise HTTPException(status_code=400, detail="Image ID must be 0-3")
        
        result = image_manager.get_image(image_id)
        
        if result is None:
            return json_response({
                "id": image_id,
                "loaded": False,
                "message": "Image not loaded"
            })
        
        return json_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/images/{image_id}")
async def delete_image(image_id: int):
    try:
        if image_id not in [0, 1, 2, 3]:
            raise HTTPException(status_code=400, detail="Image ID must be 0-3")
        
        result = image_manager.delete_image(image_id)
        return json_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/images")
async def delete_all_images():
    try:
        result = image_manager.delete_all_images()
        return json_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    try:
        result = image_manager.get_status()
        return json_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/resize")
async def resize_all_images():
    try:
        result = image_manager.resize_all_to_common()
        return json_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/common-size")
async def get_common_size():
    try:
        common_size = image_manager.get_common_size()
        
        if common_size is None:
            return json_response({
                "common_size": None,
                "message": "No common size calculated"
            })
        
        return json_response({
            "common_size": {
                "width": common_size[0],
                "height": common_size[1]
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ft/calculate/{image_id}")
async def calculate_ft(image_id: int):
    result = image_manager.calculate_ft_for_image(image_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return json_response(result)


@app.post("/api/ft/calculate-all")
async def calculate_all_ft():
    return json_response(image_manager.calculate_all_ft_components())


@app.get("/api/ft/component/{image_id}/{component}")
async def get_component(image_id: int, component: str):
    component = component.lower()
    if component not in ["magnitude", "phase", "real", "imaginary"]:
        raise HTTPException(status_code=400, detail="Invalid component")
    result = image_manager.get_ft_component_display(image_id, component)
    if result is None:
        raise HTTPException(status_code=404, detail="Component not available; calculate FT first")
    return json_response(result)


# @app.post("/api/ft/mix")
# async def mix_components(body: MixRequest):
#     """Mix FT components from 4 images using per-image rectangular masks."""
#     try:
#         # Convert Pydantic models to dicts
#         rectangles_list = [
#             rect.dict() if rect is not None else None
#             for rect in body.rectangles
#         ]
        
#         result = image_manager.mix_ft_components(
#             weights=body.weights,
#             rectangles=rectangles_list,
#             component_mode=body.component_mode,
#             preserve_energy=body.preserve_energy,
#         )
        
#         if not result.get("success"):
#             raise HTTPException(status_code=400, detail=result.get("error"))
        
#         return json_response(result)
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ft/mix")
async def mix_components(body: MixRequest):
    """Mix FT components from 4 images using per-image rectangular masks.
    
    weights format:
    - For magnitude_phase: [[mag0, phase0], [mag1, phase1], [mag2, phase2], [mag3, phase3]]
    - For real_imaginary: [[real0, imag0], [real1, imag1], [real2, imag2], [real3, imag3]]
    """
    try:
        # Validate each weight pair has exactly 2 values
        for idx, weight_pair in enumerate(body.weights):
            if len(weight_pair) != 2:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Weight for image {idx} must have exactly 2 values, got {len(weight_pair)}"
                )
        
        rectangles_list = [
            rect.dict() if rect is not None else None
            for rect in body.rectangles
        ]
        
        result = image_manager.mix_ft_components(
            weights=body.weights,
            rectangles=rectangles_list,
            component_mode=body.component_mode,
            preserve_energy=body.preserve_energy,
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return json_response(result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/api/ft/cache")
async def ft_cache_info():
    return json_response(image_manager.get_ft_cache_info())


@app.delete("/api/ft/cache")
async def ft_cache_clear(image_id: Optional[int] = None):
    if image_id is not None and image_id not in [0, 1, 2, 3]:
        raise HTTPException(status_code=400, detail="Image ID must be 0-3")
    image_manager.clear_ft_cache(image_id)
    return json_response({"success": True, "cleared": image_id if image_id is not None else "all"})

