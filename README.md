# sma-S3BucketExposed
A simple command-line tool that checks if an AWS S3 bucket allows public listing and/or writing by attempting to list the bucket's contents and write a test file.  Uses boto3. - Focused on Identifies common security misconfigurations in web applications and services by scanning exposed endpoints and analyzing responses. Supports customizable rulesets for different technologies and generates actionable reports on discovered vulnerabilities.

## Install
`git clone https://github.com/ShadowStrikeHQ/sma-s3bucketexposed`

## Usage
`./sma-s3bucketexposed [params]`

## Parameters
- `-h`: Show help message and exit

## How the check works

The S3 client is built with an unsigned signature configuration, so the check tests public access and does not use the operator's AWS credentials. The summary prints an explicit status for each check: allowed, access_denied, does_not_exist, or unknown. A bucket that does not exist ends the run with exit status 1, and an invalid bucket name (3 to 63 characters, lowercase letters, numbers, dots, and hyphens only) also exits with status 1.

Warning: the write probe writes a test object into the bucket and then deletes it. If cleanup fails, the delete is retried once, the leftover test object key is named in the final summary, and the test object is left behind in the bucket.

## License
Copyright (c) ShadowStrikeHQ
