#!/usr/bin/env python3
"""
Test script to verify FFmpeg works correctly in Docker
Run this inside the Docker container to diagnose issues
"""
import subprocess
import shutil
import os
import tempfile

def test_ffmpeg():
    """Test FFmpeg conversion"""
    print("=" * 60)
    print("FFmpeg Diagnostic Test")
    print("=" * 60)
    
    # Find FFmpeg
    ffmpeg_path = shutil.which('ffmpeg') or '/usr/local/bin/ffmpeg'
    print(f"\n1. FFmpeg path: {ffmpeg_path}")
    print(f"   Exists: {os.path.exists(ffmpeg_path)}")
    
    # Check FFmpeg version
    print(f"\n2. FFmpeg version:")
    result = subprocess.run([ffmpeg_path, '-version'], capture_output=True, text=True)
    print(result.stdout.split('\n')[0] if result.stdout else result.stderr[:200])
    
    # Test a simple conversion command
    print(f"\n3. Testing FFmpeg conversion command...")
    print(f"   Command: {ffmpeg_path} -f lavfi -i 'sine=frequency=1000:duration=1' -f wav test.wav")
    
    result = subprocess.run(
        [ffmpeg_path, '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=1', '-f', 'wav', 'test.wav'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    print(f"   Return code: {result.returncode}")
    if result.stderr:
        print(f"   Stderr: {result.stderr[:500]}")
    if result.stdout:
        print(f"   Stdout: {result.stdout[:200]}")
    
    if os.path.exists('test.wav'):
        size = os.path.getsize('test.wav')
        print(f"   Output file created: test.wav ({size} bytes)")
        
        # Check file format
        with open('test.wav', 'rb') as f:
            magic = f.read(12)
        print(f"   Magic bytes: {magic.hex()}")
        if magic[:4] == b'RIFF' and b'WAVE' in magic:
            print("   ✓ File format verified: WAV")
        else:
            print("   ✗ File format verification failed")
        
        os.remove('test.wav')
    else:
        print("   ✗ Output file was NOT created")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_ffmpeg()

