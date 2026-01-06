# Audio Transcription - Speaker Diarization Implementation Guide

## Overview

This document describes the proposed solution for adding speaker diarization (speaker identification) to the Audio Transcription tool. Currently, the tool uses OpenAI Whisper API which provides plain text transcription without speaker identification.

## Current Implementation

- **Tool**: OpenAI Whisper API (`whisper-1` model)
- **Output**: Plain text transcription
- **Limitation**: Does not identify or separate different speakers

## Problem Statement

Users may want transcripts that identify different speakers, especially for:
- Interviews
- Podcasts with multiple hosts
- Conference calls
- Meetings
- Panel discussions

## Proposed Solution: Combine Whisper with Speaker Diarization

### Approach

Use a two-step process:
1. **Speaker Diarization**: Identify who spoke when using `pyannote.audio`
2. **Transcription**: Transcribe each speaker segment using OpenAI Whisper API
3. **Combine**: Format output with speaker labels

### Implementation Details

#### Required Dependencies

```python
# Add to requirements.txt
pyannote.audio>=3.1.0
torch>=2.0.0
torchaudio>=2.0.0
```

#### Required Configuration

- **HuggingFace Token**: Required to access `pyannote.audio` models
  - Sign up at https://huggingface.co/
  - Accept terms for `pyannote/speaker-diarization-3.1`
  - Generate access token
  - Add to `.env`: `HUGGINGFACE_API_TOKEN=your_token_here`

#### Code Implementation

```python
from pyannote.audio import Pipeline
import torch
from openai import OpenAI
import tempfile
import subprocess
import os
import shutil
import logging

logger = logging.getLogger(__name__)

def _transcribe_with_speakers(file_path, api_key, hf_token):
    """
    Transcribe audio with speaker identification.
    
    Args:
        file_path: Path to audio file
        api_key: OpenAI API key
        hf_token: HuggingFace API token
    
    Returns:
        Formatted transcript with speaker labels, or None on error
    """
    try:
        # 1. Initialize speaker diarization pipeline
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
        
        # 2. Run diarization to identify speaker segments
        diarization = pipeline(file_path)
        
        # 3. Process each speaker segment
        transcript_parts = []
        temp_dir = tempfile.mkdtemp()
        
        try:
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                # Extract audio segment for this speaker turn
                segment_path = os.path.join(
                    temp_dir, 
                    f"segment_{turn.start:.2f}_{turn.end:.2f}.wav"
                )
                
                # Extract segment using ffmpeg
                subprocess.run([
                    'ffmpeg', '-i', file_path,
                    '-ss', str(turn.start),
                    '-t', str(turn.end - turn.start),
                    '-acodec', 'copy',
                    segment_path,
                    '-y'
                ], check=True, capture_output=True)
                
                # Transcribe segment with Whisper
                client = OpenAI(api_key=api_key, timeout=600.0)
                with open(segment_path, 'rb') as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=None
                    )
                
                # Format with speaker label
                transcript_parts.append(
                    f"**Speaker {speaker}** ({turn.start:.1f}s - {turn.end:.1f}s):\n{transcript.text}"
                )
        
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir)
        
        return "\n\n".join(transcript_parts)
        
    except Exception as e:
        logger.error(f'Speaker diarization error: {str(e)}')
        return None
```

#### UI Modifications

Add an optional checkbox in the template:

```html
<div class="form-group" style="margin-top: 1rem;">
    <label>
        <input type="checkbox" name="identify_speakers" id="identify_speakers">
        Identify different speakers (requires additional processing time)
    </label>
    <p style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
        Separate transcript by speaker. Useful for interviews, podcasts, and meetings.
    </p>
</div>
```

#### View Function Update

```python
def audio_transcription(request):
    """Transcribe audio files using OpenAI Whisper API"""
    # ... existing validation code ...
    
    identify_speakers = request.POST.get('identify_speakers') == 'on'
    hf_token = settings.HUGGINGFACE_API_TOKEN if identify_speakers else None
    
    if identify_speakers and not hf_token:
        messages.error(
            request, 
            'Speaker identification requires HuggingFace API token. Please configure HUGGINGFACE_API_TOKEN in settings.'
        )
        return render(request, 'text_converter/audio_transcription.html', {
            'openai_available': OPENAI_AVAILABLE,
        })
    
    # Transcribe with or without speaker identification
    if identify_speakers:
        transcription_text = _transcribe_with_speakers(
            input_path, 
            api_key, 
            hf_token
        )
    else:
        transcription_text, detected_language = _transcribe_audio(
            input_path, 
            api_key
        )
    
    # ... rest of the function ...
```

## Considerations

### Advantages
- Provides speaker-separated transcripts
- Uses existing Whisper API for transcription
- Open-source diarization model (pyannote.audio)
- Can be made optional (checkbox)

### Challenges
1. **Additional Dependencies**
   - Requires PyTorch (large dependency)
   - Requires HuggingFace authentication
   - More complex setup

2. **Performance**
   - Slower processing (diarization + multiple API calls)
   - Higher memory usage
   - More CPU-intensive

3. **Cost**
   - More OpenAI API calls (one per speaker segment)
   - Potential increase in API costs for multi-speaker audio

4. **Accuracy**
   - Depends on audio quality
   - Speaker separation may not be perfect
   - May require tuning for specific use cases

5. **File Size Limits**
   - Still subject to OpenAI's 25MB file size limit
   - May need to split large files before processing

## Alternative Solutions

### 1. AssemblyAI API
- **Pros**: Built-in speaker diarization, single API call
- **Cons**: Different API, additional cost, migration required

### 2. Deepgram API
- **Pros**: Speaker diarization support, good accuracy
- **Cons**: Different API, additional cost, migration required

### 3. Rev.ai
- **Pros**: Professional transcription service with speaker identification
- **Cons**: More expensive, different API

## Recommendation

**Current Status**: Not implemented - solution documented for future consideration

**When to Implement**:
- If user demand for speaker identification is high
- If resources allow for additional dependencies and processing time
- If HuggingFace token can be securely configured

**Implementation Priority**: Low-Medium (nice-to-have feature)

## Testing Checklist

If implementing, test with:
- [ ] Single speaker audio
- [ ] Two-speaker conversation
- [ ] Multi-speaker (3+ speakers) audio
- [ ] Audio with background noise
- [ ] Audio with overlapping speech
- [ ] Different audio formats (MP3, WAV, M4A, OGG)
- [ ] Audio files of various lengths
- [ ] Error handling (missing HF token, API failures)

## References

- [pyannote.audio Documentation](https://github.com/pyannote/pyannote-audio)
- [OpenAI Whisper API Documentation](https://platform.openai.com/docs/guides/speech-to-text)
- [HuggingFace pyannote Models](https://huggingface.co/pyannote)

## Last Updated

2025-01-XX - Initial documentation created

