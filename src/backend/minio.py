import threading
import urllib3
import logging
from typing import Optional, Dict
from minio import Minio, MinioAdmin
from minio.error import S3Error
import requests
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from main import config
from exceptions import InternalError


logger = logging.getLogger(__name__)


@dataclass
class MinioConfig:
    """Configuration for MinIO client"""
    endpoint: str
    access_key: str
    secret_key: str
    secure: bool
    bucket: str
    ext_url_api: Optional[str] = None
    region: str = "us-east-1"
    
    @classmethod
    def from_settings(cls, settings: dict) -> "MinioConfig":
        """Create config from settings dictionary with validation"""
        raw_endpoint = settings.get("MINIO_ENDPOINT", "")
        if not raw_endpoint:
            raise ValueError("MINIO_ENDPOINT is required")
        
        # Parse endpoint
        endpoint = raw_endpoint.replace("https://", "").replace("http://", "").rstrip("/")
        secure = raw_endpoint.startswith("https://")
        
        # Validate credentials
        access_key = settings.get("MINIO_ROOT", "").strip()
        secret_key = settings.get("MINIO_ROOT_PASSWORD", "").strip()
        
        if not access_key or not secret_key:
            raise ValueError("MINIO_ROOT and MINIO_ROOT_PASSWORD are required")
        
        bucket = settings.get("MINIO_BUCKET", "").strip()
        if not bucket:
            raise ValueError("MINIO_BUCKET is required")
        
        return cls(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            bucket=bucket,
            ext_url_api=settings.get("MINIO_EXT_URL_API"),
            region=settings.get("MINIO_REGION", "us-east-1")
        )


