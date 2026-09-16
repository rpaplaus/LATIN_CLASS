import React, { useState } from 'react';
import { Volume2, Loader2, VolumeX } from 'lucide-react';
import { mediaApi } from '../../api/mediaApi';

interface LatinAudioButtonProps {
  text: string;
  audioUrl?: string | null;
  audioBase64?: string | null;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  label?: string;
}

export const LatinAudioButton: React.FC<LatinAudioButtonProps> = ({
  text,
  audioUrl,
  audioBase64,
  size = 'md',
  className = '',
  label,
}) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [hasError, setHasError] = useState<boolean>(false);

  const handlePlayAudio = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isPlaying || isLoading) return;

    setHasError(false);
    setIsLoading(true);

    try {
      let src: string;

      if (audioBase64) {
        src = `data:audio/mpeg;base64,${audioBase64}`;
      } else if (audioUrl) {
        src = audioUrl;
      } else {
        const ttsData = await mediaApi.getTTSAudio(text);
        src = ttsData.audio_base64
          ? `data:audio/mpeg;base64,${ttsData.audio_base64}`
          : ttsData.audio_url;
      }

      const audio = new Audio(src);

      audio.onloadeddata = () => {
        setIsLoading(false);
        setIsPlaying(true);
      };

      audio.onended = () => {
        setIsPlaying(false);
      };

      audio.onerror = () => {
        setIsLoading(false);
        setIsPlaying(false);
        setHasError(true);
      };

      await audio.play();
    } catch (err) {
      console.warn('Erro ao reproduzir pronúncia em áudio:', err);
      setIsLoading(false);
      setIsPlaying(false);
      setHasError(true);
    }
  };

  const sizeClasses = {
    sm: 'p-1.5 text-xs',
    md: 'p-2 text-sm',
    lg: 'p-2.5 text-base',
  };

  const iconSizes = {
    sm: 14,
    md: 18,
    lg: 22,
  };

  return (
    <button
      type="button"
      onClick={handlePlayAudio}
      disabled={isLoading}
      title={label || `Ouvir pronúncia clássica de "${text}"`}
      className={`inline-flex items-center justify-center rounded-full transition-all duration-200 ${
        isPlaying
          ? 'bg-amber-500 text-stone-900 shadow-md shadow-amber-500/20 scale-105 animate-pulse'
          : hasError
          ? 'bg-red-900/30 text-red-400 hover:bg-red-900/50'
          : 'bg-stone-800/80 hover:bg-amber-500/20 text-stone-300 hover:text-amber-400 border border-stone-700/60 hover:border-amber-500/40'
      } ${sizeClasses[size]} ${className}`}
      aria-label={label || `Ouvir pronúncia clássica de ${text}`}
    >
      {isLoading ? (
        <Loader2 size={iconSizes[size]} className="animate-spin text-amber-400" />
      ) : hasError ? (
        <VolumeX size={iconSizes[size]} />
      ) : (
        <Volume2
          size={iconSizes[size]}
          className={isPlaying ? 'animate-bounce' : ''}
        />
      )}
      {label && <span className="ml-1.5 font-medium">{label}</span>}
    </button>
  );
};
