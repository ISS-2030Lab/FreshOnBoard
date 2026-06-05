import boto3
import os
from botocore.config import Config
from botocore.exceptions import ClientError


def get_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["OBS_ENDPOINT"],
        aws_access_key_id=os.environ["OBS_ACCESS_KEY"],
        aws_secret_access_key=os.environ["OBS_SECRET_KEY"],
        config=Config(request_checksum_calculation="when_required"),
    )


def list_buckets():
    s3 = get_client()
    response = s3.list_buckets()
    return [b["Name"] for b in response.get("Buckets", [])]


def list_objects(bucket, prefix=""):
    s3 = get_client()
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [obj["Key"] for obj in response.get("Contents", [])]


def list_dirs(bucket, prefix=""):
    s3 = get_client()
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter="/")
    return [p["Prefix"] for p in response.get("CommonPrefixes", [])]


def upload(bucket, local_path, remote_key):
    s3 = get_client()
    s3.upload_file(local_path, bucket, remote_key)
    print(f"Uploaded {local_path} -> s3://{bucket}/{remote_key}")


def download(bucket, remote_key, local_path):
    s3 = get_client()
    s3.download_file(bucket, remote_key, local_path)
    print(f"Downloaded s3://{bucket}/{remote_key} -> {local_path}")


def delete(bucket, remote_key):
    s3 = get_client()
    s3.delete_object(Bucket=bucket, Key=remote_key)
    print(f"Deleted s3://{bucket}/{remote_key}")


def exists(bucket, remote_key):
    s3 = get_client()
    try:
        s3.head_object(Bucket=bucket, Key=remote_key)
        return True
    except ClientError:
        return False


def _md5(file_path):
    import hashlib
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _remote_etag(s3, bucket, remote_key):
    try:
        resp = s3.head_object(Bucket=bucket, Key=remote_key)
        return resp["ETag"].strip('"')
    except ClientError:
        return None


def sync_dir(bucket, local_dir, remote_prefix=""):
    s3 = get_client()
    local_dir = os.path.abspath(local_dir)
    uploaded = skipped = 0

    for root, _, files in os.walk(local_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative = os.path.relpath(local_path, local_dir)
            remote_key = os.path.join(remote_prefix, relative).lstrip("/")

            etag = _remote_etag(s3, bucket, remote_key)
            if etag and etag == _md5(local_path):
                print(f"Skipped (unchanged): {relative}")
                skipped += 1
                continue

            s3.upload_file(local_path, bucket, remote_key)
            print(f"Uploaded: {relative} -> s3://{bucket}/{remote_key}")
            uploaded += 1

    print(f"\nDone: {uploaded} uploaded, {skipped} skipped.")


if __name__ == "__main__":
    # print("Buckets:", list_buckets())
    # print("Dirs in yw-2030-extern:", list_dirs("yw-2030-extern"))

    upload("yw-2030-extern", 
           "/Users/yinhongliu/Documents/source/FreshOnBoard/readings.md", "Intern/yinhongliu/readings.md")