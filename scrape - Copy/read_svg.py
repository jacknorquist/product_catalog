from dotenv import load_dotenv
import requests
import cairosvg
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from io import BytesIO
import os

# Load environment variables from .env file
load_dotenv()

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name='us-east-2'
)

bucket_name = 'projectscatalog'

def upload_svg_as_png_to_s3(svg_url, bucket_name, s3_key):
    try:
        # Download the SVG file from the URL
        print('in here')
        response = requests.get(svg_url, stream=True, allow_redirects=True)
        response.raise_for_status()
        print(response.status_code)  # Raise an exception for HTTP errors

        # Convert the SVG to PNG
        png_data = cairosvg.svg2png(bytestring=response.content)

        # Upload the PNG data to S3
        s3.upload_fileobj(BytesIO(png_data), bucket_name, s3_key, ExtraArgs={'ContentType': 'image/png', 'ContentDisposition': 'inline'})

        # Construct the S3 URL
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        return s3_url

    except requests.RequestException as e:
        print(f"Failed to download SVG file: {e}")
    except NoCredentialsError:
        print("AWS credentials not available.")
    except ClientError as e:
        return (f"Failed to upload to S3: {e}")
    except Exception as e:
        return f"An error occurred: {e}"