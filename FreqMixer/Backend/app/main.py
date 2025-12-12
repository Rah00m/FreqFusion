# from fastapi import FastAPI, File, UploadFile, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# import os
# import uuid
# from typing import List, Dict
# import json

# # Import our modules
# from image_manager import ImageManager
# from utils import JsonEncoder

# # Initialize FastAPI app
# app = FastAPI(
#     title="Fourier Transform Mixer API - Phase 1",
#     description="Image upload and resizing system",
#     version="1.0.0"
# )

# # CORS Configuration
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],  # React frontend
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Create uploads directory
# UPLOAD_DIR = "uploads"
# os.makedirs(UPLOAD_DIR, exist_ok=True)

# # Initialize Image Manager
# image_manager = ImageManager()

# # Custom JSON response with numpy support
# def json_response(data: Dict):
#     return JSONResponse(
#         content=json.loads(json.dumps(data, cls=JsonEncoder))
#     )

# @app.get("/")
# async def root():
#     return {"message": "Fourier Mixer Backend - Phase 1: Image Management"}

# @app.get("/api/health")
# async def health_check():
#     """Health check endpoint"""
#     return {
#         "status": "healthy",
#         "service": "fourier-mixer-api",
#         "version": "1.0.0"
#     }

# @app.post("/api/upload/{image_id}")
# async def upload_image(
#     image_id: int,
#     file: UploadFile = File(...)
# ):
#     """Upload an image (0-3)"""
#     try:
#         # Validate image_id
#         if image_id not in [0, 1, 2, 3]:
#             raise HTTPException(status_code=400, detail="Image ID must be 0-3")
        
#         # Read file content
#         contents = await file.read()
        
#         # Load image using ImageManager
#         result = image_manager.load_image(image_id, contents)
        
#         if not result.get('success', False):
#             raise HTTPException(status_code=400, detail=result.get('error', 'Upload failed'))
        
#         # Save file locally (optional)
#         filename = f"{uuid.uuid4()}_{file.filename}"
#         filepath = os.path.join(UPLOAD_DIR, filename)
        
#         with open(filepath, "wb") as f:
#             f.write(contents)
        
#         # Add filename to result
#         result['filename'] = file.filename
#         result['saved_as'] = filename
        
#         return json_response(result)
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/images")
# async def get_all_images():
#     """Get all uploaded images"""
#     try:
#         result = image_manager.get_all_images()
#         return json_response(result)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/images/{image_id}")
# async def get_image(image_id: int):
#     """Get specific image"""
#     try:
#         if image_id not in [0, 1, 2, 3]:
#             raise HTTPException(status_code=400, detail="Image ID must be 0-3")
        
#         result = image_manager.get_image(image_id)
        
#         if result is None:
#             return json_response({
#                 "id": image_id,
#                 "loaded": False,
#                 "message": "Image not loaded"
#             })
        
#         return json_response(result)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.delete("/api/images/{image_id}")
# async def delete_image(image_id: int):
#     """Delete a specific image"""
#     try:
#         if image_id not in [0, 1, 2, 3]:
#             raise HTTPException(status_code=400, detail="Image ID must be 0-3")
        
#         result = image_manager.delete_image(image_id)
#         return json_response(result)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.delete("/api/images")
# async def delete_all_images():
#     """Delete all images"""
#     try:
#         result = image_manager.delete_all_images()
#         return json_response(result)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/status")
# async def get_status():
#     """Get system status"""
#     try:
#         result = image_manager.get_status()
#         return json_response(result)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/samples")
# async def load_sample_images():
#     """Load 4 sample images for testing"""
#     try:
#         result = image_manager.load_sample_images()
#         return json_response(result)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/resize")
# async def resize_all_images():
#     """Resize all images to common size"""
#     try:
#         result = image_manager.resize_all_to_common()
#         return json_response(result)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/resize/{image_id}")
# async def resize_single_image(image_id: int):
#     """Resize specific image to common size"""
#     try:
#         if image_id not in [0, 1, 2, 3]:
#             raise HTTPException(status_code=400, detail="Image ID must be 0-3")
        
#         result = image_manager.resize_image_to_common(image_id)
        
#         if result is None:
#             raise HTTPException(status_code=400, detail="Image not loaded or no common size")
        
#         return json_response(result)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/common-size")
# async def get_common_size():
#     """Get current common size"""
#     try:
#         common_size = image_manager.get_common_size()
        
#         if common_size is None:
#             return json_response({
#                 "common_size": None,
#                 "message": "No common size calculated (need at least 1 image)"
#             })
        
#         return json_response({
#             "common_size": {
#                 "width": common_size[0],
#                 "height": common_size[1]
#             },
#             "total_images": image_manager.get_loaded_count()
#         })
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/stats")
# async def get_statistics():
#     """Get detailed statistics"""
#     try:
#         images_data = image_manager.get_all_images()
#         loaded_count = image_manager.get_loaded_count()
#         common_size = image_manager.get_common_size()
        
#         return json_response({
#             "images": images_data,
#             "statistics": {
#                 "loaded_count": loaded_count,
#                 "common_size": common_size,
#                 "total_capacity": 4,
#                 "available_slots": 4 - loaded_count
#             }
#         })
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         app, 
#         host="0.0.0.0", 
#         port=5000, 
#         reload=True,
#         log_level="info"
#     )


from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import uuid
import json

# استيراد من نفس المجلد
from .image_manager import ImageManager
from .utils import JsonEncoder

# Initialize FastAPI app
app = FastAPI(
    title="Fourier Transform Mixer API - Phase 1",
    description="Image upload and resizing system",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize Image Manager
image_manager = ImageManager()

# Custom JSON response
def json_response(data: dict):
    return JSONResponse(
        content=json.loads(json.dumps(data, cls=JsonEncoder))
    )

@app.get("/")
async def root():
    return {"message": "Fourier Mixer Backend - Phase 1: Image Management"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "fourier-mixer-api",
        "version": "1.0.0"
    }

@app.post("/api/upload/{image_id}")
async def upload_image(
    image_id: int,
    file: UploadFile = File(...)
):
    try:
        if image_id not in [0, 1, 2, 3]:
            raise HTTPException(status_code=400, detail="Image ID must be 0-3")
        
        contents = await file.read()
        result = image_manager.load_image(image_id, contents)
        
        if not result.get('success', False):
            raise HTTPException(status_code=400, detail=result.get('error', 'Upload failed'))
        
        # Save file locally
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

@app.post("/api/samples")
async def load_sample_images():
    try:
        result = image_manager.load_sample_images()
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