import React, { useEffect, useState, useMemo } from 'react';
import { lessonApi } from '../api/lessonApi';
import { CompletedLessonSummary } from '../types/progress';
import { LessonContent } from '../types/lesson';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import {
  Scroll,
  BookOpen,
  Award,
  ShieldCheck,
  Search,
  CheckCircle2,
  Calendar,
  ArrowRight,
  Database,
  Volume2,
} from 'lucide-react';

interface TabulariumPageProps {
  onReviewLesson: (lesson: LessonContent) => void;
  onBackToDashboard: () => void;
}

export const TabulariumPage: React.FC<TabulariumPageProps> = ({
  onReviewLesson,
  onBackToDashboard,
}) => {
  const [history, setHistory] = useState<CompletedLessonSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [loadingLessonId, setLoadingLessonId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await lessonApi.getHistory();
        setHistory(data);
      } catch (err: any) {
        console.error('Erro ao carregar histórico do Tabularium:', err);
        setError('Não foi possível acessar os arquivos do Tabularium. Tente novamente.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const handleReview = async (lessonId: string) => {
    setLoadingLessonId(lessonId);
    try {
      const lessonContent = await lessonApi.getLessonById(lessonId);
      onReviewLesson(lessonContent);
    } catch (err: any) {
      console.error('Erro ao buscar conteúdo da lição no Tabularium:', err);
      alert('Erro ao carregar a aula histórica. Verifique sua conexão.');
    } finally {
      setLoadingLessonId(null);
    }
  };

  const filteredHistory = useMemo(() => {
    if (!searchQuery.trim()) return history;
    const query = searchQuery.toLowerCase();
    return history.filter(
      (item) =>
        item.title.toLowerCase().includes(query) ||
        item.module_title.toLowerCase().includes(query) ||
        item.pedagogical_objective.toLowerCase().includes(query) ||
        item.grammar_topics.some((topic) => topic.toLowerCase().includes(query))
    );
  }, [history, searchQuery]);

  // Metric computations
  const averageScore = useMemo(() => {
    if (history.length === 0) return 0;
    const sum = history.reduce((acc, curr) => acc + curr.score, 0);
    return Math.round(sum / history.length);
  }, [history]);

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return new Intl.DateTimeFormat('pt-BR', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      }).format(date);
    } catch {
      return isoString;
    }
  };

  const formatTopic = (topicKey: string) => {
    return topicKey
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Imperial Hero Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-stone-950 via-stone-900 to-amber-950 text-white p-6 sm:p-8 shadow-xl border border-stone-800">
        <div className="relative z-10">
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/20 border border-amber-400/30 text-amber-300 text-xs font-semibold uppercase tracking-wider">
              <Scroll className="w-3.5 h-3.5" />
              <span>Tabularium Publicum</span>
            </span>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-[11px] font-medium">
              <Database className="w-3 h-3" />
              <span>Custo Zero de IA (PostgreSQL Puro)</span>
            </span>
          </div>

          <h2 className="font-serif text-2xl sm:text-3xl font-bold tracking-wide">
            Tabularium Latium
          </h2>
          <p className="text-stone-300 text-sm mt-1 max-w-2xl leading-relaxed">
            Arquivo Imperial do Senado Romano. Consulte o registro indelével de todas as suas lições
            concluídas com teoria, vocabulário e gabarito oficial sem qualquer consumo de tokens.
          </p>

          {/* Quick Metrics Bar inside hero */}
          <div className="grid grid-cols-3 gap-3 mt-6 pt-5 border-t border-white/10">
            <div>
              <p className="text-stone-400 text-[11px] uppercase tracking-wider">Pergaminhos</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Scroll className="w-4 h-4 text-amber-400" />
                <span className="font-bold text-base sm:text-lg">
                  {history.length} {history.length === 1 ? 'aula' : 'aulas'}
                </span>
              </div>
            </div>
            <div>
              <p className="text-stone-400 text-[11px] uppercase tracking-wider">Média Imperial</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Award className="w-4 h-4 text-amber-400" />
                <span className="font-bold text-base sm:text-lg">
                  {averageScore}/100
                </span>
              </div>
            </div>
            <div>
              <p className="text-stone-400 text-[11px] uppercase tracking-wider">Preservação</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span className="font-bold text-base sm:text-lg">100% Permanente</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" />
          <input
            type="text"
            placeholder="Pesquisar por capítulo, módulo ou tópico..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs sm:text-sm bg-white border border-stone-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 transition-all text-stone-800 placeholder:text-stone-400"
          />
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto text-xs text-stone-500">
          <Volume2 className="w-4 h-4 text-amber-600" />
          <span>Áudios clássicos preservados no disco permanente</span>
        </div>
      </div>

      {/* Content Area */}
      {isLoading ? (
        <div className="py-16 text-center space-y-3">
          <div className="w-10 h-10 rounded-xl bg-amber-100 border border-amber-300 flex items-center justify-center mx-auto text-xl animate-pulse">
            🏛️
          </div>
          <p className="font-serif text-stone-600 text-sm">
            Recuperando pergaminhos dos arquivos do Tabularium...
          </p>
        </div>
      ) : error ? (
        <Card className="p-8 text-center space-y-3 border-red-200 bg-red-50/50">
          <p className="text-sm font-semibold text-red-800">{error}</p>
          <Button variant="secondary" size="sm" onClick={() => window.location.reload()}>
            Tentar Novamente
          </Button>
        </Card>
      ) : history.length === 0 ? (
        /* Empty State */
        <Card className="p-10 text-center space-y-4 border-stone-200">
          <div className="w-14 h-14 rounded-full bg-amber-50 border border-amber-200 flex items-center justify-center mx-auto text-2xl">
            📜
          </div>
          <div className="space-y-1 max-w-md mx-auto">
            <h3 className="font-serif text-lg font-bold text-slate-800">
              O Tabularium está vazio
            </h3>
            <p className="text-stone-500 text-xs sm:text-sm leading-relaxed">
              Você ainda não concluiu nenhuma lição. Assim que finalizar sua primeira aula na Trilha
              de Estudos, o pergaminho completo será arquivado aqui para revisão eterna com gabarito oficial.
            </p>
          </div>
          <div className="pt-2">
            <Button variant="primary" onClick={onBackToDashboard}>
              <BookOpen className="w-4 h-4 mr-2" />
              <span>Ir para a Trilha de Aprendizado</span>
            </Button>
          </div>
        </Card>
      ) : filteredHistory.length === 0 ? (
        <div className="py-12 text-center text-stone-500 text-sm">
          Nenhuma lição encontrada para "{searchQuery}".
        </div>
      ) : (
        /* History Lesson Cards Grid */
        <div className="space-y-4">
          {filteredHistory.map((item) => (
            <Card
              key={item.completion_id}
              className="p-5 sm:p-6 border-stone-200/90 hover:border-amber-300/80 hover:shadow-md transition-all duration-200 space-y-4 bg-white"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-stone-100 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-amber-100/70 border border-amber-300/60 flex items-center justify-center text-amber-800 font-serif font-bold text-xs">
                    {item.order_index}
                  </div>
                  <div>
                    <span className="text-[10px] font-semibold text-amber-700 uppercase tracking-wider block">
                      {item.module_title}
                    </span>
                    <h3 className="font-serif text-base sm:text-lg font-bold text-slate-900 leading-tight">
                      {item.title}
                    </h3>
                  </div>
                </div>

                {/* Score and Date Badges */}
                <div className="flex items-center gap-2 self-start sm:self-auto">
                  <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Nota: {item.score}/100</span>
                  </div>
                  <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-stone-100 border border-stone-200 text-stone-600 text-[11px]">
                    <Calendar className="w-3 h-3 text-stone-400" />
                    <span>{formatDate(item.completed_at)}</span>
                  </div>
                </div>
              </div>

              {/* Pedagogical Objective */}
              <p className="text-xs sm:text-sm text-stone-600 leading-relaxed">
                {item.pedagogical_objective}
              </p>

              {/* Topics and Action */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                {/* Grammar Topics Pills */}
                <div className="flex flex-wrap items-center gap-1.5">
                  {item.grammar_topics.map((topic, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded-md bg-stone-100 border border-stone-200/80 text-[11px] text-stone-700 font-serif"
                    >
                      {formatTopic(topic)}
                    </span>
                  ))}
                </div>

                {/* Review Button */}
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleReview(item.id)}
                  isLoading={loadingLessonId === item.id}
                  className="sm:self-end flex-shrink-0"
                >
                  <BookOpen className="w-3.5 h-3.5 mr-1.5" />
                  <span>Revisar Aula</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
