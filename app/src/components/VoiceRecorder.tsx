import React, { useState, useRef, useCallback } from 'react';
import styled from 'styled-components';
import { useConnection, useWallet } from '@solana/wallet-adapter-react';
import { Program } from '@project-serum/anchor';

const RecorderContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  backdrop-filter: blur(10px);
`;

const RecordButton = styled.button<{ isRecording: boolean }>`
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: none;
  background: ${props => props.isRecording ? '#ff4444' : '#4CAF50'};
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

  &:hover {
    transform: scale(1.1);
  }

  &:active {
    transform: scale(0.95);
  }
`;

const StatusText = styled.p`
  margin-top: 1rem;
  color: white;
  font-size: 1.1rem;
`;

const VoiceVisualizer = styled.canvas`
  width: 300px;
  height: 100px;
  margin: 1rem 0;
`;

interface VoiceRecorderProps {
  program: Program;
  onRecordingComplete: (audioBlob: Blob) => void;
}

const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ program, onRecordingComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const visualizerRef = useRef<HTMLCanvasElement>(null);
  const animationFrame = useRef<number>();
  const { connection } = useConnection();
  const { publicKey } = useWallet();

  const drawVisualizer = useCallback((canvasCtx: CanvasRenderingContext2D, dataArray: Uint8Array, bufferLength: number) => {
    const WIDTH = canvasCtx.canvas.width;
    const HEIGHT = canvasCtx.canvas.height;

    canvasCtx.fillStyle = 'rgb(0, 0, 0)';
    canvasCtx.fillRect(0, 0, WIDTH, HEIGHT);

    const barWidth = (WIDTH / bufferLength) * 2.5;
    let barHeight;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      barHeight = dataArray[i] / 2;

      const gradient = canvasCtx.createLinearGradient(0, 0, 0, HEIGHT);
      gradient.addColorStop(0, '#4CAF50');
      gradient.addColorStop(1, '#1B5E20');

      canvasCtx.fillStyle = gradient;
      canvasCtx.fillRect(x, HEIGHT - barHeight, barWidth, barHeight);

      x += barWidth + 1;
    }
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setAudioStream(stream);

      const recorder = new MediaRecorder(stream);
      mediaRecorder.current = recorder;
      audioChunks.current = [];

      recorder.ondataavailable = (event) => {
        audioChunks.current.push(event.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
        onRecordingComplete(audioBlob);

        // Store on Solana if wallet is connected
        if (publicKey) {
          try {
            // Convert blob to base64
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);
            reader.onloadend = async () => {
              const base64Audio = reader.result as string;
              
              // Call your program to store the voice data
              // This is a placeholder - implement actual storage logic
              await program.methods
                .storeVoiceData(base64Audio)
                .accounts({
                  // Add your program accounts here
                })
                .rpc();
            };
          } catch (error) {
            console.error('Error storing voice data:', error);
          }
        }
      };

      // Set up audio analyzer
      const audioCtx = new AudioContext();
      const analyser = audioCtx.createAnalyser();
      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);
      analyser.fftSize = 256;
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const canvas = visualizerRef.current;
      if (canvas) {
        const canvasCtx = canvas.getContext('2d');
        if (canvasCtx) {
          const animate = () => {
            animationFrame.current = requestAnimationFrame(animate);
            analyser.getByteFrequencyData(dataArray);
            drawVisualizer(canvasCtx, dataArray, bufferLength);
          };
          animate();
        }
      }

      recorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      audioStream?.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      if (animationFrame.current) {
        cancelAnimationFrame(animationFrame.current);
      }
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <RecorderContainer>
      <VoiceVisualizer ref={visualizerRef} />
      <RecordButton
        isRecording={isRecording}
        onClick={toggleRecording}
        aria-label={isRecording ? 'Stop Recording' : 'Start Recording'}
      >
        <i className={`fas fa-${isRecording ? 'stop' : 'microphone'}`} />
      </RecordButton>
      <StatusText>
        {isRecording ? 'Recording...' : 'Click to start recording'}
      </StatusText>
    </RecorderContainer>
  );
};

export default VoiceRecorder;
