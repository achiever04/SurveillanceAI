"""
IPFS storage manager for decentralized evidence storage
"""
import ipfshttpclient
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
from loguru import logger
from config.settings import settings


class IPFSStorageManager:
    """Manage evidence storage on IPFS"""
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        gateway_url: Optional[str] = None
    ):
        """
        Initialize IPFS manager
        
        Args:
            api_url: IPFS API URL (default from settings)
            gateway_url: IPFS gateway URL (default from settings)
        """
        self.api_url = api_url or settings.IPFS_API
        self.gateway_url = gateway_url or settings.IPFS_GATEWAY
        self.client = None
        self.is_connected = False
        
        self._connect()
    
    def _connect(self):
        """Establish connection to IPFS node"""
        try:
            self.client = ipfshttpclient.connect(self.api_url)
            
            # Test connection
            version = self.client.version()
            self.is_connected = True
            
            logger.info(f"Connected to IPFS node: {version['Version']}")
        except Exception as e:
            logger.error(f"Failed to connect to IPFS: {e}")
            self.client = None
            self.is_connected = False
    
    def upload_file(self, file_path: str) -> Optional[str]:
        """
        Upload file to IPFS
        
        Args:
            file_path: Path to file
            
        Returns:
            IPFS CID or None if failed
        """
        if not self.is_connected:
            logger.warning("IPFS not connected, attempting reconnection...")
            self._connect()
            
            if not self.is_connected:
                return None
        
        try:
            result = self.client.add(file_path)
            cid = result['Hash']
            
            logger.info(f"Uploaded file to IPFS: {cid}")
            return cid
        except Exception as e:
            logger.error(f"Failed to upload file to IPFS: {e}")
            return None
    
    def upload_bytes(self, data: bytes, filename: str = "data") -> Optional[str]:
        """
        Upload raw bytes to IPFS
        
        Args:
            data: Byte data
            filename: Optional filename
            
        Returns:
            IPFS CID or None
        """
        if not self.is_connected:
            self._connect()
            if not self.is_connected:
                return None
        
        try:
            result = self.client.add_bytes(data)
            cid = result
            
            logger.info(f"Uploaded {len(data)} bytes to IPFS: {cid}")
            return cid
        except Exception as e:
            logger.error(f"Failed to upload bytes to IPFS: {e}")
            return None
    
    def upload_json(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Upload JSON data to IPFS
        
        Args:
            data: Dictionary to upload
            
        Returns:
            IPFS CID or None
        """
        try:
            json_bytes = json.dumps(data, indent=2).encode('utf-8')
            return self.upload_bytes(json_bytes, "data.json")
        except Exception as e:
            logger.error(f"Failed to upload JSON to IPFS: {e}")
            return None
    
    def download_file(self, cid: str, output_path: str) -> bool:
        """
        Download file from IPFS
        
        Args:
            cid: IPFS CID
            output_path: Where to save file
            
        Returns:
            True if successful
        """
        if not self.is_connected:
            self._connect()
            if not self.is_connected:
                return False
        
        try:
            data = self.client.cat(cid)
            
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output, 'wb') as f:
                f.write(data)
            
            logger.info(f"Downloaded file from IPFS: {cid} -> {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download from IPFS: {e}")
            return False
    
    def download_bytes(self, cid: str) -> Optional[bytes]:
        """
        Download raw bytes from IPFS
        
        Args:
            cid: IPFS CID
            
        Returns:
            Byte data or None
        """
        if not self.is_connected:
            self._connect()
            if not self.is_connected:
                return None
        
        try:
            data = self.client.cat(cid)
            logger.info(f"Downloaded {len(data)} bytes from IPFS: {cid}")
            return data
        except Exception as e:
            logger.error(f"Failed to download from IPFS: {e}")
            return None
    
    def download_json(self, cid: str) -> Optional[Dict[str, Any]]:
        """
        Download and parse JSON from IPFS
        
        Args:
            cid: IPFS CID
            
        Returns:
            Parsed dictionary or None
        """
        try:
            data = self.download_bytes(cid)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
        except Exception as e:
            logger.error(f"Failed to download JSON from IPFS: {e}")
            return None
    
    def pin_content(self, cid: str) -> bool:
        """
        Pin content to prevent garbage collection
        
        Args:
            cid: IPFS CID to pin
            
        Returns:
            True if successful
        """
        if not self.is_connected:
            return False
        
        try:
            self.client.pin.add(cid)
            logger.info(f"Pinned content: {cid}")
            return True
        except Exception as e:
            logger.error(f"Failed to pin content: {e}")
            return False
    
    def unpin_content(self, cid: str) -> bool:
        """
        Unpin content (allows garbage collection)
        
        Args:
            cid: IPFS CID to unpin
            
        Returns:
            True if successful
        """
        if not self.is_connected:
            return False
        
        try:
            self.client.pin.rm(cid)
            logger.info(f"Unpinned content: {cid}")
            return True
        except Exception as e:
            logger.error(f"Failed to unpin content: {e}")
            return False
    
    def list_pins(self) -> List[str]:
        """
        List all pinned content
        
        Returns:
            List of pinned CIDs
        """
        if not self.is_connected:
            return []
        
        try:
            pins = self.client.pin.ls()
            cids = list(pins['Keys'].keys())
            logger.info(f"Found {len(cids)} pinned items")
            return cids
        except Exception as e:
            logger.error(f"Failed to list pins: {e}")
            return []
    
    def get_file_stat(self, cid: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics about file/directory
        
        Args:
            cid: IPFS CID
            
        Returns:
            Statistics dictionary or None
        """
        if not self.is_connected:
            return None
        
        try:
            stat = self.client.files.stat(f'/ipfs/{cid}')
            return {
                'size': stat['Size'],
                'hash': stat['Hash'],
                'type': stat['Type']
            }
        except Exception as e:
            logger.error(f"Failed to get file stat: {e}")
            return None
    
    def verify_content(self, cid: str, expected_hash: str) -> bool:
        """
        Verify content matches expected hash
        
        Args:
            cid: IPFS CID
            expected_hash: Expected SHA-256 hash
            
        Returns:
            True if content matches hash
        """
        import hashlib
        
        data = self.download_bytes(cid)
        if not data:
            return False
        
        actual_hash = hashlib.sha256(data).hexdigest()
        return actual_hash == expected_hash
    
    def upload_directory(self, dir_path: str) -> Optional[str]:
        """
        Upload entire directory to IPFS
        
        Args:
            dir_path: Path to directory
            
        Returns:
            Root CID or None
        """
        if not self.is_connected:
            return None
        
        try:
            result = self.client.add(dir_path, recursive=True)
            
            # Get root CID (last entry)
            if isinstance(result, list):
                root_cid = result[-1]['Hash']
            else:
                root_cid = result['Hash']
            
            logger.info(f"Uploaded directory to IPFS: {root_cid}")
            return root_cid
        except Exception as e:
            logger.error(f"Failed to upload directory: {e}")
            return None
    
    def get_gateway_url(self, cid: str) -> str:
        """
        Get HTTP gateway URL for CID
        
        Args:
            cid: IPFS CID
            
        Returns:
            Gateway URL
        """
        return f"{self.gateway_url}/ipfs/{cid}"
    
    def check_connection(self) -> bool:
        """
        Check if IPFS connection is active
        
        Returns:
            True if connected
        """
        if not self.client:
            return False
        
        try:
            self.client.version()
            return True
        except:
            return False
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to IPFS
        
        Returns:
            True if reconnection successful
        """
        logger.info("Attempting to reconnect to IPFS...")
        self._connect()
        return self.is_connected
    
    def get_node_info(self) -> Optional[Dict[str, Any]]:
        """
        Get IPFS node information
        
        Returns:
            Node info dictionary or None
        """
        if not self.is_connected:
            return None
        
        try:
            version = self.client.version()
            id_info = self.client.id()
            
            return {
                "version": version['Version'],
                "peer_id": id_info['ID'],
                "addresses": id_info['Addresses']
            }
        except Exception as e:
            logger.error(f"Failed to get node info: {e}")
            return None
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.client:
            try:
                self.client.close()
            except:
                pass