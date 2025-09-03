#!/usr/bin/env python3
"""
Test script for the YouTube scraper optimizations
"""

import os
import sys
sys.path.append('/Users/am/ytscraper')

from ytscrp import generate_video_id_hash, check_existing_file, sanitize_filename

def test_video_id_hash():
    """Test video ID hash generation"""
    print("Testing video ID hash generation...")
    
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s",
    ]
    
    for url in test_urls:
        hash_val = generate_video_id_hash(url)
        print(f"URL: {url}")
        print(f"Hash: {hash_val}")
        print()

def test_filename_sanitization():
    """Test filename sanitization"""
    print("Testing filename sanitization...")
    
    test_filenames = [
        "Normal Video Title",
        "Video with / slash and \\ backslash",
        "Video: with < > characters and | pipe",
        "Video with \" quotes and * asterisk",
        "Video with ? question mark",
        "Very long video title that exceeds the maximum length limit and should be truncated to prevent filesystem issues" * 3
    ]
    
    for filename in test_filenames:
        sanitized = sanitize_filename(filename)
        print(f"Original: {filename[:50]}{'...' if len(filename) > 50 else ''}")
        print(f"Sanitized: {sanitized}")
        print()

def test_duplicate_check():
    """Test duplicate file checking"""
    print("Testing duplicate file checking...")
    
    # Create a test directory with some fake files
    test_dir = "/tmp/test_downloads"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create some test files
    test_files = [
        "Rick Astley - Never Gonna Give You Up_abc123def456.mp3",
        "Another Video_xyz789uvw012.mp4",
        "Some Random Video.webm"
    ]
    
    for filename in test_files:
        with open(os.path.join(test_dir, filename), 'w') as f:
            f.write("test content")
    
    # Test duplicate checking
    test_cases = [
        ("Rick Astley - Never Gonna Give You Up", "abc123def456", True),  # Should find audio file
        ("Rick Astley - Never Gonna Give You Up", "abc123def456", False),  # Should find audio file but looking for video
        ("Another Video", "xyz789uvw012", False),  # Should find video file
        ("Non-existent Video", "nonexistent123", True),  # Should not find anything
        ("Some Random Video", "unknown", False),  # Should find by title similarity
    ]
    
    for title, video_hash, audio_only in test_cases:
        result = check_existing_file(test_dir, title, video_hash, audio_only)
        print(f"Title: {title}")
        print(f"Hash: {video_hash}")
        print(f"Audio Only: {audio_only}")
        print(f"Found: {result}")
        print()
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)

if __name__ == "__main__":
    print("=== YouTube Scraper Optimization Tests ===\n")
    
    test_video_id_hash()
    test_filename_sanitization()
    test_duplicate_check()
    
    print("=== Tests Complete ===")
