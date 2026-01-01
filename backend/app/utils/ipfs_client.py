"""
IPFS client for decentralized file storage
"""
import ipfshttpclient
from typing import Optional
from pathlib import Path
from loguru import logger
from config.settings import settings

class IPFSClient:
    """Client for interacting with IPFS"""
    
    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize IPFS client
        
        Args:
            api_url: IPFS API URL (default from settings)
        """
        self.api_url = api_url or settings.IPFS_API
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to IPFS node"""
        try:
            self.client = ipfshttpclient.connect(self.api_url)
            logger.info(f"Connected to IPFS at {self.api_url}")
        except Exception as e:
            logger.error(f"Failed to connect to IPFS: {e}")
            self.client = None
    
    async def add_file(self, data: bytes, filename: Optional[str] = None) -> Optional[str]:
        """
        Add file to IPFS
        
        Args:
            data: File data as bytes
            filename: Optional filename
            
        Returns:
            IPFS CID or None if failed
        """
        if not self.client:
            logger.warning("IPFS client not connected")
            return None
        
        try:
            result = self.client.add_bytes(data)
            cid = result
            logger.info(f"File added to IPFS: {cid}")
            return cid
        except Exception as e:
            logger.error(f"Failed to add file to IPFS: {e}")
            return None
    
    async def add_file_from_path(self, file_path: str) -> Optional[str]:
        """
        Add file from local path to IPFS
        
        Args:
            file_path: Path to file
            
        Returns:
            IPFS CID or None
        """
        if not self.client:
            return None
        
        try:
            result = self.client.add(file_path)
            cid = result['Hash']
            logger.info(f"File {file_path} added to IPFS: {cid}")
            return cid
        except Exception as e:
            logger.error(f"Failed to add file from path: {e}")
            return None
    
    async def get_file(self, cid: str, output_path: Optional[str] = None) -> Optional[bytes]:
        """
        Get file from IPFS
        
        Args:
            cid: IPFS CID
            output_path: Optional path to save file
            
        Returns:
            File data as bytes or None
        """
        if not self.client:
            return None
        
        try:
            data = self.client.cat(cid)
            
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(data)
            
            return data
        except Exception as e:
            logger.error(f"Failed to get file from IPFS: {e}")
            return None
    
    def pin_file(self, cid: str) -> bool:
        """
        Pin file to prevent garbage collection
        
        Args:
            cid: IPFS CID
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            self.client.pin.add(cid)
            logger.info(f"File pinned: {cid}")
            return True
        except Exception as e:
            logger.error(f"Failed to pin file: {e}")
            return False
    
    def unpin_file(self, cid: str) -> bool:
        """
        Unpin file
        
        Args:
            cid: IPFS CID
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            self.client.pin.rm(cid)
            logger.info(f"File unpinned: {cid}")
            return True
        except Exception as e:
            logger.error(f"Failed to unpin file: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to IPFS"""
        if not self.client:
            return False
        
        try:
            self.client.version()
            return True
        except:
            return False