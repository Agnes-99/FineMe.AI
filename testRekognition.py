import boto3
import os
from dotenv import load_dotenv

load_dotenv()

rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

def test_rekognition():
    try:
        response = rekognition.list_collections()
        print("✅ Rekognition connected successfully!")
        print("Existing collections:", response.get('CollectionIds', []))
    except Exception as e:
        print("❌ Something went wrong:", e)

if __name__ == "__main__":
    test_rekognition()