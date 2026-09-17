import React, { useState } from 'react';
import { useProgress } from '../context/ProgressContext';
import { lessonApi } from '../api/lessonApi';
import { ExerciseEvaluationResponse } from '../types/evaluation';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import {
  ArrowLeft,
  BookOpen,
  HelpCircle,
  CheckCircle2,
  XCircle,
  Lightbulb,
  Award,
  Scroll,
  Sparkles,
  ArrowRight,
  Check,
  Feather,
  Layers,
  Mic,
} from 'lucide-react';
import { LatinAudioButton } from '../components/common/LatinAudioButton';
import { FlashcardModal } from '../components/flashcards/FlashcardModal';
import { PronunciationLabModal } from '../components/pronunciation/PronunciationLabModal';
import { HistoricalTriviaCard } from '../components/trivia/HistoricalTriviaCard';
import { MagisterChatDrawer } from '../components/chat/MagisterChatDrawer';
import { FloatingMagisterButton } from '../components/chat/FloatingMagisterButton';
import { flashcardApi } from '../api/flashcardApi';
import { FlashcardItem } from '../types/flashcard';
import { LessonContent } from '../types/lesson';
import {
  ExerciseHeader,
  getSafeQuestionPrompt,
  getSafeInstruction,
} from '../components/classroom/ExerciseCard';

interface ClassroomPageProps {
  onBackToDashboard: () => void;
  isReadOnly?: boolean;
  reviewLesson?: LessonContent | null;
  onBackToTabularium?: () => void;
}

interface AnswerRecord {
  isCorrect: boolean;
  answer: string;
  score: number;
  evaluation?: ExerciseEvaluationResponse;
}

