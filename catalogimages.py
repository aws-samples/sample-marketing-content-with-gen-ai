"""
Image Catalog Documentation Generator

This script processes a directory of images and generates descriptive metadata using AWS Bedrock's
Claude AI model. For each image, it creates a description and tags, then saves the results to a JSON file.

Dependencies:
- boto3: AWS SDK for Python
- PIL: Python Imaging Library for image processing
- AWS Bedrock service access configured
"""

import boto3
import json
import base64
import io
import os 

from PIL import Image
import random

# Initialize AWS Bedrock client for AI image analysis
bedrock_client = boto3.client(service_name='bedrock-runtime',region_name='us-west-2')
def encode_image(img_file):
    """
    Convert an image file to a base64 encoded string.
    
    Args:
        img_file (str): Path to the image file
        
    Returns:
        str: Base64 encoded string representation of the image
    """
    with open(img_file, "rb") as image_file:
        img_str = base64.b64encode(image_file.read())
        base64_string = img_str.decode("utf-8")
    return base64_string

def get_content_from_model(body):
    """
    Extract text content from the Bedrock model response.
    
    Args:
        body (dict): Response body from the Bedrock model
        
    Returns:
        str: Concatenated text content from the model response
    """
    response = []
    response_body = json.loads(body.get("body").read())
    for m in response_body["content"]:
        if m["type"] == "text":
            response.append(m["text"])
    return "".join(response)

def describe_image(model_id, existing_image, format):
    """
    Send an image to AWS Bedrock's Claude model for analysis and description.
    
    The function requests a two-sentence description and 5 tags for the image.
    
    Args:
        model_id (str): AWS Bedrock model identifier
        existing_image (str): Path to the image file
        format (str): MIME type of the image (e.g., 'image/jpeg', 'image/png')
        
    Returns:
        str: JSON string containing image description and tags
    """
    # Set maximum token limit for model response
    MAX_TOKENS = 1000

    # Define the prompt for the AI model
    analysis_question="""
    You are a service that describes images. 
    Can you generate me a description of what happens in this image in two sentances. 
    Then generate 5 tags that could be assocaited with that image.
    Respond in the JSON format:
    {
        "description": "Description of the image in 2 sentances",
        "tags": "tag1, tag2, tag3, tag4, tag5"
    }
    """
    # Convert image to base64 for API transmission
    base64_string = encode_image(existing_image)
    
    # Construct the message for the model
    message = {"role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64",
                        "media_type": format, "data": base64_string}},
                        {"type": "text", "text": analysis_question}
                        ]}
    
    # Prepare the request body
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": MAX_TOKENS,
            "messages": [message],
        }
    )

    # Call the Bedrock model
    response = bedrock_client.invoke_model(
        modelId=model_id,
        body=body,
        contentType='application/json',
    )
    
    # Extract and return the text content from the response
    return get_content_from_model(response)



def get_filenames_in_directory(directory_path):
    """
    Retrieve a list of all filenames in the specified directory.
    
    Args:
        directory_path (str): Path to the directory to scan
        
    Returns:
        list or str: List of filenames if directory exists, error message otherwise
    """
    try:
        filenames = os.listdir(directory_path)
        return filenames
    except FileNotFoundError:
        return f"Directory '{directory_path}' does not exist."

# Main execution block
if __name__ == "__main__":
    # Directory containing images to process
    directory_path = "imagecatalog"
    filenames = get_filenames_in_directory(directory_path)
    
    # Dictionary to store image descriptions and tags
    json_dict = {} 
    
    # Process each file in the directory
    for filename in filenames:
        full_path = "imagecatalog/" + filename
        print(f"Processing file: {full_path}")
        try:
            # Process JPG images
            if full_path.lower().endswith(".jpg"):
                response = describe_image('anthropic.claude-3-haiku-20240307-v1:0', full_path, 'image/jpeg')
                jsonresponse = json.loads(response)
                json_dict[full_path] = jsonresponse 
            # Process PNG images
            elif full_path.lower().endswith(".png"):
                response = describe_image('anthropic.claude-3-haiku-20240307-v1:0', full_path, 'image/png')
                jsonresponse = json.loads(response)
                json_dict[full_path] = jsonresponse         
            else: 
                print('Not a jpeg or png - skipping file')
        except Exception as e:
            print(f"Error processing {full_path}: {str(e)}")
    
    # Output the results to console
    print(json.dumps(json_dict))
    
    # Save results to a JSON file
    file_path = "imagecatalog.json"
    with open(file_path, 'w') as file:
        json.dump(json_dict, file, indent=4)  # indent=4 for pretty-printing
    
    print(f"Image catalog saved to {file_path}")
