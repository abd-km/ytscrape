#!/usr/bin/env python3
"""
Demonstration of how duplicate detection works with shared directories
"""

import os
import sys
sys.path.append('/Users/am/ytscraper')

from ytscrp import get_shared_download_dir, check_existing_file, generate_video_id_hash

def demo_duplicate_detection():
    """Demonstrate how duplicate detection works across tasks"""
    print("=== Duplicate Detection Demo ===\n")
    
    # Simulate two different download tasks
    print("📁 Simulating shared directory structure:")
    audio_dir = get_shared_download_dir(audio_only=True)
    video_dir = get_shared_download_dir(audio_only=False)
    
    print(f"Audio files go to: {audio_dir}")
    print(f"Video files go to: {video_dir}")
    print()
    
    # Simulate some existing files from a previous download task
    print("🎵 Simulating files from previous download task:")
    existing_files = [
        (audio_dir, "Rick Astley - Never Gonna Give You Up_dQw4w9WgXcQ.mp3"),
        (audio_dir, "Queen - Bohemian Rhapsody_fJ9rUzIMcZQ.mp3"),
        (video_dir, "Epic Nature Documentary_xyzABC123def.mp4"),
    ]
    
    for directory, filename in existing_files:
        file_path = os.path.join(directory, filename)
        with open(file_path, 'w') as f:
            f.write(f"Simulated content for {filename}")
        print(f"   Created: {filename}")
    
    print()
    
    # Now simulate a new download task trying to download the same content
    print("🔍 New download task - checking for duplicates:")
    
    test_cases = [
        {
            "title": "Rick Astley - Never Gonna Give You Up",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "audio_only": True
        },
        {
            "title": "Queen - Bohemian Rhapsody", 
            "url": "https://www.youtube.com/watch?v=fJ9rUzIMcZQ",
            "audio_only": True
        },
        {
            "title": "Epic Nature Documentary",
            "url": "https://www.youtube.com/watch?v=xyzABC123def", 
            "audio_only": False
        },
        {
            "title": "Brand New Video",
            "url": "https://www.youtube.com/watch?v=newvideo123",
            "audio_only": True
        }
    ]
    
    for case in test_cases:
        download_dir = get_shared_download_dir(case['audio_only'])
        video_id_hash = generate_video_id_hash(case['url'])
        existing_file = check_existing_file(download_dir, case['title'], video_id_hash, case['audio_only'])
        
        content_type = "🎵 Audio" if case['audio_only'] else "🎥 Video"
        
        if existing_file:
            print(f"   {content_type}: '{case['title']}' -> ✅ FOUND DUPLICATE: {existing_file}")
        else:
            print(f"   {content_type}: '{case['title']}' -> ⬇️  WILL DOWNLOAD (new file)")
    
    print()
    
    # Show the benefit
    print("💡 Benefits of shared directories:")
    print("   • Files from Task A are found when Task B runs")
    print("   • No duplicate downloads = saves bandwidth & time")
    print("   • All audio files in one place: downloads/audio/")
    print("   • All video files in one place: downloads/videos/")
    print("   • Task-specific zips still available in downloads/tasks/")
    
    # Cleanup
    print("\n🧹 Cleaning up demo files...")
    for directory, filename in existing_files:
        file_path = os.path.join(directory, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"   Removed: {filename}")

if __name__ == "__main__":
    demo_duplicate_detection()
    print("\n✅ Demo complete!")
