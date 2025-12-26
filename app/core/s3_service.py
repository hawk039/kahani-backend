import boto3
from botocore.exceptions import NoCredentialsError
from botocore.config import Config
import os
from fastapi import HTTPException
import uuid
import io
from dotenv import load_dotenv

# Explicitly load environment variables
load_dotenv()

# Load environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# DEBUG PRINT
print(f"--- S3 CONFIG DEBUG ---")
print(f"AWS_REGION loaded as: {AWS_REGION}")
print(f"S3_BUCKET_NAME loaded as: {S3_BUCKET_NAME}")
print(f"-----------------------")

def get_s3_client():
    """
    Creates and returns a boto3 S3 client with s3v4 signature.
    """
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise ValueError("AWS credentials not found in environment variables.")
    
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
        config=Config(signature_version='s3v4')
    )

async def upload_file_bytes_to_s3(file_bytes: bytes, filename: str, content_type: str) -> str:
    """
    Uploads file bytes to S3 and returns the public URL.
    """
    s3_client = get_s3_client()
    
    # Generate a unique filename to prevent overwrites
    file_extension = filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    try:
        # Create a file-like object from bytes
        file_obj = io.BytesIO(file_bytes)
        
        # Upload the file
        s3_client.upload_fileobj(
            file_obj,
            S3_BUCKET_NAME,
            unique_filename,
            ExtraArgs={
                "ContentType": content_type,
                # "ACL": "public-read"  <-- REMOVED because bucket does not support ACLs
            }
        )
        
        # Construct the public URL using the configured region
        file_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
        return file_url

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available.")
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image to S3: {str(e)}")
