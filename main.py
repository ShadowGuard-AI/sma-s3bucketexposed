import argparse
import logging
import sys
import boto3
import uuid
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

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

def is_valid_bucket_name(bucket_name):
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789.-")
    return (
        3 <= len(bucket_name) <= 63
        and all(c in allowed for c in bucket_name)
        and bucket_name[0] in "abcdefghijklmnopqrstuvwxyz0123456789"
        and bucket_name[-1] in "abcdefghijklmnopqrstuvwxyz0123456789"
        and ".." not in bucket_name
        and ".-" not in bucket_name
        and "-." not in bucket_name
    )

def check_bucket_access(bucket_name):
    """
    Checks if an S3 bucket allows public listing and writing, without
    using any credentials, so the result reflects public access.

    Returns:
        dict: listing, writing, listing_status, writing_status, exists,
            and leftover_key (the test object key left behind if cleanup
            failed, otherwise None).
    """
    # No region is set anywhere, so the client uses whatever the SDK
    # resolves from the environment. For a bucket living elsewhere the
    # first answer is often a redirect error, which the handlers below
    # file under unknown rather than allowed or denied.
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    results = {'listing': False, 'writing': False, 'listing_status': 'unknown', 'writing_status': 'unknown', 'exists': None, 'leftover_key': None}

    # Check if bucket listing is allowed
    try:
        logging.info(f"Attempting to list contents of bucket: {bucket_name}")
        s3.list_objects_v2(Bucket=bucket_name)
        results['listing'] = True
        results['listing_status'] = 'allowed'
        results['exists'] = True
        logging.info(f"Bucket {bucket_name} allows public listing.")
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code', '')
        if code == 'AccessDenied':
            # Exists here is an inference, not a fact: S3 also answers
            # 403 for names that are not yours to know about, which is
            # the same response a private bucket that does exist gives.
            results['listing_status'] = 'access_denied'
            results['exists'] = True
            logging.info(f"Bucket {bucket_name} does not allow public listing.")
        elif code == 'NoSuchBucket':
            results['listing_status'] = 'does_not_exist'
            results['writing_status'] = 'does_not_exist'
            results['exists'] = False
            logging.error(f"Bucket {bucket_name} does not exist.")
            return results
        else:
            results['listing_status'] = 'unknown'
            logging.error(f"Error listing bucket {bucket_name}: {e}")
    except BotoCoreError as e:
        results['listing_status'] = 'unknown'
        logging.error(f"Error listing bucket {bucket_name}: {e}. Listing result is unknown.")

    # Check if bucket writing is allowed
    test_file_name = f"test_file_{uuid.uuid4()}.txt"
    try:
        logging.info(f"Attempting to write a test file to bucket: {bucket_name}")
        s3.put_object(Bucket=bucket_name, Key=test_file_name, Body="This is a test file.")
        results['writing'] = True
        results['writing_status'] = 'allowed'
        results['exists'] = True
        logging.info(f"Bucket {bucket_name} allows public writing.")

        # Clean up the test file, retrying the delete once on failure
        cleaned = False
        for attempt in range(2):
            try:
                s3.delete_object(Bucket=bucket_name, Key=test_file_name)
                cleaned = True
                logging.info(f"Successfully cleaned up test file {test_file_name} in bucket {bucket_name}")
                break
            except (ClientError, BotoCoreError) as e:
                logging.error(f"Error cleaning up test file {test_file_name} in bucket {bucket_name} (attempt {attempt + 1}): {e}")
            except Exception as e:
                logging.error(f"Error cleaning up test file {test_file_name} in bucket {bucket_name} (attempt {attempt + 1}): {e}")
        if not cleaned:
            results['leftover_key'] = test_file_name
            logging.error(f"Cleanup failed. Test object {test_file_name} was left behind in bucket {bucket_name}.")

    except ClientError as e:
        code = e.response.get('Error', {}).get('Code', '')
        if code == 'AccessDenied':
            results['writing_status'] = 'access_denied'
            results['exists'] = True
            logging.info(f"Bucket {bucket_name} does not allow public writing.")
        elif code == 'NoSuchBucket':
            results['writing_status'] = 'does_not_exist'
            results['exists'] = False
            logging.error(f"Bucket {bucket_name} does not exist.")
            return results
        else:
            results['writing_status'] = 'unknown'
            logging.error(f"Error writing to bucket {bucket_name}: {e}")
    except BotoCoreError as e:
        results['writing_status'] = 'unknown'
        logging.error(f"Error writing to bucket {bucket_name}: {e}. Writing result is unknown.")
    except Exception as e:
        results['writing_status'] = 'unknown'
        logging.error(f"An unexpected error occurred while attempting to write to {bucket_name}: {e}")

    return results

def main():
    """
    Main function to parse arguments and check S3 bucket access.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    bucket_name = args.bucket_name

    if not is_valid_bucket_name(bucket_name):
        logging.error("Invalid S3 bucket name format. Bucket names must be between 3 and 63 characters long, can contain only lowercase letters, numbers, dots (.), and hyphens (-), must begin and end with a lowercase letter or number, and must not contain adjacent dots or a dot next to a hyphen.")
        sys.exit(1)

    logging.warning("Write probe warning: this check writes a test object into the bucket and then deletes it. If cleanup fails, the test object is left behind in the bucket.")

    results = check_bucket_access(bucket_name)

    print(f"Bucket: {bucket_name}")
    print(f"Public Listing: {results['listing']} (status: {results['listing_status']})")
    print(f"Public Writing: {results['writing']} (status: {results['writing_status']})")
    if results.get('leftover_key'):
        print(f"Leftover test object: {results['leftover_key']} (cleanup failed, this object was left behind in the bucket)")

    # Only a bucket that does not exist exits non zero. A bucket that
    # is wide open for public writing, the worst result this tool can
    # find, still exits 0, so a script must read the printed lines and
    # cannot gate on the exit code.
    if results.get('exists') is False:
        sys.exit(1)


if __name__ == "__main__":
    main()
