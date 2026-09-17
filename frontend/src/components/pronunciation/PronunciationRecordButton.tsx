import React from 'react';
import { Mic, Square, Loader2, RefreshCw } from 'lucide-react';
import { RecordingStatus } from '../../hooks/useAudioRecorder';

interface PronunciationRecordButtonProps {
  status: RecordingStatus;
  durationSeconds: number;
  onStart: () => void;
  onStop: () => void;
  onReset: () => void;
  disabled?: boolean;
}

export const PronunciationRecordButton: React.FC<PronunciationRecordButtonProps> = ({
  status,
  durationSeconds,
  onStart,
  onStop,
  onReset,
  disabled = false,
}) => {
  const formatTime = (secs: number): string => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-col items-center justify-center gap-3">
      {/* Dynamic Main Button with Smooth Concentric Waves */}
      <div className="relative flex items-center justify-center">
        {/* Animated Outer Pulse Waves when Recording */}
        {status === 'recording' && (
          <>
            <div className="absolute w-24 h-24 rounded-full bg-rose-500/20 animate-ping pointer-events-none" />
            <div className="absolute w-20 h-20 rounded-full bg-amber-500/30 animate-pulse pointer-events-none" />
          </>
        )}

        {/* Processing State Pulsing Ring */}
        {status === 'processing' && (
          <div className="absolute w-20 h-20 rounded-full border-2 border-dashed border-amber-500/60 animate-spin pointer-events-none" />
        )}

        {/* The Action Button */}
        {status === 'recording' ? (
          <button
            type="button"
            onClick={onStop}
            className="relative z-10 w-16 h-16 rounded-full bg-gradient-to-tr from-rose-600 to-red-500 text-white shadow-xl shadow-rose-900/30 flex items-center justify-center hover:scale-105 active:scale-95 transition-all cursor-pointer group"
            title="Clique para finalizar a gravação"
          >
            <Square className="w-6 h-6 fill-white text-white group-hover:scale-90 transition-transform" />
          </button>
        ) : status === 'processing' ? (
          <div className="relative z-10 w-16 h-16 rounded-full bg-stone-800 text-amber-400 shadow-lg flex items-center justify-center border border-amber-500/30">
            <Loader2 className="w-7 h-7 animate-spin text-amber-400" />
          </div>
        ) : status === 'ready' ? (
          <button
            type="button"
            onClick={onReset}
            className="relative z-10 w-16 h-16 rounded-full bg-stone-100 hover:bg-stone-200 text-stone-700 border-2 border-stone-300 shadow-md flex items-center justify-center hover:rotate-180 transition-all cursor-pointer"
            title="Gravar novamente"
          >
            <RefreshCw className="w-6 h-6" />
          </button>
        ) : (
          <button
            type="button"
            onClick={onStart}
            disabled={disabled}
            className={`relative z-10 w-16 h-16 rounded-full bg-gradient-to-tr from-amber-600 via-amber-500 to-yellow-500 text-white shadow-xl shadow-amber-700/25 flex items-center justify-center transition-all cursor-pointer group ${
              disabled
                ? 'opacity-50 cursor-not-allowed'
                : 'hover:scale-105 hover:shadow-amber-500/40 active:scale-95'
            }`}
            title="Clique para iniciar a gravação da pronúncia"
          >
            <Mic className="w-7 h-7 group-hover:scale-110 transition-transform" />
          </button>
        )}
      </div>

      {/* Live Audio Visualizer Bars & Status Label */}
      {status === 'recording' && (
        <div className="flex flex-col items-center gap-1.5 animate-fadeIn">
          {/* Simulated Equalizer Waveform */}
          <div className="flex items-center gap-1 h-6">
            <span className="w-1 bg-rose-500 rounded-full animate-bounce [animation-delay:-0.3s] h-3" />
            <span className="w-1 bg-amber-500 rounded-full animate-bounce [animation-delay:-0.15s] h-6" />
            <span className="w-1 bg-rose-500 rounded-full animate-bounce [animation-delay:-0.4s] h-4" />
            <span className="w-1 bg-amber-500 rounded-full animate-bounce [animation-delay:-0.2s] h-5" />
            <span className="w-1 bg-rose-500 rounded-full animate-bounce [animation-delay:-0.1s] h-3" />
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            <span className="text-xs font-mono font-bold text-rose-700">
              Gravando: {formatTime(durationSeconds)}
            </span>
          </div>
          <p className="text-[11px] text-stone-500">Fale com clareza em tom natural. Clique no quadrado para avaliar.</p>
        </div>
      )}

      {status === 'processing' && (
        <div className="text-center animate-fadeIn">
          <p className="text-xs font-serif font-bold text-amber-900">
            Magister Latium avaliando fonética clássica...
          </p>
          <p className="text-[11px] text-stone-500">
            Comparando com a norma da Pronuntiatio Restituta (C=/k/, V=/w/).
          </p>
        </div>
      )}

      {status === 'inactive' && (
        <div className="text-center">
          <p className="text-xs font-serif font-semibold text-stone-800">
            Pressione o microfone e leia em voz alta
          </p>
          <p className="text-[11px] text-stone-500">
            Dica: Articule as vogais com solidez e firmeza romana.
          </p>
        </div>
      )}

      {status === 'ready' && (
        <div className="text-center">
          <p className="text-xs font-semibold text-emerald-800">
            Áudio gravado com sucesso!
          </p>
          <p className="text-[11px] text-stone-500">
            Pressione o botão de refazer para regravar ou avalie abaixo.
          </p>
        </div>
      )}
    </div>
  );
};
