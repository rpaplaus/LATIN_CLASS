import React, { useState } from 'react';
import { useProgress } from '../context/ProgressContext';
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
} from 'lucide-react';

interface ClassroomPageProps {
  onBackToDashboard: () => void;
}

export const ClassroomPage: React.FC<ClassroomPageProps> = ({ onBackToDashboard }) => {
  const { activeLesson, completeLesson, isLoading } = useProgress();
  const [activeTab, setActiveTab] = useState<'theory' | 'vocabulary' | 'exercises'>('theory');

  // Exercise runner states
  const [currentExIndex, setCurrentExIndex] = useState<number>(0);
  const [selectedOption, setSelectedOption] = useState<string>('');
  const [textAnswer, setTextAnswer] = useState<string>('');
  const [isAnswerChecked, setIsAnswerChecked] = useState<boolean>(false);
  const [userAnswers, setUserAnswers] = useState<Record<number, { isCorrect: boolean; answer: string }>>({});
  const [isLessonFinished, setIsLessonFinished] = useState<boolean>(false);

  if (!activeLesson) {
    return (
      <div className="text-center py-16 space-y-4">
        <div className="w-16 h-16 rounded-full bg-stone-100 flex items-center justify-center mx-auto text-2xl">
          🏛️
        </div>
        <h3 className="font-serif text-xl font-bold text-slate-800">
          Nenhuma lição ativa no momento
        </h3>
        <p className="text-stone-500 text-sm max-w-sm mx-auto">
          Retorne ao painel para iniciar uma aula personalizada preparada pelo Magister Latium.
        </p>
        <Button variant="primary" onClick={onBackToDashboard}>
          Voltar ao Painel
        </Button>
      </div>
    );
  }

  const exercises = activeLesson.exercises || [];
  const currentEx = exercises[currentExIndex];

  const handleCheckAnswer = () => {
    if (!currentEx) return;

    let isCorrect = false;
    const given = currentEx.options ? selectedOption : textAnswer.trim();

    if (currentEx.options) {
      isCorrect =
        selectedOption.trim().toLowerCase() === currentEx.correct_answer.trim().toLowerCase();
    } else {
      isCorrect =
        textAnswer.trim().toLowerCase() === currentEx.correct_answer.trim().toLowerCase();
    }

    setUserAnswers((prev) => ({
      ...prev,
      [currentExIndex]: { isCorrect, answer: given },
    }));
    setIsAnswerChecked(true);
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
    const correctCount = Object.values(userAnswers).filter((a) => a.isCorrect).length;
    return Math.round((correctCount / exercises.length) * 100);
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
            onClick={onBackToDashboard}
            className="p-2 rounded-xl hover:bg-stone-200/60 text-stone-600 transition-colors"
            title="Voltar ao Painel"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold text-amber-700 uppercase tracking-wider">
                {activeLesson.module_title}
              </span>
            </div>
            <h2 className="font-serif text-xl sm:text-2xl font-bold text-slate-900 leading-tight">
              {activeLesson.lesson_title}
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
                      <h4 className="font-serif font-bold text-lg text-amber-900">
                        {item.word}
                      </h4>
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
                      <p className="text-xs text-stone-500 mt-1 italic">
                        "{item.example_sentence}"
                      </p>
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
                    <p className="font-serif text-base font-semibold text-slate-900">
                      {ex.latin}
                    </p>
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
                🏆
              </div>

              <div className="space-y-2">
                <Badge variant="success" size="md">
                  Lição Finalizada com Êxito!
                </Badge>
                <h3 className="font-serif text-2xl font-bold text-slate-900">
                  Optime Fecisti! (Muito Bem!)
                </h3>
                <p className="text-stone-600 text-sm">
                  Você completou todos os exercícios propostos para esta lição.
                </p>
              </div>

              {/* Score Display */}
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

              <div className="pt-2">
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
                <div>
                  <Badge variant="neutral" size="sm">
                    {currentEx.instruction || 'Responda a pergunta'}
                  </Badge>
                  <h3 className="font-serif text-lg sm:text-xl font-bold text-slate-900 mt-2">
                    {currentEx.question}
                  </h3>
                </div>

                {/* Multiple Choice Options */}
                {currentEx.options && currentEx.options.length > 0 ? (
                  <div className="space-y-2.5">
                    {currentEx.options.map((opt, optIdx) => {
                      const isSelected = selectedOption === opt;
                      const isCorrectAnswer =
                        opt.trim().toLowerCase() === currentEx.correct_answer.trim().toLowerCase();

                      let optionStyle =
                        'border-stone-200 hover:border-stone-300 bg-white text-stone-800';

                      if (isSelected && !isAnswerChecked) {
                        optionStyle = 'border-amber-600 bg-amber-50/50 text-amber-900 ring-2 ring-amber-500/20';
                      }

                      if (isAnswerChecked) {
                        if (isCorrectAnswer) {
                          optionStyle = 'border-emerald-500 bg-emerald-50 text-emerald-900 font-medium';
                        } else if (isSelected && !isCorrectAnswer) {
                          optionStyle = 'border-red-400 bg-red-50 text-red-900';
                        } else {
                          optionStyle = 'opacity-50 border-stone-200 bg-stone-50';
                        }
                      }

                      return (
                        <button
                          key={optIdx}
                          disabled={isAnswerChecked}
                          onClick={() => setSelectedOption(opt)}
                          className={`w-full p-3.5 rounded-xl border text-left text-sm sm:text-base flex items-center justify-between transition-all ${optionStyle}`}
                        >
                          <span className="font-serif">{opt}</span>
                          {isAnswerChecked && isCorrectAnswer && (
                            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 ml-2" />
                          )}
                          {isAnswerChecked && isSelected && !isCorrectAnswer && (
                            <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 ml-2" />
                          )}
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  /* Text input for fill in the blank / translation */
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={textAnswer}
                      onChange={(e) => setTextAnswer(e.target.value)}
                      disabled={isAnswerChecked}
                      placeholder="Digite sua resposta em latim..."
                      className="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 text-sm font-serif"
                    />
                  </div>
                )}

                {/* Explanation feedback after check */}
                {isAnswerChecked && (
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
                <div className="pt-2 flex justify-end">
                  {!isAnswerChecked ? (
                    <Button
                      variant="primary"
                      onClick={handleCheckAnswer}
                      disabled={!selectedOption && !textAnswer.trim()}
                    >
                      Verificar Resposta
                    </Button>
                  ) : (
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
              <Button variant="primary" onClick={handleFinishAndSave} isLoading={isLoading}>
                Concluir e Salvar Estudo
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
