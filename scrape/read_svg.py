from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import base64
from io import BytesIO
import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

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

def upload_base64_png_to_s3_from_svg(svg_url, bucket_name, s3_key):
    try:
        # Download the SVG file from the URL
        response = requests.get(svg_url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the SVG content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'xml')

        # Find the <image> tag within the <defs> section
        defs = soup.find('defs')
        if defs:
            image_tag = defs.find('image')
            if image_tag and 'xlink:href' in image_tag.attrs:
                # Extract the PNG data from the xlink:href attribute
                png_data = image_tag['xlink:href']

                # Check if the data is base64 encoded
                if png_data.startswith('data:image/png;base64,'):
                    base64_data = png_data.split(',')[1]
                    binary_data = base64.b64decode(base64_data)

                    # Upload the decoded PNG data to S3
                    s3.upload_fileobj(BytesIO(binary_data), bucket_name, s3_key, ExtraArgs={'ContentType': 'image/png', 'ContentDisposition': 'inline'})

                    # Construct the S3 URL
                    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
                    return s3_url
                else:
                    return "The PNG data is not base64 encoded."
            else:
                return "No PNG data found in the SVG file."
        else:
            return "No <defs> section found in the SVG file."

    except requests.RequestException as e:
        return f"Failed to download SVG file: {e}"
    except NoCredentialsError:
        return "AWS credentials not available."
    except ClientError as e:
        return f"Failed to upload to S3: {e}"
    except Exception as e:
        return f"An error occurred: {e}"