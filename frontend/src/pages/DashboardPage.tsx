import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useProgress } from '../context/ProgressContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { ProgressBar } from '../components/ui/ProgressBar';
import {
  Sparkles,
  CheckCircle2,
  Circle,
  Flame,
  Award,
  ChevronDown,
  ChevronUp,
  Compass,
  ArrowRight,
  GraduationCap,
  Trophy,
  Scroll,
  Bookmark,
  Swords,
} from 'lucide-react';
import { SenateBadgesModal } from '../components/gamification/SenateBadgesModal';
import { AdaptiveProficiencyWidget } from '../components/proficiency/AdaptiveProficiencyWidget';
import { LessonSummary } from '../types/progress';

interface DashboardPageProps {
  onOpenClassroom: () => void;
  onOpenTabularium?: () => void;
  onOpenLexicon?: () => void;
  onOpenArena?: () => void;
  onReviewLessonId?: (lessonId: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onOpenClassroom,
  onOpenTabularium,
  onOpenLexicon,
  onOpenArena,
  onReviewLessonId,
}) => {
  const { user } = useAuth();
  const {
    progress,
    modules,
    startNextLesson,
    isGeneratingLesson,
    isLoading,
    isSenateModalOpen,
    setIsSenateModalOpen,
  } = useProgress();
  const [expandedModuleId, setExpandedModuleId] = useState<string | null>(null);

  const handleStartLesson = async () => {
    try {
      await startNextLesson();
      onOpenClassroom();
    } catch (err) {
      console.error('Erro ao iniciar próxima aula:', err);
    }
  };

  const toggleModule = (id: string) => {
    setExpandedModuleId((prev) => (prev === id ? null : id));
  };

  // Calculate total lessons and completion percentage
  const totalLessons = modules.reduce((acc, m) => acc + (m.lessons?.length || 0), 0);
  const completedCount = progress?.completed_lessons_count || 0;
  const progressPercent = totalLessons > 0 ? (completedCount / totalLessons) * 100 : 0;

  const studentName = user?.full_name || user?.email.split('@')[0] || 'Discipulus';

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Salve / Welcome Greeting Card */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-stone-900 via-stone-800 to-amber-950 text-white p-6 sm:p-8 shadow-xl">
        <div className="relative z-10">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/20 border border-amber-400/30 text-amber-300 text-xs font-semibold uppercase tracking-wider mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Academia Latina</span>
          </div>
          <h2 className="font-serif text-2xl sm:text-3xl font-bold tracking-wide">
            Salve, {studentName}!
          </h2>
          <p className="text-stone-300 text-sm mt-1 max-w-xl">
            Bem-vindo ao Latium AI. O Magister Latium está pronto para conduzir seus estudos gramaticais e práticos hoje.
          </p>

          {/* Quick Metrics Bar inside hero */}
          <div className="grid grid-cols-3 gap-3 mt-6 pt-5 border-t border-white/10">
            <div>
              <p className="text-stone-400 text-[11px] uppercase tracking-wider">Ofensiva</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Flame className="w-4 h-4 text-orange-400 fill-orange-400" />
                <span className="font-bold text-base sm:text-lg">{progress?.current_streak_days || 1} dias</span>
              </div>
            </div>
            <div>
              <p className="text-stone-400 text-[11px] uppercase tracking-wider">Pontuação</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Award className="w-4 h-4 text-amber-400" />
                <span className="font-bold text-base sm:text-lg">{progress?.total_points || 0} pts</span>
              </div>
            </div>
            <div>
              <p className="text-stone-400 text-[11px] uppercase tracking-wider">Concluídas</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="font-bold text-base sm:text-lg">
                  {completedCount}/{totalLessons || 10}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Decorative background Roman Column motif */}
        <div className="absolute right-4 -bottom-6 opacity-10 text-9xl select-none pointer-events-none font-serif">
          🏛️
        </div>
      </div>

      {/* Senate Hall / Badges Quick Card */}
      <div
        onClick={() => setIsSenateModalOpen(true)}
        className="flex items-center justify-between p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-stone-900 via-amber-950/40 to-stone-900 border border-amber-500/40 shadow-lg cursor-pointer hover:border-amber-400 hover:scale-[1.01] transition-all group"
      >
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-300 group-hover:scale-110 transition-transform">
            <Trophy size={24} />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-serif font-bold uppercase tracking-widest text-amber-400">
                • SENATUS LATIUM •
              </span>
            </div>
            <h4 className="text-base font-serif font-bold text-stone-100">
              Galeria de Comendas do Senado Romano
            </h4>
            <p className="text-xs text-stone-400">
              Consulte suas insígnias, títulos imperiais e progresso de honrarias
            </p>
          </div>
        </div>
        <div className="hidden sm:flex items-center text-xs font-serif font-bold text-amber-400 group-hover:translate-x-1 transition-transform">
          <span>Abrir Galeria</span>
          <ArrowRight className="w-4 h-4 ml-1" />
        </div>
      </div>

      {/* Tabularium / Historical Archive Quick Card */}
      <div
        onClick={onOpenTabularium}
        className="flex items-center justify-between p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-stone-900 via-stone-850 to-amber-950/40 border border-amber-700/40 shadow-md cursor-pointer hover:border-amber-500 hover:scale-[1.005] transition-all group"
      >
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 group-hover:scale-110 transition-transform">
            <Scroll size={24} />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-serif font-bold uppercase tracking-widest text-amber-400">
                • TABULARIUM LATIUM •
              </span>
              <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Custo Zero de IA
              </span>
            </div>
            <h4 className="text-base font-serif font-bold text-stone-100">
              Arquivo Imperial de Lições
            </h4>
            <p className="text-xs text-stone-400">
              Consulte pergaminhos concluídos, vocabulário e gabaritos oficiais sem consumo de tokens
            </p>
          </div>
        </div>
        <div className="hidden sm:flex items-center text-xs font-serif font-bold text-amber-400 group-hover:translate-x-1 transition-transform">
          <span>Acessar Arquivo</span>
          <ArrowRight className="w-4 h-4 ml-1" />
        </div>
      </div>

      {/* Lexicon Universale / Pugillares Quick Card */}
      <div
        onClick={onOpenLexicon}
        className="flex items-center justify-between p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-stone-900 via-stone-850 to-amber-950/40 border border-amber-700/40 shadow-md cursor-pointer hover:border-amber-500 hover:scale-[1.005] transition-all group"
      >
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 group-hover:scale-110 transition-transform">
            <Bookmark size={24} />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-serif font-bold uppercase tracking-widest text-amber-400">
                • LEXICON UNIVERSALE •
              </span>
              <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                ⭐ Pugillares
              </span>
            </div>
            <h4 className="text-base font-serif font-bold text-stone-100">
              Dicionário Global & Tabuinhas de Estudo
            </h4>
            <p className="text-xs text-stone-400">
              Consulte termos assimilados, ouça pronúncias clássicas e revise suas palavras favoritas
            </p>
          </div>
        </div>
        <div className="hidden sm:flex items-center text-xs font-serif font-bold text-amber-400 group-hover:translate-x-1 transition-transform">
          <span>Abrir Lexicon</span>
          <ArrowRight className="w-4 h-4 ml-1" />
        </div>
      </div>

      {/* Arena Latium / Adaptive Flashcards Quick Card */}
      <div
        onClick={onOpenArena}
        className="flex items-center justify-between p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-stone-950 via-red-950/40 to-amber-950/30 border border-red-800/40 shadow-md cursor-pointer hover:border-red-500 hover:scale-[1.005] transition-all group"
      >
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-red-900/30 border border-red-700/50 text-red-300 group-hover:scale-110 transition-transform shadow-inner">
            <Swords size={24} />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-serif font-bold uppercase tracking-widest text-red-400">
                • ARENA LATIUM •
              </span>
              <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 border border-red-500/30">
                ⚔️ Combate Adaptativo
              </span>
            </div>
            <h4 className="text-base font-serif font-bold text-stone-100">
              Desafio Rápido de Fraquezas (EMA)
            </h4>
            <p className="text-xs text-stone-400">
              Enfrente 3 flashcards focados no seu tópico mais vulnerável com avaliação instantânea
            </p>
          </div>
        </div>
        <div className="hidden sm:flex items-center text-xs font-serif font-bold text-red-400 group-hover:translate-x-1 transition-transform">
          <span>Entrar na Arena</span>
          <ArrowRight className="w-4 h-4 ml-1" />
        </div>
      </div>

      {/* Main Next Lesson CTA Card */}
      <Card className="p-6 border-amber-200/80 bg-gradient-to-br from-white via-amber-50/20 to-orange-50/30 shadow-md hover:shadow-lg transition-all">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <Badge variant="warning">Próxima Lição</Badge>
              <span className="text-xs text-stone-500 font-medium">
                {progress?.current_module_title || 'Módulo I: Pronúncia e Saudações'}
              </span>
            </div>
            <h3 className="font-serif text-xl font-bold text-slate-900">
              {progress?.current_lesson_title || 'Lição I: O Alfabeto Latino e Sons'}
            </h3>
            <p className="text-xs sm:text-sm text-stone-600">
              O Magister Latium preparou teoria interativa, termos de vocabulário e exercícios dinâmicos.
            </p>
          </div>

          <div className="sm:flex-shrink-0">
            <Button
              variant="primary"
              size="lg"
              onClick={handleStartLesson}
              isLoading={isGeneratingLesson}
              className="w-full sm:w-auto shadow-md"
            >
              <GraduationCap className="w-5 h-5 mr-1.5" />
              <span>{isGeneratingLesson ? 'Gerando Aula com IA...' : 'Iniciar Aula'}</span>
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </Button>
          </div>
        </div>

        {/* Global Progress Line */}
        <div className="mt-5 pt-4 border-t border-stone-200/70">
          <ProgressBar
            value={progressPercent}
            label="Progresso Geral no Curso de Latim"
            showPercentage
          />
        </div>
      </Card>

      {/* Adaptive Proficiency & Student Adaptation Diagnostic */}
      <AdaptiveProficiencyWidget />

      {/* Syllabus / Modules Overview */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-amber-700" />
            <h3 className="font-serif text-lg font-bold text-slate-900">
              Trilha de Aprendizado (Syllabus)
            </h3>
          </div>
          <span className="text-xs text-stone-500 font-medium">
            {modules.length} Módulos Canônicos
          </span>
        </div>

        {isLoading && modules.length === 0 ? (
          <div className="text-center py-10 text-stone-400">
            <div className="w-8 h-8 border-3 border-amber-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-sm font-serif">Carregando trilha de estudos...</p>
          </div>
        ) : (
          <div className="space-y-3">
            {modules.map((module) => {
              const isExpanded = expandedModuleId === module.id;
              const moduleLessons = module.lessons || [];
              const moduleCompletedCount = moduleLessons.filter(
                (l: LessonSummary) => l.is_completed
              ).length;
              const isAllCompleted =
                moduleLessons.length > 0 && moduleCompletedCount === moduleLessons.length;

              return (
                <Card
                  key={module.id}
                  className="overflow-hidden border-stone-200 transition-all hover:border-amber-300/80"
                >
                  <button
                    onClick={() => toggleModule(module.id)}
                    className="w-full p-4 sm:p-5 flex items-center justify-between text-left gap-3 bg-white hover:bg-stone-50/80 transition-colors"
                  >
                    <div className="flex items-start sm:items-center gap-3">
                      <div
                        className={`w-9 h-9 rounded-xl flex items-center justify-center font-serif font-bold text-sm flex-shrink-0 ${
                          isAllCompleted
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-stone-100 text-stone-700'
                        }`}
                      >
                        {module.order_index}
                      </div>

                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="font-serif font-bold text-base text-slate-900">
                            {module.title}
                          </h4>
                          <Badge variant={isAllCompleted ? 'success' : 'default'} size="sm">
                            {module.level}
                          </Badge>
                        </div>
                        <p className="text-xs text-stone-500 line-clamp-1 mt-0.5">
                          {module.description}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className="text-xs font-semibold text-stone-500 hidden sm:inline">
                        {moduleCompletedCount}/{moduleLessons.length}
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-stone-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-stone-400" />
                      )}
                    </div>
                  </button>

                  {/* Expanded Lessons List */}
                  {isExpanded && (
                    <div className="bg-stone-50/70 border-t border-stone-200/80 divide-y divide-stone-200/50 p-3 sm:p-4">
                      {moduleLessons.length === 0 ? (
                        <p className="text-xs text-stone-400 italic py-2">
                          Nenhuma lição cadastrada neste módulo ainda.
                        </p>
                      ) : (
                        moduleLessons.map((lesson: LessonSummary) => (
                          <div
                            key={lesson.id}
                            className="py-3 px-2 flex items-center justify-between gap-3 hover:bg-stone-100/60 rounded-lg transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              {lesson.is_completed ? (
                                <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                              ) : (
                                <Circle className="w-5 h-5 text-stone-300 flex-shrink-0" />
                              )}
                              <div>
                                <p
                                  className={`text-sm font-medium ${
                                    lesson.is_completed
                                      ? 'text-stone-700'
                                      : 'text-slate-900 font-semibold'
                                  }`}
                                >
                                  {lesson.title}
                                </p>
                                <p className="text-xs text-stone-500 line-clamp-1">
                                  {lesson.pedagogical_objective}
                                </p>
                              </div>
                            </div>

                            <div className="flex items-center gap-2">
                              {lesson.is_completed ? (
                                <>
                                  <Badge variant="success" size="sm">
                                    Concluída
                                  </Badge>
                                  {onReviewLessonId && (
                                    <button
                                      onClick={() => onReviewLessonId(lesson.id)}
                                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-800 hover:text-amber-950 bg-amber-100/70 hover:bg-amber-200/80 border border-amber-300/80 px-2 py-0.5 rounded-md transition-all shadow-2xs"
                                      title="Revisar no Tabularium (Custo Zero de IA)"
                                    >
                                      <Scroll className="w-3 h-3 text-amber-700" />
                                      <span>Revisar</span>
                                    </button>
                                  )}
                                </>
                              ) : (
                                <Badge variant="neutral" size="sm">
                                  Pendente
                                </Badge>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Senate Badges Modal */}
      <SenateBadgesModal
        isOpen={isSenateModalOpen}
        onClose={() => setIsSenateModalOpen(false)}
      />
    </div>
  );
};
