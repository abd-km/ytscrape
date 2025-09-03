#!/usr/bin/env python3
"""
Test script for the shared directory functionality
"""

import os
import sys
sys.path.append('/Users/am/ytscraper')

from ytscrp import get_shared_download_dir, create_task_zip_file

def test_shared_directory():
    """Test shared directory creation"""
    print("Testing shared directory creation...")
    
    # Test audio directory
    audio_dir = get_shared_download_dir(audio_only=True)
    print(f"Audio directory: {audio_dir}")
    assert os.path.exists(audio_dir), "Audio directory should exist"
    
    # Test video directory
    video_dir = get_shared_download_dir(audio_only=False)
    print(f"Video directory: {video_dir}")
    assert os.path.exists(video_dir), "Video directory should exist"
    
    # Verify they are different directories
    assert audio_dir != video_dir, "Audio and video directories should be different"
    
    print("✅ Shared directory creation works!")

def test_directory_structure():
    """Test the expected directory structure"""
    print("\nTesting directory structure...")
    
    expected_dirs = [
        "downloads/audio",
        "downloads/videos", 
        "downloads/tasks"
    ]
    
    # Create directories by calling functions
    get_shared_download_dir(audio_only=True)
    get_shared_download_dir(audio_only=False)
    os.makedirs("downloads/tasks", exist_ok=True)
    
    for expected_dir in expected_dirs:
        print(f"Checking: {expected_dir}")
        assert os.path.exists(expected_dir), f"Directory {expected_dir} should exist"
    
    print("✅ Directory structure is correct!")

def test_task_zip_creation():
    """Test task-specific zip creation with fake data"""
    print("\nTesting task-specific zip creation...")
    
    # Create some fake files in shared directories
    audio_dir = get_shared_download_dir(audio_only=True)
    video_dir = get_shared_download_dir(audio_only=False)
    
    test_files = {
        os.path.join(audio_dir, "test_audio.mp3"): "fake audio content",
        os.path.join(video_dir, "test_video.mp4"): "fake video content"
    }
    
    for file_path, content in test_files.items():
        with open(file_path, 'w') as f:
            f.write(content)
    
    # Mock video downloads data for testing
    import threading
    from ytscrp import storage_lock, video_downloads, VideoDownload
    
    test_task_id = "test_task_123"
    
    with storage_lock:
        video_downloads[test_task_id] = [
            VideoDownload(
                url="test_url_1",
                title="Test Audio",
                status="completed",
                filename="test_audio.mp3"
            ),
            VideoDownload(
                url="test_url_2", 
                title="Test Video",
                status="completed",
                filename="test_video.mp4"
            )
        ]
    
    # Test zip creation for audio files
    audio_zip_path = f"downloads/tasks/{test_task_id}_audio.zip"
    create_task_zip_file(test_task_id, audio_dir, audio_zip_path)
    
    if os.path.exists(audio_zip_path):
        print("✅ Task-specific zip creation works!")
        os.remove(audio_zip_path)  # Cleanup
    else:
        print("❌ Task-specific zip creation failed!")
    
    # Cleanup test files
    for file_path in test_files.keys():
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Cleanup video downloads
    with storage_lock:
        if test_task_id in video_downloads:
            del video_downloads[test_task_id]

if __name__ == "__main__":
    print("=== Shared Directory Implementation Tests ===\n")
    
    test_shared_directory()
    test_directory_structure() 
    test_task_zip_creation()
    
    print("\n=== Tests Complete ===")
    print("\nNew directory structure:")
    print("downloads/")
    print("├── audio/           # All audio files (shared)")
    print("├── videos/          # All video files (shared)")  
    print("└── tasks/           # Task-specific zips")
    print("    ├── task1.zip")
    print("    ├── task2.zip")
    print("    └── ...")
