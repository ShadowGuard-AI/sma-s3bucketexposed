import argparse
import logging
import boto3
import os
import uuid
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    
    Returns:
        argparse.ArgumentParser: The argument parser object.
    """
    parser = argparse.ArgumentParser(description="Checks if an AWS S3 bucket allows public listing and/or writing.")
    parser.add_argument("bucket_name", help="The name of the S3 bucket to check.")
    return parser

def check_bucket_access(bucket_name):
    """
    Checks if an S3 bucket allows public listing and writing.

    Args:
        bucket_name (str): The name of the S3 bucket.

    Returns:
        dict: A dictionary containing the results of the checks.
            {'listing': bool, 'writing': bool}
    """
    s3 = boto3.client('s3')
    results = {'listing': False, 'writing': False}

    # Check if bucket listing is allowed
    try:
        logging.info(f"Attempting to list contents of bucket: {bucket_name}")
        s3.list_objects_v2(Bucket=bucket_name)
        results['listing'] = True
        logging.info(f"Bucket {bucket_name} allows public listing.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDenied':
            logging.info(f"Bucket {bucket_name} does not allow public listing.")
        elif e.response['Error']['Code'] == 'NoSuchBucket':
             logging.error(f"Bucket {bucket_name} does not exist.")
             return results  # Exit early since bucket doesn't exist
        else:
            logging.error(f"Error listing bucket {bucket_name}: {e}")

    # Check if bucket writing is allowed
    test_file_name = f"test_file_{uuid.uuid4()}.txt"
    try:
        logging.info(f"Attempting to write a test file to bucket: {bucket_name}")
        s3.put_object(Bucket=bucket_name, Key=test_file_name, Body="This is a test file.")
        results['writing'] = True
        logging.info(f"Bucket {bucket_name} allows public writing.")

        # Clean up the test file
        try:
            s3.delete_object(Bucket=bucket_name, Key=test_file_name)
            logging.info(f"Successfully cleaned up test file {test_file_name} in bucket {bucket_name}")
        except ClientError as e:
            logging.error(f"Error cleaning up test file {test_file_name} in bucket {bucket_name}: {e}")

    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDenied':
            logging.info(f"Bucket {bucket_name} does not allow public writing.")
        elif e.response['Error']['Code'] == 'NoSuchBucket':
            logging.error(f"Bucket {bucket_name} does not exist.")
            return results
        else:
            logging.error(f"Error writing to bucket {bucket_name}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while attempting to write to {bucket_name}: {e}")

    return results

def main():
    """
    Main function to parse arguments and check S3 bucket access.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    bucket_name = args.bucket_name

    # Input validation: Basic check for bucket name format
    if not (0 < len(bucket_name) <= 63 and all(c.isalnum() or c in '.-' for c in bucket_name) and not bucket_name.startswith('-') and not bucket_name.endswith('-')):
        logging.error("Invalid S3 bucket name format. Bucket names must be between 3 and 63 characters long, can contain only lowercase letters, numbers, dots (.), and hyphens (-), and must not start or end with a hyphen.")
        return

    results = check_bucket_access(bucket_name)

    print(f"Bucket: {bucket_name}")
    print(f"Public Listing: {results['listing']}")
    print(f"Public Writing: {results['writing']}")


if __name__ == "__main__":
    main()

# Usage examples:
# python sma-S3BucketExposed.py my-bucket-name
# python sma-S3BucketExposed.py another.bucket.name