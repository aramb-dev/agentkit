"""File storage and management for AgentKit."""

import os
import uuid
import hashlib
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import shutil


class FileManager:
    """Manages file storage, retrieval, and metadata."""

    def __init__(self, storage_dir: str = "uploads"):
        self.storage_dir = Path(storage_dir)
        self.metadata_dir = self.storage_dir / "metadata"
        self.files_dir = self.storage_dir / "files"

        # Create directories if they don't exist
        self.storage_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
        self.files_dir.mkdir(exist_ok=True)

    def generate_file_id(self, content: bytes, filename: str) -> str:
        """
        Generate cryptographically secure file ID.
        Uses secrets module for unpredictable, non-enumerable IDs.
        """
        import secrets
        # Use cryptographically secure random token
        # 32 bytes = 256 bits of entropy, URL-safe base64 encoded
        return secrets.token_urlsafe(32)

    async def store_file(
        self,
        content: bytes,
        filename: str,
        content_type: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Store file permanently and return file metadata.

        Returns:
            Dict with file_id, storage_path, metadata_path, etc.
        """
        # Generate unique file ID
        file_id = self.generate_file_id(content, filename)

        # Create file paths
        file_extension = Path(filename).suffix
        stored_filename = f"{file_id}{file_extension}"
        file_path = self.files_dir / stored_filename
        metadata_path = self.metadata_dir / f"{file_id}.json"

        # Store the actual file
        with open(file_path, "wb") as f:
            f.write(content)

        # Create metadata
        metadata = {
            "file_id": file_id,
            "original_filename": filename,
            "stored_filename": stored_filename,
            "content_type": content_type,
            "file_size": len(content),
            "upload_timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "file_path": str(file_path),
            "metadata_path": str(metadata_path),
        }

        # Store metadata
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    def get_file_metadata(self, file_id: str) -> Optional[Dict]:
        """Retrieve file metadata by file ID."""
        metadata_path = self.metadata_dir / f"{file_id}.json"

        if not metadata_path.exists():
            return None

        with open(metadata_path, "r") as f:
            return json.load(f)

    def get_file_content(self, file_id: str) -> Optional[bytes]:
        """Retrieve file content by file ID."""
        metadata = self.get_file_metadata(file_id)
        if not metadata:
            return None

        file_path = Path(metadata["file_path"])
        if not file_path.exists():
            return None

        with open(file_path, "rb") as f:
            return f.read()

    def list_user_files(self, user_id: Optional[str] = None) -> List[Dict]:
        """List all files for a user (or all files if user_id is None)."""
        files = []

        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)

                # Filter by user if specified
                if user_id is None or metadata.get("user_id") == user_id:
                    files.append(metadata)
            except (json.JSONDecodeError, FileNotFoundError):
                continue

        # Sort by upload timestamp (newest first)
        files.sort(key=lambda x: x["upload_timestamp"], reverse=True)
        return files

    def delete_file(self, file_id: str) -> bool:
        """Delete a file and its metadata."""
        metadata = self.get_file_metadata(file_id)
        if not metadata:
            return False

        try:
            # Delete the actual file
            file_path = Path(metadata["file_path"])
            if file_path.exists():
                file_path.unlink()

            # Delete metadata
            metadata_path = Path(metadata["metadata_path"])
            if metadata_path.exists():
                metadata_path.unlink()

            return True
        except Exception:
            return False

    def cleanup_old_files(self, days_old: int = 30) -> int:
        """Delete files older than specified days. Returns count of deleted files."""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_count = 0

        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)

                upload_date = datetime.fromisoformat(metadata["upload_timestamp"])

                if upload_date < cutoff_date:
                    if self.delete_file(metadata["file_id"]):
                        deleted_count += 1
            except (json.JSONDecodeError, FileNotFoundError, ValueError):
                continue

        return deleted_count

    def get_storage_stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        total_files = len(list(self.metadata_dir.glob("*.json")))
        total_size = 0

        for file_path in self.files_dir.iterdir():
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }


# Global file manager instance
file_manager = FileManager()
