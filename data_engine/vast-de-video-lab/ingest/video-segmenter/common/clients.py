import logging
import boto3
from typing import Dict, List, Any, Tuple
from botocore.exceptions import ClientError


class S3Client:
    """S3 client for video operations"""
    
    def __init__(self, settings):
        self.settings = settings
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3endpoint,
            aws_access_key_id=settings.s3accesskey,
            aws_secret_access_key=settings.s3secretkey,
            verify=False
        )
    
    def head_object(self, bucket: str, key: str) -> dict[str, Any]:
        """Get metadata for an S3 object"""
        logging.info(f"Fetching metadata for s3://{bucket}/{key}")
        response = self.client.head_object(Bucket=bucket, Key=key)
        return response
    
    def download_file(self, bucket: str, key: str) -> bytes:
        """Download file from S3"""
        logging.info(f"Downloading s3://{bucket}/{key}")
        response = self.client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read()
        logging.info(f"Downloaded {len(content)} bytes")
        return content
    
    def upload_bytes(self, content: bytes, bucket: str, key: str, metadata: Dict[str, str] = None) -> bool:
        """Upload bytes to S3 with metadata"""
        try:
            logging.info(f"Uploading {len(content)} bytes to s3://{bucket}/{key}")
            
            put_args = {
                "Bucket": bucket,
                "Key": key,
                "Body": content
            }
            
            if metadata:
                put_args["Metadata"] = metadata
            
            self.client.put_object(**put_args)
            logging.info(f"Successfully uploaded to s3://{bucket}/{key}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to upload to s3://{bucket}/{key}: {e}")
            return False
    
    def get_object_acl(self, bucket: str, key: str) -> Tuple[List[str], List[str]]:
        """Get object ACL and extract allowed users and groups"""
        try:
            logging.info(f"Fetching ACL for s3://{bucket}/{key}")
            response = self.client.get_object_acl(Bucket=bucket, Key=key)
            
            allowed_users = []
            allowed_groups = []
            
            # Parse grants from ACL
            for grant in response.get("Grants", []):
                permission = grant.get("Permission")
                grantee = grant.get("Grantee", {})
                grantee_type = grantee.get("Type")
                
                # Only consider READ permissions
                if permission in ["READ", "FULL_CONTROL"]:
                    if grantee_type == "CanonicalUser":
                        user_id = grantee.get("DisplayName")
                        if user_id and user_id not in allowed_users:
                            allowed_users.append(user_id)
                    elif grantee_type == "Group":
                        group_uri = grantee.get("URI", "")
                        # Extract group identifier from URI
                        if "AllUsers" in group_uri:
                            allowed_groups.append("public-read")
                        elif "AuthenticatedUsers" in group_uri:
                            allowed_groups.append("authenticated-users")
                        else:
                            # Custom group - extract identifier
                            group_id = group_uri.split("/")[-1] if group_uri else None
                            if group_id and group_id not in allowed_groups:
                                allowed_groups.append(group_id)
                    elif grantee_type == "AmazonCustomerByEmail":
                        email = grantee.get("EmailAddress")
                        if email and email not in allowed_users:
                            allowed_users.append(email)
            
            # Also check the owner
            owner = response.get("Owner", {})
            owner_id = owner.get("ID")
            if owner_id and owner_id not in allowed_users:
                allowed_users.append(owner_id)
            
            logging.info(f"ACL extracted - Users: {len(allowed_users)}, Groups: {len(allowed_groups)}")
            return allowed_users, allowed_groups
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchKey":
                logging.warning(f"Object not found: s3://{bucket}/{key}")
                return [], []
            elif error_code == "AccessDenied":
                logging.warning(f"Access denied when fetching ACL for s3://{bucket}/{key}")
                return [], []
            else:
                logging.error(f"Error fetching ACL for s3://{bucket}/{key}: {e}")
                return [], []
        except Exception as e:
            logging.error(f"Unexpected error fetching ACL for s3://{bucket}/{key}: {e}")
            return [], []

