import argparse
import os
import json
import sys

try:
    import boto3
except ImportError:
    print(
        "This script requires boto3 to be installed. Please run: \n\n\tpip install boto3\n",
        file=sys.stderr,
    )
    sys.exit(1)

ENVIRONMENT_DEV = "dev"
ENVIRONMENT_PROD = "prod"
ENVIRONMENT_CLOUD = "cloud"

access_key = os.environ.get('AFID_APP_ACCESS_KEY')
secret_key = os.environ.get('AFID_APP_SECRET_KEY')


# S3_ENDPOINT = "https://sdkwdpmf97lg.compat.objectstorage.ap-sydney-1.oraclecloud.com"
S3_ENDPOINT = "https://projects.pawsey.org.au"


def get_s3_client(environment: str):


    # bucket_name = "prod-django-storage"
    bucket_name = 'afid-media-prod'
    
    boto_session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    s3 = boto_session.client("s3", endpoint_url=S3_ENDPOINT)

    return s3, bucket_name


def setup_output_dir(path: str):
    if not os.path.exists(path):
        os.mkdir(path)


def main(coco_filename: str, github_token: str, environment: str, output_dir: str):
    # vault_client = get_vault_client(github_token)
    s3_client, bucket_name = get_s3_client(environment)

    if output_dir != ".":
        setup_output_dir(output_dir)

    with open(coco_filename, "r") as f:
        coco_json = json.load(f)

    image_count = len(coco_json["images"])

    for i, image in enumerate(coco_json["images"], start=1):
        filename = image.get("filename") or image.get("file_name")

        print(f"[{i}/{image_count}] Downlading image {filename}")
        print(f"from {os.path.join(bucket_name, filename)}")

        with open(os.path.join(output_dir, filename), "wb") as f:
            s3_client.download_fileobj(bucket_name, filename, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Helper script to download the image files described by an AFID-generated COCO-JSON file."
    )

    parser.add_argument(
        "coco_filename", help="Path to the COCO-JSON file to parse", type=str
    )

    parser.add_argument(
        "github_token",
        help="A GitHub personal access token with read:org scope. Set to '-' to read from stdin",
        type=str,
    )

    parser.add_argument(
        "--env",
        help=f"The AFID environment that the COCO-JSON file was generated from (default: {ENVIRONMENT_CLOUD}).",
        type=str,
        choices=[ENVIRONMENT_DEV, ENVIRONMENT_PROD, ENVIRONMENT_CLOUD],
        default=ENVIRONMENT_CLOUD,
    )

    parser.add_argument(
        "-o",
        "--out",
        dest="out",
        help="Path to the folder to write images to. It will be created if it does not exist. If not given then the images will be downloaded to the current working directory",
        type=str,
        default=".",
    )

    args = parser.parse_args()

    github_token = args.github_token
    if github_token == "-":
        github_token = input()

    main(args.coco_filename, github_token, args.env, args.out)