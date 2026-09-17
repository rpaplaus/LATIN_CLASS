import React, { useEffect, useState } from 'react';
import {
  Swords,
  Shield,
  RotateCw,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ArrowRight,
  Award,
  RefreshCw,
} from 'lucide-react';
import { arenaApi } from '../api/arenaApi';
import {
  ArenaChallengeResponse,
  ArenaEvaluationResponse,
  ArenaFlashcard,
} from '../types/arena';
import { LatinAudioButton } from '../components/common/LatinAudioButton';
import { useToast } from '../context/ToastContext';

interface ArenaPageProps {
  onBackToDashboard?: () => void;
  onNavigateToTabularium?: () => void;
}

export const ArenaPage: React.FC<ArenaPageProps> = ({
  onBackToDashboard,
  onNavigateToTabularium,
}) => {
  const [challenge, setChallenge] = useState<ArenaChallengeResponse | null>(null);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [isFlipped, setIsFlipped] = useState<boolean>(false);
  const [showHint, setShowHint] = useState<boolean>(false);
  const [studentAnswer, setStudentAnswer] = useState<string>('');
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [evaluation, setEvaluation] = useState<ArenaEvaluationResponse | null>(null);
  const [roundResults, setRoundResults] = useState<
    Array<{ card: ArenaFlashcard; eval: ArenaEvaluationResponse }>
  >([]);
  const [isRoundFinished, setIsRoundFinished] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const { showToast } = useToast();

  const loadChallenge = async (quiet = false) => {
    if (!quiet) setIsLoading(true);
    setIsFlipped(false);
    setShowHint(false);
    setStudentAnswer('');
    setEvaluation(null);
    setCurrentIndex(0);
    setRoundResults([]);
    setIsRoundFinished(false);

    try {
      const data = await arenaApi.generateChallenge();
      setChallenge(data);
    } catch (err) {
      console.error('[ArenaPage] Erro ao carregar desafio:', err);
      showToast('Falha ao abrir a Arena Latium. Verifique a conexão.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadChallenge();
  }, []);

  const currentCard: ArenaFlashcard | null =
    challenge && challenge.cards.length > currentIndex
      ? challenge.cards[currentIndex]
      : null;

  // Handle typing evaluation with Censor Míni
  const handleSubmitAnswer = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!challenge || !currentCard || !studentAnswer.trim() || isEvaluating) return;

    setIsEvaluating(true);
    try {
      const res = await arenaApi.evaluateCard({
        topic_key: challenge.topic_key,
        card_id: currentCard.id,
        latin: currentCard.latin,
        expected_answer: currentCard.translation,
        student_answer: studentAnswer.trim(),
      });
      setEvaluation(res);
      setIsFlipped(true); // Flip card to show evaluation
      setRoundResults((prev) => [...prev, { card: currentCard, eval: res }]);
    } catch (err) {
      console.error('[ArenaPage] Erro ao avaliar resposta:', err);
      showToast('Falha ao enviar resposta para o Censor Latium.', 'error');
    } finally {
      setIsEvaluating(false);
    }
  };

  // Handle self-evaluation buttons (Quick study without typing)
  const handleSelfEvaluate = async (isCorrect: boolean) => {
    if (!challenge || !currentCard || isEvaluating) return;

    setIsEvaluating(true);
    const answerSubmitted = isCorrect ? currentCard.translation : 'Não lembrei';

    try {
      const res = await arenaApi.evaluateCard({
        topic_key: challenge.topic_key,
        card_id: currentCard.id,
        latin: currentCard.latin,
        expected_answer: currentCard.translation,
        student_answer: answerSubmitted,
      });
      setEvaluation(res);
      setRoundResults((prev) => [...prev, { card: currentCard, eval: res }]);
    } catch (err) {
      console.error('[ArenaPage] Erro na autoavaliação:', err);
    } finally {
      setIsEvaluating(false);
    }
  };

  // Move to the next card or finish round
  const handleNextCard = () => {
    if (!challenge) return;

    if (currentIndex + 1 < challenge.cards.length) {
      setIsFlipped(false);
      setShowHint(false);
      setStudentAnswer('');
      setEvaluation(null);
      setCurrentIndex((prev) => prev + 1);
    } else {
      setIsRoundFinished(true);
    }
  };

  const correctCount = roundResults.filter((r) => r.eval.is_correct).length;
  const initialMastery = challenge?.current_mastery ?? 0.5;
  const latestMastery =
    roundResults.length > 0
      ? roundResults[roundResults.length - 1].eval.new_mastery
      : initialMastery;
  const masteryDelta = Math.round((latestMastery - initialMastery) * 100);

  return (
    <div className="w-full max-w-2xl mx-auto px-4 py-6 space-y-6 animate-fade-in flex flex-col items-center justify-center min-h-[calc(100vh-140px)]">
      {/* 1. Arena Header Badge */}
      <div className="w-full flex items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-serif font-bold uppercase tracking-wider text-[11px] bg-rose-950/80 text-rose-300 border border-rose-800/60 shadow-xs">
            <Swords className="w-3.5 h-3.5 text-rose-400" />
            Arena Latium • Combate Adaptativo
          </span>
          <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono tracking-wider bg-amber-950/60 text-amber-300 border border-amber-800/40">
            ⚡ Prompt Míni (Baixo Custo)
          </span>
        </div>

        <button
          onClick={() => loadChallenge(true)}
          className="text-stone-400 hover:text-stone-200 text-xs flex items-center gap-1 transition-colors px-2 py-1 rounded-lg bg-stone-900/60 border border-stone-800"
          title="Gerar novo desafio"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Reiniciar</span>
        </button>
      </div>

      {isLoading ? (
        <div className="w-full py-24 text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-rose-950/40 border border-rose-800/50 mx-auto flex items-center justify-center text-3xl shadow-lg animate-pulse">
            ⚔️
          </div>
          <div className="space-y-1">
            <h3 className="font-serif font-bold text-lg text-stone-100">
              Forjando o Combate na Arena...
            </h3>
            <p className="text-xs text-stone-400 font-sans max-w-sm mx-auto">
              O Magister Latium está consultando sua taxa de erro (EMA) para selecionar suas maiores fraquezas.
            </p>
          </div>
        </div>
      ) : isRoundFinished ? (
        /* 2. Victory & Triumph Screen */
        <div className="w-full bg-gradient-to-b from-[#1f1a17] via-[#1a1513] to-[#120f0d] rounded-3xl p-6 sm:p-8 border border-amber-700/50 shadow-2xl text-center space-y-6 animate-scale-up">
          <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-amber-600 via-rose-600 to-amber-400 mx-auto p-1 shadow-xl flex items-center justify-center">
            <div className="w-full h-full rounded-full bg-[#161210] flex items-center justify-center text-4xl">
              🏆
            </div>
          </div>

          <div className="space-y-2">
            <span className="text-[11px] font-serif uppercase tracking-widest text-amber-400 font-bold">
              • COMBATE CONCLUÍDO •
            </span>
            <h2 className="text-2xl sm:text-3xl font-serif font-bold text-stone-100 tracking-wide">
              TRIUMPHUS IN ARENA!
            </h2>
            <p className="text-xs sm:text-sm text-stone-300 font-serif max-w-md mx-auto">
              Você enfrentou suas vulnerabilidades em <strong>{challenge?.topic_label}</strong> e refinou seu domínio do Latim.
            </p>
          </div>

          {/* Combat Metrics Box */}
          <div className="grid grid-cols-2 gap-3 bg-stone-900/60 p-4 rounded-2xl border border-stone-800/80 text-left">
            <div>
              <span className="text-[11px] uppercase tracking-wider text-stone-400 font-sans block">
                Acertos na Rodada
              </span>
              <span className="text-2xl font-serif font-bold text-amber-300 mt-0.5 block">
                {correctCount} de 3 cartões
              </span>
            </div>

            <div>
              <span className="text-[11px] uppercase tracking-wider text-stone-400 font-sans block">
                Evolução da Maestria
              </span>
              <span className="text-2xl font-serif font-bold text-emerald-400 mt-0.5 block flex items-center gap-1">
                {Math.round(latestMastery * 100)}%
                {masteryDelta !== 0 && (
                  <span
                    className={`text-xs font-sans px-1.5 py-0.5 rounded-full ${
                      masteryDelta > 0
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        : 'bg-rose-950 text-rose-300 border border-rose-800'
                    }`}
                  >
                    {masteryDelta > 0 ? `+${masteryDelta}%` : `${masteryDelta}%`}
                  </span>
                )}
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <button
              onClick={() => loadChallenge()}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-rose-700 to-amber-700 hover:from-rose-600 hover:to-amber-600 text-white font-serif font-bold text-sm shadow-lg transition-all hover:scale-105"
            >
              <Swords className="w-4 h-4" />
              Novo Combate na Arena
            </button>

            {onBackToDashboard && (
              <button
                onClick={onBackToDashboard}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-stone-800/80 hover:bg-stone-700/80 text-stone-200 text-xs font-semibold border border-stone-700 transition-all"
              >
                Voltar ao Painel
              </button>
            )}

            {onNavigateToTabularium && (
              <button
                onClick={onNavigateToTabularium}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-stone-800/80 hover:bg-stone-700/80 text-amber-300 text-xs font-semibold border border-amber-800/40 transition-all"
              >
                Ver no Tabularium
              </button>
            )}
          </div>
        </div>
      ) : currentCard ? (
        /* 3. Centered Single-Card Minigame */
        <div className="w-full space-y-4">
          {/* Target Topic & Stepper Indicator */}
          <div className="flex items-center justify-between text-xs text-stone-400 px-1">
            <div className="flex items-center gap-2 truncate">
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
              <span className="font-serif text-stone-300 font-semibold truncate">
                {challenge?.topic_label}
              </span>
              <span className="text-[10px] text-rose-400 font-mono">
                (Maestria: {Math.round(initialMastery * 100)}%)
              </span>
            </div>

            <div className="font-mono text-stone-400 tracking-wider">
              Desafio {currentIndex + 1} de {challenge?.cards.length}
            </div>
          </div>

          {/* Stepper Progress Bar */}
          <div className="w-full h-1.5 bg-stone-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-rose-600 to-amber-500 transition-all duration-500"
              style={{
                width: `${((currentIndex + 1) / (challenge?.cards.length || 3)) * 100}%`,
              }}
            />
          </div>

          {/* 3D Flashcard Container with Flip Animation */}
          <div
            className="w-full min-h-[360px] sm:min-h-[400px] relative perspective-1000 select-none cursor-pointer group"
            onClick={() => {
              if (!isFlipped && !evaluation) {
                // Clicking outside inputs flips the card for self-study
                setIsFlipped(true);
              }
            }}
          >
            <div
              className={`w-full h-full absolute inset-0 transition-transform duration-700 transform-style-3d rounded-3xl ${
                isFlipped ? 'rotate-y-180' : ''
              }`}
            >
              {/* --- FRONT OF CARD --- */}
              <div className="w-full h-full absolute inset-0 backface-hidden bg-gradient-to-br from-[#241e1a] via-[#1d1815] to-[#14110f] rounded-3xl p-6 sm:p-8 border border-amber-800/40 shadow-2xl flex flex-col justify-between text-[#fdfbf7]">
                {/* Top Badges & Audio Pronunciation */}
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-serif tracking-wider uppercase text-amber-500/90 font-bold flex items-center gap-1">
                    <Shield className="w-3.5 h-3.5" />
                    Latim Clássico
                  </span>

                  <div onClick={(e) => e.stopPropagation()}>
                    <LatinAudioButton
                      text={currentCard.latin}
                      audioUrl={currentCard.audio_url}
                      size="md"
                    />
                  </div>
                </div>

                {/* Central Latin Prompt */}
                <div className="py-6 text-center space-y-3">
                  <h2 className="text-2xl sm:text-3xl lg:text-4xl font-serif font-bold text-stone-100 tracking-wide leading-snug drop-shadow-sm">
                    {currentCard.latin}
                  </h2>

                  {/* Optional Grammar Hint */}
                  {showHint ? (
                    <div className="inline-block px-3 py-1.5 rounded-xl bg-amber-950/70 border border-amber-700/50 text-amber-300 text-xs font-serif animate-fade-in">
                      💡 {currentCard.hint}
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowHint(true);
                      }}
                      className="inline-flex items-center gap-1 text-[11px] text-stone-400 hover:text-amber-300 transition-colors"
                    >
                      <HelpCircle className="w-3 h-3" />
                      Revelar Dica Gramatical
                    </button>
                  )}
                </div>

                {/* Bottom Interactive Area */}
                <div className="space-y-3" onClick={(e) => e.stopPropagation()}>
                  {/* Typing Form */}
                  <form onSubmit={handleSubmitAnswer} className="flex gap-2">
                    <input
                      type="text"
                      value={studentAnswer}
                      onChange={(e) => setStudentAnswer(e.target.value)}
                      placeholder="Digite a tradução em português..."
                      disabled={isEvaluating}
                      className="flex-1 bg-stone-900/80 border border-stone-700/80 rounded-xl px-4 py-2.5 text-sm text-stone-100 placeholder-stone-500 focus:outline-hidden focus:border-amber-500 focus:ring-1 focus:ring-amber-500 transition-all font-sans"
                    />
                    <button
                      type="submit"
                      disabled={!studentAnswer.trim() || isEvaluating}
                      className="px-4 py-2.5 rounded-xl bg-rose-700 hover:bg-rose-600 disabled:opacity-40 text-white font-serif font-bold text-xs shadow-md transition-all shrink-0 flex items-center gap-1"
                    >
                      {isEvaluating ? 'Avaliando...' : 'Avaliar'}
                    </button>
                  </form>

                  {/* Or Quick Flip Button */}
                  <div className="flex items-center justify-between text-xs text-stone-400 pt-1">
                    <span className="text-[11px]">Ou toque no cartão para memorizar:</span>
                    <button
                      type="button"
                      onClick={() => setIsFlipped(true)}
                      className="inline-flex items-center gap-1 text-amber-400 hover:text-amber-300 font-semibold"
                    >
                      <RotateCw className="w-3.5 h-3.5" />
                      Virar Carta (Flip)
                    </button>
                  </div>
                </div>
              </div>

              {/* --- BACK OF CARD --- */}
              <div className="w-full h-full absolute inset-0 backface-hidden rotate-y-180 bg-gradient-to-br from-[#1e1916] via-[#191512] to-[#120f0d] rounded-3xl p-6 sm:p-8 border border-amber-600/50 shadow-2xl flex flex-col justify-between text-[#fdfbf7]">
                {/* Back Header */}
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-serif tracking-wider uppercase text-amber-400 font-bold flex items-center gap-1">
                    <Award className="w-3.5 h-3.5" />
                    Gabarito Oficial
                  </span>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setIsFlipped(false);
                    }}
                    className="text-xs text-stone-400 hover:text-stone-200 flex items-center gap-1"
                    title="Virar para a frente"
                  >
                    <RotateCw className="w-3 h-3" />
                    Frente
                  </button>
                </div>

                {/* Canonical Answer & Feedback */}
                <div className="py-4 text-center space-y-3">
                  <span className="text-xs uppercase tracking-widest text-stone-400 block font-serif">
                    Tradução Canônica:
                  </span>
                  <h3 className="text-xl sm:text-2xl lg:text-3xl font-serif font-bold text-amber-300">
                    "{currentCard.translation}"
                  </h3>

                  {/* Feedback Card (if evaluated by Censor Míni) */}
                  {evaluation && (
                    <div
                      className={`p-3.5 rounded-xl border text-xs max-w-md mx-auto space-y-1 ${
                        evaluation.is_correct
                          ? 'bg-emerald-950/60 border-emerald-800 text-emerald-200'
                          : 'bg-rose-950/60 border-rose-800 text-rose-200'
                      }`}
                    >
                      <div className="flex items-center justify-center gap-1.5 font-bold">
                        {evaluation.is_correct ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-400" />
                        )}
                        <span>{evaluation.is_correct ? 'Optime!' : 'Atenção!'}</span>
                        <span className="opacity-75">({evaluation.score}/100)</span>
                      </div>
                      <p className="italic font-serif">{evaluation.feedback}</p>
                    </div>
                  )}

                  {/* Self-evaluation Buttons if card was flipped without typing */}
                  {!evaluation && (
                    <div
                      className="pt-2 space-y-2"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <p className="text-[11px] text-stone-400 font-serif">
                        Você lembrou a resposta correta?
                      </p>
                      <div className="flex items-center justify-center gap-3">
                        <button
                          type="button"
                          onClick={() => handleSelfEvaluate(true)}
                          disabled={isEvaluating}
                          className="px-4 py-2 rounded-xl bg-emerald-900/60 hover:bg-emerald-800/80 border border-emerald-700 text-emerald-300 text-xs font-semibold flex items-center gap-1.5 transition-all"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Acertei (+100%)
                        </button>
                        <button
                          type="button"
                          onClick={() => handleSelfEvaluate(false)}
                          disabled={isEvaluating}
                          className="px-4 py-2 rounded-xl bg-rose-900/60 hover:bg-rose-800/80 border border-rose-700 text-rose-300 text-xs font-semibold flex items-center gap-1.5 transition-all"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          Preciso Revisar
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Back Footer: Next Challenge Button */}
                <div
                  className="pt-2 border-t border-stone-800/80 flex items-center justify-between"
                  onClick={(e) => e.stopPropagation()}
                >
                  <span className="text-[11px] text-stone-400">
                    {evaluation ? 'Maestria atualizada no banco' : 'Selecione uma opção acima'}
                  </span>

                  <button
                    type="button"
                    onClick={handleNextCard}
                    disabled={!evaluation && !isFlipped}
                    className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 text-white font-serif font-bold text-xs shadow-md transition-all flex items-center gap-1.5 hover:scale-105 ml-auto"
                  >
                    <span>
                      {currentIndex + 1 < (challenge?.cards.length || 3)
                        ? 'Próximo Desafio'
                        : 'Ver Triunfo'}
                    </span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
