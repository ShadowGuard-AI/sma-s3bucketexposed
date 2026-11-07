# sma-S3BucketExposed
A simple command-line tool that checks if an AWS S3 bucket allows public listing and/or writing by attempting to list the bucket's contents and write a test file, using boto3 with an unsigned client so the result reflects public access. It prints an explicit status for each check. It does not scan web applications, endpoints, or other services, and it has no rulesets.

## Install
```
git clone https://github.com/ShadowGuard-AI/sma-s3bucketexposed
cd sma-s3bucketexposed
pip install -r requirements.txt
```

## Usage
`python3 main.py <bucket-name>`

## Parameters
- `bucket_name`: Required positional argument. The name of the S3 bucket to check.
- `-h`: Show help message and exit

## How the check works

The S3 client is built with an unsigned signature configuration, so the check tests public access and does not use the operator's AWS credentials. The summary prints an explicit status for each check: allowed, access_denied, does_not_exist, or unknown. A bucket that does not exist ends the run with exit status 1, and an invalid bucket name also exits with status 1. A valid name is 3 to 63 characters of lowercase letters, numbers, dots, and hyphens only, begins and ends with a lowercase letter or number, and contains no adjacent dots and no dot next to a hyphen. Other outcomes, including a bucket that allows public writing, exit 0, so a script must read the printed status lines and cannot gate on the exit code alone.

Warning: the write probe writes a test object into the bucket and then deletes it. If cleanup fails, the delete is retried once, the leftover test object key is named in the final summary, and the test object is left behind in the bucket.

## License
MIT License. See [LICENSE](LICENSE).
