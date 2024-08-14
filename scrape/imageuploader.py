from dotenv import load_dotenv
import requests
from botocore.exceptions import NoCredentialsError
import mimetypes
import os
import boto3

# Load environment variables from .env file
load_dotenv()

# Access the environment variables

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name='us-east-2'
)

bucket_name = 'projectscatalog'


def upload_image_stream_to_s3(image_url, bucket_name, s3_key, content_type='img/png'):
    s3 = boto3.client('s3')

    try:
        # Stream the image data
        response = requests.get(image_url, stream=True)
        content_type, _ = mimetypes.guess_type(image_url)
        print(content_type)

        # Check if the request was successful
        if response.status_code == 200:
            # Upload the stream to S3
            s3.upload_fileobj(response.raw, bucket_name, s3_key, ExtraArgs={'ContentType': content_type})

            # Construct the S3 URL
            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
            return s3_url
        else:
            print(f"Failed to download image from {image_url}")
            return None
    except NoCredentialsError:
        print("Credentials not available")
        return None