import sounddevice as sd
import numpy as np
import webrtcvad
import wave
import threading
from queue import Queue
from typing import Optional, Callable
import time

class VoiceProcessor:
    def __init__(self, sample_rate: int = 16000, frame_duration: int = 30):
        """
        Initialize voice processor
        
        Args:
            sample_rate: Audio sample rate in Hz
            frame_duration: Frame duration in milliseconds
        """
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.vad = webrtcvad.Vad(3)  # Aggressiveness mode 3
        self.audio_queue = Queue()
        self.is_recording = False
        
        # Calculate frame size
        self.frame_size = int(sample_rate * frame_duration / 1000)
        
    def start_recording(self, callback: Optional[Callable] = None):
        """Start recording audio"""
        self.is_recording = True
        self.recording_thread = threading.Thread(
            target=self._record_audio,
            args=(callback,)
        )
        self.recording_thread.start()
        
    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        if hasattr(self, 'recording_thread'):
            self.recording_thread.join()
            
    def _record_audio(self, callback: Optional[Callable]):
        """Record audio in a separate thread"""
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.int16,
            blocksize=self.frame_size,
            callback=self._audio_callback
        ):
            while self.is_recording:
                if not self.audio_queue.empty() and callback:
                    audio_frame = self.audio_queue.get()
                    if self.is_speech(audio_frame):
                        callback(audio_frame)
                time.sleep(0.001)
                
    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio input"""
        if status:
            print(f"Audio callback status: {status}")
        self.audio_queue.put(indata.copy())
        
    def is_speech(self, audio_frame: np.ndarray) -> bool:
        """
        Detect if audio frame contains speech
        
        Args:
            audio_frame: Audio frame data
            
        Returns:
            bool: True if speech detected
        """
        try:
            frame_bytes = audio_frame.tobytes()
            return self.vad.is_speech(frame_bytes, self.sample_rate)
        except Exception as e:
            print(f"Speech detection error: {e}")
            return False
            
    def save_audio(self, audio_data: np.ndarray, filename: str):
        """
        Save audio data to WAV file
        
        Args:
            audio_data: Audio data to save
            filename: Output filename
        """
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
