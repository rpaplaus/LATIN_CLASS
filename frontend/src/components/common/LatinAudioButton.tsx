import React, { useState, useRef, useEffect } from 'react';
import { Volume2, Loader2, AlertCircle } from 'lucide-react';
import { mediaApi } from '../../api/mediaApi';
import { useToast } from '../../context/ToastContext';

export interface LatinAudioButtonProps {
  text: string;
  audioUrl?: string | null;
  audioBase64?: string | null;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  label?: string;
  onError?: (error: Error | string) => void;
}

export const LatinAudioButton: React.FC<LatinAudioButtonProps> = ({
  text,
  audioUrl,
  audioBase64,
  size = 'md',
  className = '',
  label,
  onError,
}) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [hasError, setHasError] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const { showToast } = useToast();

  // Cleanup audio playback on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
        audioRef.current = null;
      }
    };
  }, []);

  const handleError = (msg: string, rawError?: unknown) => {
    console.warn(`[LatinAudioButton] ${msg}`, rawError || '');
    setIsLoading(false);
    setIsPlaying(false);
    setHasError(true);
    setErrorMessage(msg);
    if (onError) {
      onError(rawError instanceof Error ? rawError : msg);
    }
    showToast(msg, 'error');
  };

  const handlePlayAudio = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isPlaying || isLoading) return;

    // Reset previous error state
    setHasError(false);
    setErrorMessage(null);
    setIsLoading(true);

    let src = '';

    try {
      if (audioBase64) {
        const mime = audioBase64.startsWith('UklGR') ? 'audio/wav' : 'audio/mpeg';
        src = `data:${mime};base64,${audioBase64}`;
      } else if (audioUrl) {
        src = audioUrl;
      } else {
        const ttsData = await mediaApi.getTTSAudio(text);
        if (ttsData.audio_base64) {
          const mime =
            ttsData.mime_type ||
            (ttsData.audio_base64.startsWith('UklGR') ? 'audio/wav' : 'audio/mpeg');
          src = `data:${mime};base64,${ttsData.audio_base64}`;
        } else if (ttsData.audio_url) {
          src = ttsData.audio_url;
        } else {
          throw new Error('Nenhum dado de áudio retornado pelo servidor.');
        }
      }
    } catch (err: any) {
      const is404 = err?.response?.status === 404;
      const msg = is404
        ? `Áudio de "${text}" não encontrado no repositório (404).`
        : `Falha ao carregar a pronúncia de "${text}". Verifique a conexão.`;
      handleError(msg, err);
      return;
    }

    if (!src) {
      handleError(`Caminho de áudio inválido para "${text}".`);
      return;
    }

    // Stop and clean any previously active audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    const audio = new Audio(src);
    audioRef.current = audio;

    let hasEndedOrFailed = false;

    // Safety timeout: prevent spinning indefinitely if browser stalls
    const safetyTimeout = setTimeout(() => {
      if (!hasEndedOrFailed && isLoading) {
        hasEndedOrFailed = true;
        audio.pause();
        handleError(`Tempo limite excedido ao reproduzir a pronúncia de "${text}".`);
      }
    }, 9000);

    audio.onplay = () => {
      setIsLoading(false);
      setIsPlaying(true);
    };

    audio.onplaying = () => {
      setIsLoading(false);
      setIsPlaying(true);
    };

    audio.onended = () => {
      hasEndedOrFailed = true;
      clearTimeout(safetyTimeout);
      setIsPlaying(false);
      setIsLoading(false);
    };

    audio.onerror = async () => {
      // Fallback: If pre-configured audioUrl failed (e.g. 404), dynamically request fresh TTS generation
      if (!audioBase64 && audioUrl && !hasEndedOrFailed) {
        try {
          const ttsData = await mediaApi.getTTSAudio(text);
          if (ttsData.audio_base64 || ttsData.audio_url) {
            const mime =
              ttsData.mime_type ||
              (ttsData.audio_base64?.startsWith('UklGR') ? 'audio/wav' : 'audio/mpeg');
            const fallbackSrc = ttsData.audio_base64
              ? `data:${mime};base64,${ttsData.audio_base64}`
              : ttsData.audio_url;
            const fallbackAudio = new Audio(fallbackSrc);
            audioRef.current = fallbackAudio;
            fallbackAudio.onplay = () => {
              setIsLoading(false);
              setIsPlaying(true);
            };
            fallbackAudio.onended = () => {
              clearTimeout(safetyTimeout);
              setIsPlaying(false);
              setIsLoading(false);
            };
            fallbackAudio.onerror = () => {
              clearTimeout(safetyTimeout);
              setIsPlaying(false);
              setIsLoading(false);
              handleError(`Falha ao reproduzir a pronúncia de "${text}".`);
            };
            await fallbackAudio.play();
            return;
          }
        } catch {
          // Fall through to standard error handler
        }
      }

      hasEndedOrFailed = true;
      clearTimeout(safetyTimeout);
      const mediaErr = audio.error;
      let detail = `Não foi possível reproduzir a pronúncia de "${text}".`;
      if (mediaErr) {
        if (mediaErr.code === MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED) {
          detail = `Formato de áudio de "${text}" não suportado ou arquivo não encontrado (404).`;
        } else if (mediaErr.code === MediaError.MEDIA_ERR_NETWORK) {
          detail = `Erro de conexão ao carregar o áudio de "${text}".`;
        } else if (mediaErr.code === MediaError.MEDIA_ERR_DECODE) {
          detail = `Falha na decodificação do áudio de "${text}".`;
        }
      }
      handleError(detail, mediaErr);
    };

    try {
      const playPromise = audio.play();
      if (playPromise !== undefined) {
        await playPromise;
      }
    } catch (err: any) {
      hasEndedOrFailed = true;
      clearTimeout(safetyTimeout);
      if (err?.name === 'NotAllowedError') {
        handleError('Reprodução de áudio bloqueada pelas permissões do navegador.', err);
      } else {
        handleError(`Falha ao reproduzir o áudio de "${text}".`, err);
      }
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

  const getButtonTitle = () => {
    if (hasError) {
      return errorMessage
        ? `${errorMessage} (Clique para tentar novamente)`
        : `Erro ao reproduzir pronúncia de "${text}". Clique para tentar novamente.`;
    }
    return label || `Ouvir pronúncia clássica de "${text}"`;
  };

  return (
    <button
      type="button"
      onClick={handlePlayAudio}
      disabled={isLoading}
      title={getButtonTitle()}
      className={`inline-flex items-center justify-center rounded-full transition-all duration-200 ${
        isPlaying
          ? 'bg-amber-500 text-stone-900 shadow-md shadow-amber-500/20 scale-105 animate-pulse'
          : hasError
          ? 'bg-stone-800/70 hover:bg-stone-700/80 text-stone-400 hover:text-stone-200 border border-stone-600/70 hover:border-amber-500/40 ring-1 ring-stone-600/50'
          : 'bg-stone-800/80 hover:bg-amber-500/20 text-stone-300 hover:text-amber-400 border border-stone-700/60 hover:border-amber-500/40'
      } ${sizeClasses[size]} ${className}`}
      aria-label={label || `Ouvir pronúncia clássica de ${text}`}
    >
      {isLoading ? (
        <Loader2 size={iconSizes[size]} className="animate-spin text-amber-400" />
      ) : hasError ? (
        <AlertCircle
          size={iconSizes[size]}
          className="text-stone-400 hover:text-stone-200 transition-colors"
        />
      ) : (
        <Volume2
          size={iconSizes[size]}
          className={isPlaying ? 'animate-bounce text-stone-900' : ''}
        />
      )}
      {label && <span className="ml-1.5 font-medium">{label}</span>}
    </button>
  );
};
