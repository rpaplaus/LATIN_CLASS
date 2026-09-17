import React, { useState } from 'react';
import {
  X,
  Sparkles,
  AlertCircle,
  RotateCcw,
  BookOpen,
} from 'lucide-react';
import { useAudioRecorder } from '../../hooks/useAudioRecorder';
import { PronunciationRecordButton } from './PronunciationRecordButton';
import { LatinAudioButton } from '../common/LatinAudioButton';
import { mediaApi } from '../../api/mediaApi';
import { PronunciationEvaluationResponse } from '../../types/media';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

interface PronunciationLabModalProps {
  isOpen: boolean;
  onClose: () => void;
  targetText: string;
  translation?: string;
  phoneticHint?: string;
}

export const PronunciationLabModal: React.FC<PronunciationLabModalProps> = ({
  isOpen,
  onClose,
  targetText,
  translation,
  phoneticHint,
}) => {
  const {
    status: recorderStatus,
    audioBlob,
    audioUrl,
    durationSeconds,
    errorMessage: recorderError,
    startRecording,
    stopRecording,
    resetRecording,
  } = useAudioRecorder();

  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [evaluationResult, setEvaluationResult] =
    useState<PronunciationEvaluationResponse | null>(null);
  const [evalError, setEvalError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleEvaluate = async () => {
    if (!audioBlob) return;
    setIsEvaluating(true);
    setEvalError(null);

    try {
      const result = await mediaApi.evaluatePronunciation(audioBlob, targetText);
      setEvaluationResult(result);
    } catch (err) {
      console.error('Erro na avaliação de pronúncia:', err);
      setEvalError(
        'Não foi possível processar o áudio com o Magister. Tente novamente.'
      );
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleReset = () => {
    resetRecording();
    setEvaluationResult(null);
    setEvalError(null);
  };

  const getScoreBadge = (score: number) => {
    if (score >= 85) {
      return {
        variant: 'success' as const,
        label: 'Optime! (Excelente)',
        color: 'text-emerald-700 bg-emerald-50 border-emerald-300',
      };
    }
    if (score >= 70) {
      return {
        variant: 'warning' as const,
        label: 'Bene factum! (Bom)',
        color: 'text-amber-800 bg-amber-50 border-amber-300',
      };
    }
    return {
      variant: 'stone' as const,
      label: 'Labora diligenter! (Aprimorar)',
      color: 'text-rose-700 bg-rose-50 border-rose-300',
    };
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-2xl bg-[#fdfbf7] rounded-3xl shadow-2xl border border-amber-300/60 overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header - Classical Roman Styling */}
        <div className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-stone-900 via-stone-800 to-amber-950 text-white border-b border-amber-500/30">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-amber-500/20 border border-amber-400/40 text-amber-300">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] font-serif font-bold uppercase tracking-widest text-amber-400">
                • SCHOLA PRONUNTIATIONIS •
              </span>
              <h3 className="font-serif text-lg font-bold text-stone-100">
                Laboratório de Pronúncia Latina
              </h3>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-stone-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Target Latin Phrase Card */}
          <div className="p-5 rounded-2xl bg-white border border-amber-200/90 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-xl pointer-events-none" />
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="space-y-1">
                <span className="text-[11px] font-bold uppercase tracking-wider text-amber-800">
                  Frase Canônica para Treino
                </span>
                <p className="font-serif text-2xl font-bold text-stone-900 leading-snug">
                  "{targetText}"
                </p>
                {translation && (
                  <p className="text-xs sm:text-sm text-stone-500 italic">
                    ↳ Tradução: {translation}
                  </p>
                )}
              </div>

              {/* Hear Master Native Audio Button */}
              <div className="flex-shrink-0 flex items-center gap-2">
                <LatinAudioButton
                  text={targetText}
                  size="lg"
                  label="Ouvir Magister"
                />
              </div>
            </div>

            {/* Classical Pronuntiatio Restituta Hint */}
            <div className="mt-3 pt-3 border-t border-stone-100 flex items-start gap-2 text-xs text-stone-600">
              <BookOpen className="w-4 h-4 text-amber-700 flex-shrink-0 mt-0.5" />
              <span>
                {phoneticHint ||
                  'Norma Restituída (Pronuntiatio Restituta): A letra C é sempre dura /k/ (ex: Caesar = "Káissar"), e V tem som suave de /w/ (ex: veni = "uéni").'}
              </span>
            </div>
          </div>

          {/* Interactive Voice Recorder Section */}
          <div className="p-6 rounded-2xl bg-gradient-to-b from-stone-50 to-amber-50/30 border border-stone-200 text-center space-y-4">
            <PronunciationRecordButton
              status={isEvaluating ? 'processing' : recorderStatus}
              durationSeconds={durationSeconds}
              onStart={startRecording}
              onStop={stopRecording}
              onReset={handleReset}
              disabled={isEvaluating}
            />

            {/* Recorder Errors */}
            {recorderError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-600" />
                <span>{recorderError}</span>
              </div>
            )}

            {/* Ready State Actions (Listen Own Audio + Evaluate) */}
            {recorderStatus === 'ready' && !evaluationResult && (
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2 animate-fadeIn">
                {audioUrl && (
                  <audio
                    src={audioUrl}
                    controls
                    className="h-10 max-w-xs rounded-lg shadow-sm"
                  />
                )}
                <Button
                  variant="primary"
                  onClick={handleEvaluate}
                  isLoading={isEvaluating}
                  className="shadow-md"
                >
                  <Sparkles className="w-4 h-4 mr-2 text-amber-300" />
                  <span>Avaliar com IA do Magister</span>
                </Button>
              </div>
            )}
          </div>

          {/* Evaluation Error Banner */}
          {evalError && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{evalError}</span>
            </div>
          )}

          {/* EVALUATION RESULTS CARD */}
          {evaluationResult && (
            <div className="p-5 rounded-2xl bg-white border border-amber-200 shadow-md space-y-5 animate-fadeIn">
              {/* Score & Badge Row */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-stone-100">
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-stone-500">
                    Acurácia Fonética Geral
                  </span>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="font-serif text-3xl font-extrabold text-stone-900">
                      {Math.round(evaluationResult.overall_score)}%
                    </span>
                    <Badge
                      variant={getScoreBadge(evaluationResult.overall_score).variant}
                      size="md"
                    >
                      {getScoreBadge(evaluationResult.overall_score).label}
                    </Badge>
                  </div>
                </div>

                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleReset}
                  className="self-start sm:self-auto text-xs"
                >
                  <RotateCcw className="w-3.5 h-3.5 mr-1" />
                  <span>Gravar Novamente</span>
                </Button>
              </div>

              {/* Transcription Comparison */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-stone-50 border border-stone-200">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-stone-500">
                    Texto Esperado (Norma)
                  </p>
                  <p className="font-serif text-sm font-semibold text-stone-900 mt-0.5">
                    {evaluationResult.target_text}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-amber-50/50 border border-amber-200">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-amber-800">
                    Sua Pronúncia (Transcrição STT)
                  </p>
                  <p className="font-serif text-sm font-semibold text-amber-950 mt-0.5">
                    "{evaluationResult.transcribed_text}"
                  </p>
                </div>
              </div>

              {/* Magister Feedback & Phonetic Tips */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border-l-4 border-amber-500 space-y-1">
                <p className="text-xs font-serif font-bold text-amber-950 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-700" />
                  <span>Parecer do Magister Latium</span>
                </p>
                <p className="text-xs sm:text-sm text-stone-800 leading-relaxed">
                  {evaluationResult.phonetic_tips}
                </p>
              </div>

              {/* Word-by-Word Breakdown */}
              {(evaluationResult.word_breakdown || []).length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-serif text-xs font-bold uppercase tracking-wider text-stone-700">
                    Decomposição Vocálica e Consoantes (Pronuntiatio Restituta)
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {evaluationResult.word_breakdown.map((item, idx) => {
                      const wordScore = Math.round((item.accuracy ?? 0) * 100);
                      return (
                        <div
                          key={idx}
                          className="p-3 rounded-xl border border-stone-200 bg-stone-50/60 flex flex-col justify-between text-xs space-y-1"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-serif font-bold text-stone-900 text-sm">
                              {item.word}
                            </span>
                            <span
                              className={`font-mono font-bold px-1.5 py-0.5 rounded text-[11px] ${
                                wordScore >= 80
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : wordScore >= 60
                                  ? 'bg-amber-100 text-amber-800'
                                  : 'bg-rose-100 text-rose-800'
                              }`}
                            >
                              {wordScore}%
                            </span>
                          </div>
                          <p className="text-[11px] text-stone-500 capitalize">
                            Status: <span className="font-semibold">{item.status}</span>
                          </p>
                          {item.phonetic_rule_note && (
                            <p className="text-[10px] text-amber-900 bg-amber-100/60 p-1 rounded">
                              {item.phonetic_rule_note}
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 bg-stone-100/80 border-t border-stone-200 flex justify-end">
          <Button variant="secondary" onClick={onClose}>
            Fechar Laboratório
          </Button>
        </div>
      </div>
    </div>
  );
};
