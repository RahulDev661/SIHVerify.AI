from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Passport Verification API",
    description="AI-based Passport Verification Backend",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.get("/")
async def root():
    return {
        "message": "Passport Verification API is running"
    }




@app.post("/verify")
async def verify_passport(
    file: UploadFile = File(...),
    document_type: str = Form(...)
):

          

    if document_type != "Passport":
        raise HTTPException(
            status_code=400,
            detail="Only passport verification is supported."
        )


    # -------------------------
    # Check file type
    # -------------------------

    allowed_types = {
        "image/jpeg",
        "image/jpg",
        "image/png"
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPG and PNG passport images are supported."
        )


    # -------------------------
    # Read uploaded image
    # -------------------------

    image_data = await file.read()


    # -------------------------
    # Check file size
    # -------------------------

    max_size = 10 * 1024 * 1024

    if len(image_data) > max_size:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 10MB."
        )


    # -------------------------
    # TEMPORARY RESPONSE
    # -------------------------
    #
    # Later:
    #
    # image_data
    #      ↓
    # OCR Model
    #      ↓
    # Face Model
    #      ↓
    # Verification Model
    #      ↓
    # Decision Layer
    #
    # -------------------------

    return {
        "success": True,
        "filename": file.filename,
        "document_type": document_type,
        "file_size": len(image_data),
        "message": "Passport received successfully."
    }