class MinioClientSingleton:
    """
    Thread-safe singleton for MinIO clients with lazy initialization.
    Provides both regular and admin clients, plus personalized client creation.
    """
    
    _lock = threading.Lock()
    _initialized = False
    _client: Optional[Minio] = None
    _admin: Optional[MinioAdmin] = None
    _config: Optional[MinioConfig] = None
    
    @classmethod
    def _initialize(cls) -> None:
        """Initialize MinIO clients with proper configuration"""
        with cls._lock:
            if cls._initialized:
                return
            
            try:
                # Load and validate configuration
                cls._config = MinioConfig.from_settings(config.settings)
                
                # Create connection pool
                timeout = urllib3.Timeout(
                    connect=urllib3.Timeout.DEFAULT_TIMEOUT,
                    read=10.0
                )
                
                pool = urllib3.PoolManager(
                    num_pools=5,
                    maxsize=20,
                    block=True,
                    retries=urllib3.Retry(total=3),
                    timeout=timeout,
                )
                
                # Create main client with region to avoid signature issues
                cls._client = Minio(
                    endpoint=cls._config.endpoint,
                    access_key=cls._config.access_key,
                    secret_key=cls._config.secret_key,
                    secure=cls._config.secure,
                    http_client=pool,
                    region=cls._config.region
                )
                
                # Create admin client
                cls._admin = MinioAdmin(
                    endpoint=cls._config.endpoint,
                    credentials=cls._client._provider,
                    secure=cls._config.secure,
                    http_client=pool,
                )
                
                # Pre-cache region for default bucket to avoid lookup issues
                try:
                    cls._client._region_map[cls._config.bucket] = cls._config.region
                except Exception as e:
                    logger.warning(f"Could not pre-cache region: {e}")
                
                cls._initialized = True
                logger.info("MinIO clients initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize MinIO clients: {e}")
                raise InternalError(f"MinIO initialization failed: {str(e)}")
    
    @classmethod
    def get_client(cls) -> Minio:
        """Get the singleton Minio client instance"""
        if not cls._initialized:
            cls._initialize()
        return cls._client
    
    @classmethod
    def get_admin(cls) -> MinioAdmin:
        """Get the singleton MinioAdmin client instance"""
        if not cls._initialized:
            cls._initialize()
        return cls._admin
    
    @classmethod
    def get_config(cls) -> MinioConfig:
        """Get the MinIO configuration"""
        if not cls._initialized:
            cls._initialize()
        return cls._config
    
    @classmethod
    def get_personalized_client(cls, token: str) -> Minio:
        """
        Create a personalized MinIO client using STS temporary credentials.
        
        Args:
            token: JWT token for authentication
            
        Returns:
            Minio client with temporary credentials
            
        Raises:
            InternalError: If STS authentication fails
        """
        if not cls._initialized:
            cls._initialize()
        
        if not token:
            raise ValueError("Token is required for personalized client")
        
        sts_params = {
            "Action": "AssumeRoleWithWebIdentity",
            "WebIdentityToken": token,
            "Version": "2011-06-15",
            "DurationSeconds": "3600",
        }
        
        try:
            sts_url = cls._config.ext_url_api or f"{'https' if cls._config.secure else 'http'}://{cls._config.endpoint}"
            response = requests.post(url=sts_url, params=sts_params, timeout=10)
                        
            if response.status_code not in range(200, 300):
                logger.error(f"STS failed: {response.status_code} - {response.text[:200]}")
                raise InternalError(f"STS authentication failed with status {response.status_code}")
            
            # Parse XML response
            root = ET.fromstring(response.text)
            credentials = root.find(".//{https://sts.amazonaws.com/doc/2011-06-15/}Credentials")
            
            if credentials is None:
                raise InternalError("No credentials found in STS response")
            
            # Extract credentials
            access_key_elem = credentials.find("{https://sts.amazonaws.com/doc/2011-06-15/}AccessKeyId")
            secret_key_elem = credentials.find("{https://sts.amazonaws.com/doc/2011-06-15/}SecretAccessKey")
            session_token_elem = credentials.find("{https://sts.amazonaws.com/doc/2011-06-15/}SessionToken")
            
            if not all([access_key_elem, secret_key_elem, session_token_elem]):
                raise InternalError("Incomplete credentials in STS response")
            
            # Create personalized client
            personalized_client = Minio(
                endpoint=cls._config.endpoint,
                access_key=access_key_elem.text,
                secret_key=secret_key_elem.text,
                session_token=session_token_elem.text,
                secure=cls._config.secure,
                region=cls._config.region
            )
            
            # Pre-cache region for this client too
            personalized_client._region_map[cls._config.bucket] = cls._config.region
            
            return personalized_client
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse STS XML response: {e}")
            raise InternalError(f"STS response parsing failed: {str(e)}")
        except requests.RequestException as e:
            logger.error(f"STS request failed: {e}")
            raise InternalError(f"STS request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating personalized client: {e}")
            raise InternalError(f"Failed to create personalized client: {str(e)}")
    
    @classmethod
    def health_check(cls) -> Dict[str, any]:
        """
        Perform health check on MinIO connection.
        
        Returns:
            Dictionary with health status and details
        """
        try:
            if not cls._initialized:
                cls._initialize()
            
            # Try listing buckets
            buckets = cls._client.list_buckets()
            bucket_names = [b.name for b in buckets]
            
            # Check if default bucket exists
            bucket_exists = cls._config.bucket in bucket_names
            
            return {
                "healthy": True,
                "endpoint": cls._config.endpoint,
                "secure": cls._config.secure,
                "buckets": bucket_names,
                "default_bucket": cls._config.bucket,
                "default_bucket_exists": bucket_exists
            }
        except Exception as e:
            logger.error(f"MinIO health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (mainly for testing)"""
        with cls._lock:
            cls._initialized = False
            cls._client = None
            cls._admin = None
            cls._config = None


# Global instances - lazy initialized on first access
MINIO_CLIENT = MinioClientSingleton.get_client
MINIO_ADMIN = MinioClientSingleton.get_admin
MINIO_CONFIG = MinioClientSingleton.get_config
MINIO = MinioClientSingleton