export const ClassroomPage: React.FC<ClassroomPageProps> = ({
  onBackToDashboard,
  isReadOnly = false,
  reviewLesson = null,
  onBackToTabularium,
}) => {
  const { activeLesson: contextLesson, completeLesson, isLoading } = useProgress();
  const activeLesson = reviewLesson || contextLesson;
  const [activeTab, setActiveTab] = useState<'theory' | 'vocabulary' | 'exercises'>('theory');

  // Exercise runner states
  const [currentExIndex, setCurrentExIndex] = useState<number>(0);

  // Flashcards states
  const [isFlashcardsOpen, setIsFlashcardsOpen] = useState<boolean>(false);
  const [flashcards, setFlashcards] = useState<FlashcardItem[]>([]);
  const [isLoadingFlashcards, setIsLoadingFlashcards] = useState<boolean>(false);

  // Pronunciation Lab states
  const [isPronunciationOpen, setIsPronunciationOpen] = useState<boolean>(false);
  const [pronunciationText, setPronunciationText] = useState<string>('');
  const [pronunciationTranslation, setPronunciationTranslation] = useState<string | undefined>(undefined);
  const [pronunciationHint, setPronunciationHint] = useState<string | undefined>(undefined);

  const handleOpenPronunciation = (text: string, translation?: string, hint?: string) => {
    setPronunciationText(text);
    setPronunciationTranslation(translation);
    setPronunciationHint(hint);
    setIsPronunciationOpen(true);
  };

  // Magister Interactive Chat states
  const [isChatOpen, setIsChatOpen] = useState<boolean>(false);

  const handleOpenFlashcards = async () => {
    if (!activeLesson) return;
    setIsLoadingFlashcards(true);
    try {
      if (flashcards.length === 0) {
        const resp = await flashcardApi.getLessonFlashcards(activeLesson.lesson_id);
        setFlashcards(resp.flashcards);
      }
      setIsFlashcardsOpen(true);
    } catch (err) {
      console.error('Erro ao carregar flashcards:', err);
    } finally {
      setIsLoadingFlashcards(false);
    }
  };
  const [selectedOption, setSelectedOption] = useState<string>('');
  const [textAnswer, setTextAnswer] = useState<string>('');
  const [isAnswerChecked, setIsAnswerChecked] = useState<boolean>(false);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [userAnswers, setUserAnswers] = useState<Record<number, AnswerRecord>>({});
  const [isLessonFinished, setIsLessonFinished] = useState<boolean>(false);

  if (!activeLesson) {
    return (
      <div className="text-center py-16 space-y-4">
        <div className="w-16 h-16 rounded-full bg-stone-100 flex items-center justify-center mx-auto text-2xl">
          🏛️
        </div>
        <h3 className="font-serif text-xl font-bold text-slate-800">
          {isReadOnly ? 'Nenhuma lição selecionada para revisão' : 'Nenhuma lição ativa no momento'}
        </h3>
        <p className="text-stone-500 text-sm max-w-sm mx-auto">
          {isReadOnly
            ? 'Retorne ao Tabularium para selecionar um pergaminho arquivado.'
            : 'Retorne ao painel para iniciar uma aula personalizada preparada pelo Magister Latium.'}
        </p>
        <Button variant="primary" onClick={onBackToTabularium || onBackToDashboard}>
          {isReadOnly ? 'Voltar ao Tabularium' : 'Voltar ao Painel'}
        </Button>
      </div>
    );
  }

  const exercises = activeLesson.exercises || [];
  const currentEx = exercises[currentExIndex];

  const normalizeAnswer = (str: string) =>
    str
      .trim()
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

  const handleCheckAnswer = async () => {
    // Strict Guard: Never trigger evaluations or LLM calls in Read-Only Mode
    if (isReadOnly || !currentEx) return;

    // 1. Multiple choice question: Instant validation (case & accent-insensitive)
    if (currentEx.options && currentEx.options.length > 0) {
      const isCorrect =
        normalizeAnswer(selectedOption) === normalizeAnswer(currentEx.correct_answer);
      setUserAnswers((prev) => ({
        ...prev,
        [currentExIndex]: {
          isCorrect,
          answer: selectedOption,
          score: isCorrect ? 100 : 0,
        },
      }));
      setIsAnswerChecked(true);
      return;
    }

    // 2. Open-ended / Translation question: Evaluated via Censor Latium Agent
    setIsEvaluating(true);
    try {
      const evalResult = await lessonApi.evaluateExercise(activeLesson.lesson_id, {
        lesson_id: activeLesson.lesson_id,
        exercise_id: currentEx.id,
        question: currentEx.question,
        expected_answer: currentEx.correct_answer,
        student_answer: textAnswer.trim(),
        exercise_type: currentEx.exercise_type || 'translation',
      });

      setUserAnswers((prev) => ({
        ...prev,
        [currentExIndex]: {
          isCorrect: evalResult.is_correct,
          answer: textAnswer.trim(),
          score: evalResult.score,
          evaluation: evalResult,
        },
      }));
      setIsAnswerChecked(true);
    } catch (err) {
      console.error('Erro na avaliação com Censor Latium:', err);
      // Fallback comparison (case & accent-tolerant)
      const isCorrect =
        normalizeAnswer(textAnswer) === normalizeAnswer(currentEx.correct_answer);
      setUserAnswers((prev) => ({
        ...prev,
        [currentExIndex]: {
          isCorrect,
          answer: textAnswer.trim(),
          score: isCorrect ? 100 : 40,
        },
      }));
      setIsAnswerChecked(true);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleNextExercise = () => {
    if (currentExIndex < exercises.length - 1) {
      setCurrentExIndex((prev) => prev + 1);
      setSelectedOption('');
      setTextAnswer('');
      setIsAnswerChecked(false);
    } else {
      setIsLessonFinished(true);
    }
  };

  const calculateFinalScore = () => {
    if (exercises.length === 0) return 100;
    const totalScores = Object.values(userAnswers).reduce(
      (sum, a) => sum + (a.score ?? (a.isCorrect ? 100 : 0)),
      0
    );
    return Math.round(totalScores / exercises.length);
  };

  const handleFinishAndSave = async () => {
    const score = calculateFinalScore();
    await completeLesson(score);
    onBackToDashboard();
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Top Bar with Navigation & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-stone-200/80 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToTabularium || onBackToDashboard}
            className="p-2 rounded-xl hover:bg-stone-200/60 text-stone-600 transition-colors"
            title={isReadOnly ? 'Voltar ao Tabularium' : 'Voltar ao Painel'}
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold text-amber-700 uppercase tracking-wider">
                {activeLesson.module_title}
              </span>
              {isReadOnly && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 border border-amber-300/80 text-amber-900 uppercase tracking-wider">
                  Revisão Histórica
                </span>
              )}
            </div>
            <h2 className="font-serif text-xl sm:text-2xl font-bold text-slate-900 leading-tight">
              {activeTab === 'exercises'
                ? activeLesson.lesson_title.replace(/\s*\([^)]*(?:est|sunt|sum|esse|-am|-ae|-us|-i)[^)]*\)/gi, '')
                : activeLesson.lesson_title}
            </h2>
          </div>
        </div>

        {/* Section Tabs */}
        <div className="flex bg-stone-100 p-1 rounded-xl border border-stone-200 text-xs font-semibold self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('theory')}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'theory'
                ? 'bg-white text-stone-900 shadow-sm'
                : 'text-stone-500 hover:text-stone-800'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Teoria</span>
          </button>
          <button
            onClick={() => setActiveTab('vocabulary')}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'vocabulary'
                ? 'bg-white text-stone-900 shadow-sm'
                : 'text-stone-500 hover:text-stone-800'
            }`}
          >
            <Scroll className="w-3.5 h-3.5" />
            <span>Vocabulário ({activeLesson.vocabulary?.length || 0})</span>
          </button>
          <button
            onClick={() => setActiveTab('exercises')}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'exercises'
                ? 'bg-white text-stone-900 shadow-sm'
                : 'text-stone-500 hover:text-stone-800'
            }`}
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Exercícios ({exercises.length})</span>
          </button>
        </div>
      </div>

      {/* Tabularium Read-Only Banner */}
      {isReadOnly && (
        <div className="bg-amber-500/10 border border-amber-600/30 text-amber-950 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-100 border border-amber-300 flex items-center justify-center flex-shrink-0">
              <Scroll className="w-5 h-5 text-amber-800" />
            </div>
            <div>
              <h4 className="font-serif font-bold text-sm text-slate-900">
                🏛️ Modo de Revisão Histórica (Tabularium)
              </h4>
              <p className="text-xs text-stone-600 mt-0.5">
                Você está revisando esta aula com o gabarito oficial liberado. O Censor Latium está desativado (Custo Zero de IA).
              </p>
            </div>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={onBackToTabularium || onBackToDashboard}
            className="self-start sm:self-auto text-xs flex-shrink-0"
          >
            Voltar ao Tabularium
          </Button>
        </div>
      )}

      {/* TAB 1: TEORIA & HISTÓRIA */}
      {activeTab === 'theory' && (
        <div className="space-y-6">
          {/* Pedagogical Goal Banner */}
          <Card className="p-5 bg-amber-50/60 border-amber-200/80">
            <div className="flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-serif font-bold text-amber-950 text-sm">
                  Objetivo Pedagógico do Magister
                </h4>
                <p className="text-xs sm:text-sm text-amber-900/90 mt-1">
                  {activeLesson.pedagogical_goal}
                </p>
              </div>
            </div>
          </Card>

          {/* Theory Sections */}
          <div className="space-y-4">
            {activeLesson.theory_sections?.map((section, idx) => (
              <Card key={idx} className="p-6 border-stone-200 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-stone-100 font-serif font-bold text-xs flex items-center justify-center text-stone-700">
                    {idx + 1}
                  </span>
                  <h3 className="font-serif font-bold text-lg text-slate-900">
                    {section.topic}
                  </h3>
                </div>

                <div className="prose prose-stone text-sm sm:text-base text-stone-700 leading-relaxed">
                  <p>{section.explanation}</p>
                </div>

                {section.rule_summary && (
                  <div className="mt-3 p-3.5 rounded-xl bg-stone-50 border border-stone-200 text-stone-800 text-xs sm:text-sm font-medium">
                    <span className="font-bold text-amber-800">Regra Gramatical: </span>
                    {section.rule_summary}
                  </div>
                )}
              </Card>
            ))}
          </div>

          {/* Historical Context */}
          {activeLesson.historical_context && (
            <Card className="p-6 border-stone-200 bg-[#faf8f4]">
              <h4 className="font-serif font-bold text-slate-900 text-base mb-2 flex items-center gap-2">
                🏛️ Contexto Cultural e Histórico Romano
              </h4>
              <p className="text-stone-600 text-sm leading-relaxed">
                {activeLesson.historical_context}
              </p>
            </Card>
          )}

          {/* Historical Trivia ("Você Sabia?") Microlearning Cards */}
          {activeLesson.historical_trivia && activeLesson.historical_trivia.length > 0 ? (
            <div className="space-y-4">
              {activeLesson.historical_trivia.map((trivia, tIdx) => (
                <HistoricalTriviaCard key={tIdx} trivia={trivia} />
              ))}
            </div>
          ) : (
            <HistoricalTriviaCard
              trivia={{
                title: 'A Pronúncia Viva no Fórum e os Sons de Roma',
                content:
                  'Na Roma republicana e imperial clássica (Pronuntiatio Restituta), a consoante "C" possuía som oclusivo velar /k/ universalmente — Cícero era chamado de "Kíkero" e César de "Káissar". A consoante "V" soava como a semivogal /w/ (como em "água"), fazendo com que a famosa frase "Veni, vidi, vici" ressoasse como "Uéni, uídi, uíki".',
                century_or_period: 'Século I a.C.',
                source_reference: 'Quintiliano, Institutio Oratoria (I.7) & Cícero, De Oratore',
              }}
            />
          )}

          {/* Teacher Tip */}
          {activeLesson.teacher_tip && (
            <div className="p-4 rounded-xl bg-orange-50/70 border border-orange-200 flex items-start gap-3">
              <Lightbulb className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-orange-800">
                  Consilium Magistri (Dica do Professor)
                </p>
                <p className="text-xs sm:text-sm text-orange-950 mt-0.5">
                  {activeLesson.teacher_tip}
                </p>
              </div>
            </div>
          )}

          <div className="flex justify-end pt-2">
            <Button
              variant="primary"
              onClick={() => setActiveTab('vocabulary')}
              className="shadow-sm"
            >
              <span>Ver Vocabulário da Lição</span>
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </Button>
          </div>
        </div>
      )}

      {/* TAB 2: VOCABULÁRIO & EXEMPLOS */}
      {activeTab === 'vocabulary' && (
        <div className="space-y-6">
          {/* Flashcards Interactive Launcher */}
          <div className="flex flex-col sm:flex-row items-center justify-between p-4 rounded-2xl bg-gradient-to-r from-amber-500/15 via-amber-500/5 to-transparent border border-amber-500/30 gap-3 shadow-sm">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-xl bg-amber-500/20 text-amber-800 border border-amber-500/30">
                <Layers size={22} />
              </div>
              <div>
                <h4 className="font-serif font-bold text-amber-950 text-base flex items-center gap-2">
                  <span>Tabulae Vocabularii (Flashcards 3D)</span>
                </h4>
                <p className="text-xs text-stone-600">
                  Pratique memorização ativa com ilustrações temáticas e pronúncia clássica em áudio.
                </p>
              </div>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleOpenFlashcards}
              isLoading={isLoadingFlashcards}
              className="border-amber-400 text-amber-950 hover:bg-amber-100 flex-shrink-0 font-medium"
            >
              <Sparkles className="w-4 h-4 mr-1.5 text-amber-600" />
              <span>Abrir Flashcards</span>
            </Button>
          </div>

          {/* Vocabulary Grid */}
          <div>
            <h3 className="font-serif font-bold text-lg text-slate-900 mb-3">
              Vocabulário Essencial (Vocabula)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {activeLesson.vocabulary?.map((item, idx) => (
                <Card
                  key={idx}
                  className="p-4 border-stone-200 hover:border-amber-300 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="font-serif font-bold text-lg text-amber-900">
                          {item.word}
                        </h4>
                        <LatinAudioButton text={item.word} size="sm" />
                        <button
                          type="button"
                          onClick={() =>
                            handleOpenPronunciation(
                              item.word,
                              item.translation,
                              item.example_sentence
                            )
                          }
                          className="p-1.5 rounded-full text-amber-700 hover:bg-amber-100 transition-colors"
                          title="Treinar pronúncia deste vocábulo no Laboratório"
                        >
                          <Mic className="w-4 h-4" />
                        </button>
                      </div>
                      <p className="text-xs text-stone-500 italic font-serif">
                        {item.dictionary_entry}
                      </p>
                    </div>
                    <Badge variant="warning" size="sm">
                      {item.grammatical_class}
                    </Badge>
                  </div>
                  <div className="mt-2.5 pt-2 border-t border-stone-100">
                    <p className="text-sm font-medium text-stone-800">
                      {item.translation}
                    </p>
                    {item.example_sentence && (
                      <div className="flex items-center justify-between mt-1 text-xs text-stone-500 italic">
                        <span>"{item.example_sentence}"</span>
                        <div className="flex items-center space-x-1 flex-shrink-0">
                          <LatinAudioButton text={item.example_sentence} size="sm" />
                          <button
                            type="button"
                            onClick={() =>
                              handleOpenPronunciation(
                                item.example_sentence,
                                item.translation
                              )
                            }
                            className="p-1 rounded-full text-amber-700 hover:bg-amber-100 transition-colors"
                            title="Treinar pronúncia desta frase no Laboratório"
                          >
                            <Mic className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Latin Examples */}
          {activeLesson.examples?.length > 0 && (
            <div className="pt-2">
              <h3 className="font-serif font-bold text-lg text-slate-900 mb-3">
                Exemplos Práticos & Tradução
              </h3>
              <div className="space-y-3">
                {activeLesson.examples.map((ex, idx) => (
                  <Card key={idx} className="p-4 bg-[#faf8f4] border-stone-200">
                    <div className="flex items-start justify-between">
                      <p className="font-serif text-base font-semibold text-slate-900">
                        {ex.latin}
                      </p>
                      <div className="flex items-center space-x-1.5 ml-2 flex-shrink-0">
                        <LatinAudioButton text={ex.latin} size="sm" />
                        <button
                          type="button"
                          onClick={() =>
                            handleOpenPronunciation(
                              ex.latin,
                              ex.translation,
                              ex.grammatical_notes
                            )
                          }
                          className="p-1.5 rounded-full text-amber-700 hover:bg-amber-100 transition-colors"
                          title="Treinar pronúncia no Laboratório"
                        >
                          <Mic className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <p className="text-sm text-stone-600 mt-1 font-medium">
                      ↳ {ex.translation}
                    </p>
                    {ex.grammatical_notes && (
                      <p className="text-xs text-stone-400 mt-1.5 italic">
                        Nota: {ex.grammatical_notes}
                      </p>
                    )}
                  </Card>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-between pt-2">
            <Button variant="secondary" onClick={() => setActiveTab('theory')}>
              <ArrowLeft className="w-4 h-4 mr-1.5" />
              <span>Voltar à Teoria</span>
            </Button>
            <Button variant="primary" onClick={() => setActiveTab('exercises')}>
              <span>Praticar com Exercícios</span>
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </Button>
          </div>
        </div>
      )}

      {/* TAB 3: EXERCÍCIOS INTERATIVOS */}
      {activeTab === 'exercises' && (
        <div>
          {isLessonFinished ? (
            /* Celebration / Lesson Finished Screen */
            <Card className="p-8 text-center max-w-lg mx-auto bg-gradient-to-b from-white to-amber-50/50 border-amber-200 shadow-xl space-y-6 animate-fadeIn">
              <div className="w-20 h-20 rounded-full bg-amber-100 border-2 border-amber-300 flex items-center justify-center mx-auto text-4xl shadow-inner">
                {isReadOnly ? '📜' : '🏆'}
              </div>

              <div className="space-y-2">
                <Badge variant="success" size="md">
                  {isReadOnly ? 'Revisão Histórica Concluída' : 'Lição Finalizada com Êxito!'}
                </Badge>
                <h3 className="font-serif text-2xl font-bold text-slate-900">
                  {isReadOnly ? 'Lectio Recognita!' : 'Optime Fecisti! (Muito Bem!)'}
                </h3>
                <p className="text-stone-600 text-sm">
                  {isReadOnly
                    ? 'Você concluiu a consulta completa de todos os exercícios e gabaritos deste pergaminho.'
                    : 'Você completou todos os exercícios propostos para esta lição.'}
                </p>
              </div>

              {/* Score Display (only for normal mode) */}
              {!isReadOnly && (
                <div className="p-4 rounded-xl bg-white border border-stone-200/80 shadow-sm max-w-xs mx-auto">
                  <p className="text-xs uppercase font-bold tracking-wider text-stone-400">
                    Pontuação Conquistada
                  </p>
                  <div className="flex items-center justify-center gap-1.5 mt-1">
                    <Award className="w-6 h-6 text-amber-600" />
                    <span className="font-bold text-3xl text-slate-900">
                      {calculateFinalScore()}
                    </span>
                    <span className="text-stone-400 text-sm">/ 100</span>
                  </div>
                </div>
              )}

              <div className="pt-2">
                {isReadOnly ? (
                  <Button
                    variant="primary"
                    size="lg"
                    fullWidth
                    onClick={onBackToTabularium || onBackToDashboard}
                    className="shadow-lg"
                  >
                    <Scroll className="w-5 h-5 mr-1.5" />
                    Retornar ao Tabularium
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    size="lg"
                    fullWidth
                    onClick={handleFinishAndSave}
                    isLoading={isLoading}
                    className="shadow-lg"
                  >
                    <Check className="w-5 h-5 mr-1.5" />
                    Salvar Progresso e Concluir
                  </Button>
                )}
              </div>
            </Card>
          ) : currentEx ? (
            /* Active Exercise Stepper */
            <div className="max-w-2xl mx-auto space-y-5">
              {/* Exercise Stepper Header */}
              <div className="flex items-center justify-between text-xs text-stone-500 font-semibold">
                <span>
                  Exercício {currentExIndex + 1} de {exercises.length}
                </span>
                <span>
                  {Object.keys(userAnswers).length} respondidos
                </span>
              </div>

              {/* Step indicator bar */}
              <div className="flex gap-1.5 h-1.5">
                {exercises.map((_, i) => (
                  <div
                    key={i}
                    className={`flex-1 rounded-full transition-all ${
                      i === currentExIndex
                        ? 'bg-amber-600'
                        : userAnswers[i]
                        ? userAnswers[i].isCorrect
                          ? 'bg-emerald-500'
                          : 'bg-red-400'
                        : 'bg-stone-200'
                    }`}
                  />
                ))}
              </div>

              {/* Exercise Question Card */}
              <Card className="p-6 sm:p-8 border-stone-200 space-y-5 shadow-sm">
                <ExerciseHeader
                  instruction={getSafeInstruction(
                    currentEx.instruction,
                    currentEx.correct_answer,
                    isAnswerChecked
                  )}
                  question_prompt={getSafeQuestionPrompt(
                    currentEx.question,
                    currentEx.correct_answer,
                    isAnswerChecked
                  )}
                  isAiEvaluated={!currentEx.options}
                />

                {/* Multiple Choice Options */}
                {currentEx.options && currentEx.options.length > 0 ? (
                  <div className="space-y-2.5">
                    {currentEx.options.map((opt, optIdx) => {
                      const isSelected = selectedOption === opt;
                      const isCorrectAnswer =
                        normalizeAnswer(opt) === normalizeAnswer(currentEx.correct_answer);

                      let optionStyle =
                        'border-stone-200 hover:border-stone-300 bg-white text-stone-800';

                      if (isReadOnly) {
                        if (isCorrectAnswer) {
                          optionStyle =
                            'border-emerald-500 bg-emerald-50 text-emerald-950 font-medium ring-1 ring-emerald-400';
                        } else {
                          optionStyle = 'opacity-60 border-stone-200 bg-stone-50 text-stone-600';
                        }
                      } else {
                        if (isSelected && !isAnswerChecked) {
                          optionStyle =
                            'border-amber-600 bg-amber-50/50 text-amber-900 ring-2 ring-amber-500/20';
                        }

                        if (isAnswerChecked) {
                          if (isCorrectAnswer) {
                            optionStyle =
                              'border-emerald-500 bg-emerald-50 text-emerald-900 font-medium';
                          } else if (isSelected && !isCorrectAnswer) {
                            optionStyle = 'border-red-400 bg-red-50 text-red-900';
                          } else {
                            optionStyle = 'opacity-50 border-stone-200 bg-stone-50';
                          }
                        }
                      }

                      return (
                        <button
                          key={optIdx}
                          disabled={isReadOnly || isAnswerChecked}
                          onClick={() => setSelectedOption(opt)}
                          className={`w-full p-3.5 rounded-xl border text-left text-sm sm:text-base flex items-center justify-between transition-all ${optionStyle}`}
                        >
                          <span className="font-serif">{opt}</span>
                          {((isReadOnly && isCorrectAnswer) ||
                            (isAnswerChecked && isCorrectAnswer)) && (
                            <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
                              {isReadOnly && (
                                <span className="text-[10px] uppercase font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded">
                                  Gabarito
                                </span>
                              )}
                              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                            </div>
                          )}
                          {!isReadOnly && isAnswerChecked && isSelected && !isCorrectAnswer && (
                            <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 ml-2" />
                          )}
                        </button>
                      );
                    })}

                    {isReadOnly && currentEx.explanation && (
                      <div className="p-3.5 rounded-xl bg-stone-50 border border-stone-200 text-xs text-stone-700 leading-relaxed mt-3">
                        <span className="font-bold text-slate-900 font-serif">
                          Explicação Gramatical:{' '}
                        </span>
                        {currentEx.explanation}
                      </div>
                    )}
                  </div>
                ) : isReadOnly ? (
                  /* Read-Only Mode for open-ended / translation questions: Strictly omit input & evaluate button, reveal canonical answer */
                  <div className="p-5 rounded-xl bg-emerald-50/90 border border-emerald-300 space-y-3 shadow-xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                        <span className="font-serif font-bold text-sm text-emerald-950">
                          Gabarito Clássico (Resposta Esperada):
                        </span>
                      </div>
                      <span className="text-[10px] uppercase font-bold text-emerald-800 bg-emerald-200/70 px-2.5 py-0.5 rounded-full">
                        Alvo Oficial
                      </span>
                    </div>
                    <p className="font-serif text-base sm:text-lg font-bold text-emerald-900 pl-7">
                      {currentEx.correct_answer}
                    </p>
                    {currentEx.explanation && (
                      <div className="pl-7 pt-2.5 text-xs sm:text-sm text-emerald-800 leading-relaxed border-t border-emerald-200/70 mt-2">
                        <span className="font-semibold text-emerald-950">
                          Explicação do Magister:{' '}
                        </span>
                        {currentEx.explanation}
                      </div>
                    )}
                  </div>
                ) : (
                  /* Text input for fill in the blank / translation */
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={textAnswer}
                      onChange={(e) => setTextAnswer(e.target.value)}
                      disabled={isAnswerChecked || isEvaluating}
                      placeholder="Digite sua resposta em latim ou português..."
                      autoComplete="off"
                      autoCorrect="off"
                      autoCapitalize="none"
                      spellCheck="false"
                      className="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 text-sm font-sans text-stone-900 bg-white placeholder:text-stone-400 normal-case transition-all"
                    />
                  </div>
                )}

                {/* Loading spinner while Censor Latium is analyzing */}
                {isEvaluating && (
                  <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200 text-amber-900 flex items-center gap-3 animate-pulse">
                    <Feather className="w-5 h-5 text-amber-700 animate-bounce" />
                    <span className="text-xs font-medium">
                      O Censor Latium está analisando a morfologia, caso e concordância da sua oração...
                    </span>
                  </div>
                )}

                {/* Rich AI Evaluation Feedback (Phase 4) */}
                {isAnswerChecked && userAnswers[currentExIndex]?.evaluation && (
                  <div className="space-y-4 pt-2 animate-fadeIn">
                    {/* Overall feedback banner */}
                    <div
                      className={`p-4 rounded-xl border ${
                        userAnswers[currentExIndex].evaluation.is_correct
                          ? 'bg-emerald-50/90 border-emerald-300 text-emerald-950'
                          : 'bg-amber-50 border-amber-300 text-amber-950'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 flex-wrap mb-2">
                        <div className="flex items-center gap-2">
                          {userAnswers[currentExIndex].evaluation.is_correct ? (
                            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                          ) : (
                            <XCircle className="w-5 h-5 text-amber-600" />
                          )}
                          <span className="font-serif font-bold text-sm">
                            Parecer do Censor Latium ({userAnswers[currentExIndex].evaluation.evaluator_model})
                          </span>
                        </div>
                        <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-white/80 border border-stone-200">
                          Nota: {userAnswers[currentExIndex].evaluation.score}/100
                        </span>
                      </div>
                      <p className="text-xs sm:text-sm leading-relaxed opacity-95">
                        {userAnswers[currentExIndex].evaluation.overall_feedback}
                      </p>
                    </div>

                    {/* Morphological Breakdown Pills */}
                    {userAnswers[currentExIndex].evaluation.morphological_breakdown.length > 0 && (
                      <div className="p-4 rounded-xl bg-stone-50 border border-stone-200 space-y-2.5">
                        <p className="text-xs font-bold uppercase tracking-wider text-stone-700 flex items-center gap-1.5">
                          <span>🔍 Decomposição Morfológica (Verbum de Verbo)</span>
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {userAnswers[currentExIndex].evaluation.morphological_breakdown.map((token, tIdx) => (
                            <div
                              key={tIdx}
                              className={`p-2.5 rounded-lg border text-xs ${
                                token.is_correct
                                  ? 'bg-white border-stone-200'
                                  : 'bg-red-50/80 border-red-200'
                              }`}
                            >
                              <div className="flex items-center justify-between gap-1">
                                <span className="font-serif font-bold text-amber-900">
                                  {token.token}
                                </span>
                                <span className="text-[10px] text-stone-400 italic">
                                  {token.lemma}
                                </span>
                              </div>
                              <p className="text-[11px] text-stone-600 mt-0.5">
                                {token.part_of_speech} — {token.grammatical_features}
                              </p>
                              {token.feedback_note && (
                                <p className="text-[10px] text-amber-800 mt-1 italic">
                                  ↳ {token.feedback_note}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Syntax Critique */}
                    {userAnswers[currentExIndex].evaluation.syntax_critique && (
                      <div className="p-3.5 rounded-xl bg-[#faf8f4] border border-stone-200 text-xs sm:text-sm text-stone-700 leading-relaxed">
                        <span className="font-bold text-slate-900">Crítica de Sintaxe: </span>
                        {userAnswers[currentExIndex].evaluation.syntax_critique}
                      </div>
                    )}

                    {/* Suggested Classical Alternatives */}
                    {userAnswers[currentExIndex].evaluation.suggested_classical_alternatives?.length > 0 && (
                      <div className="p-3.5 rounded-xl bg-amber-50/50 border border-amber-200/80 text-xs text-amber-950 space-y-1">
                        <p className="font-bold uppercase tracking-wider text-[10px] text-amber-800">
                          Variações Clássicas Recomendadas:
                        </p>
                        <ul className="list-disc list-inside space-y-0.5 font-serif italic text-xs">
                          {userAnswers[currentExIndex].evaluation.suggested_classical_alternatives.map((alt, aIdx) => (
                            <li key={aIdx}>{alt}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Multiple choice feedback (when no AI evaluation object) */}
                {isAnswerChecked && !userAnswers[currentExIndex]?.evaluation && (
                  <div
                    className={`p-4 rounded-xl text-xs sm:text-sm animate-fadeIn ${
                      userAnswers[currentExIndex]?.isCorrect
                        ? 'bg-emerald-50 border border-emerald-200 text-emerald-900'
                        : 'bg-red-50 border border-red-200 text-red-900'
                    }`}
                  >
                    <div className="flex items-center gap-2 font-bold mb-1">
                      {userAnswers[currentExIndex]?.isCorrect ? (
                        <>
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          <span>Correto! Optime!</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-4 h-4 text-red-600" />
                          <span>Incorreto. A resposta correta é: {currentEx.correct_answer}</span>
                        </>
                      )}
                    </div>
                    {currentEx.explanation && (
                      <p className="mt-1 opacity-90 leading-relaxed">
                        {currentEx.explanation}
                      </p>
                    )}
                  </div>
                )}

                {/* Action buttons */}
                <div className="pt-2 flex items-center justify-between gap-2">
                  {isReadOnly ? (
                    <>
                      {currentExIndex > 0 ? (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setCurrentExIndex((prev) => prev - 1)}
                        >
                          <ArrowLeft className="w-4 h-4 mr-1" />
                          <span>Pergunta Anterior</span>
                        </Button>
                      ) : (
                        <div />
                      )}

                      <div className="flex items-center gap-2">
                        {currentExIndex < exercises.length - 1 ? (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => setCurrentExIndex((prev) => prev + 1)}
                          >
                            <span>Próxima Pergunta</span>
                            <ArrowRight className="w-4 h-4 ml-1.5" />
                          </Button>
                        ) : (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => setIsLessonFinished(true)}
                          >
                            <Check className="w-4 h-4 mr-1.5" />
                            <span>Concluir Revisão</span>
                          </Button>
                        )}
                      </div>
                    </>
                  ) : !isAnswerChecked ? (
                    <div className="w-full flex justify-end">
                      <Button
                        variant="primary"
                        onClick={handleCheckAnswer}
                        disabled={(!selectedOption && !textAnswer.trim()) || isEvaluating}
                        isLoading={isEvaluating}
                      >
                        {!currentEx.options ? 'Avaliar com Censor Latium' : 'Verificar Resposta'}
                      </Button>
                    </div>
                  ) : (
                    <div className="w-full flex justify-end">
                      <Button variant="primary" onClick={handleNextExercise}>
                        {currentExIndex < exercises.length - 1 ? (
                          <>
                            <span>Próxima Pergunta</span>
                            <ArrowRight className="w-4 h-4 ml-1.5" />
                          </>
                        ) : (
                          <>
                            <span>Finalizar Aula</span>
                            <Check className="w-4 h-4 ml-1.5" />
                          </>
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          ) : (
            /* Fallback if no exercises were returned */
            <div className="text-center py-10 space-y-3">
              <p className="text-stone-500 text-sm">
                Esta lição é puramente teórica e não possui exercícios interativos.
              </p>
              <Button
                variant="primary"
                onClick={isReadOnly ? (onBackToTabularium || onBackToDashboard) : handleFinishAndSave}
                isLoading={!isReadOnly && isLoading}
              >
                {isReadOnly ? 'Retornar ao Tabularium' : 'Concluir e Salvar Estudo'}
              </Button>
            </div>
          )}
        </div>
      )}

      {/* 3D Flashcards Modal */}
      {activeLesson && (
        <FlashcardModal
          isOpen={isFlashcardsOpen}
          onClose={() => setIsFlashcardsOpen(false)}
          flashcards={flashcards}
          lessonTitle={activeLesson.lesson_title}
        />
      )}

      {/* Laboratório de Pronúncia Modal */}
      <PronunciationLabModal
        isOpen={isPronunciationOpen}
        onClose={() => setIsPronunciationOpen(false)}
        targetText={pronunciationText}
        translation={pronunciationTranslation}
        phoneticHint={pronunciationHint}
      />

      {/* Magister Latium Side-Drawer Chat */}
      <MagisterChatDrawer
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        lessonId={activeLesson?.lesson_id}
        lessonTitle={activeLesson?.lesson_title}
        contextTopics={activeLesson?.theory_sections?.map((t) => t.topic) || []}
      />

      {/* Floating Action Button for Magister Chat (Disabled in Read-Only) */}
      {!isReadOnly && (
        <FloatingMagisterButton
          isOpen={isChatOpen}
          onClick={() => setIsChatOpen(true)}
        />
      )}
    </div>
  );
};
