import React, { useState, useEffect } from 'react';
import {
  BrainCircuit,
  AlertTriangle,
  Sparkles,
  Info,
} from 'lucide-react';
import { proficiencyApi } from '../../api/proficiencyApi';
import {
  StudentProficiencyProfileResponse,
  TopicProficiencyItem,
} from '../../types/proficiency';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

interface AdaptiveProficiencyWidgetProps {
  className?: string;
}

export const TOPIC_DISPLAY_NAMES: Record<string, string> = {
  // Módulo I
  '1st_declension_nominative': '1ª Declinação: Caso Nominativo',
  'verb_esse_present': 'Verbo Esse: Presente do Indicativo',
  'questions_with_ne': 'Interrogações Clássicas (-ne)',
  '1st_declension_accusative': '1ª Declinação: Caso Acusativo',
  '1st_declension_genitive': '1ª Declinação: Caso Genitivo',
  'preposition_in_ablative': 'Preposição In + Ablativo',
  'vocabulary_family': 'Vocabulário Familiar Romano',

  // Módulo II
  '2nd_declension_masculine': '2ª Declinação Masculina (-us, -i)',
  'noun_adjective_agreement': 'Concordância Nominal',
  'vocative_case': 'Caso Vocativo',
  'regular_conjugations': 'Conjugações Verbais Regulares',
  'verb_personal_endings': 'Desinências Pessoais Ativas',

  // Additional canonical aliases and uppercase variants
  'adjective_agreement_feminine': 'Concordância Adjetival Feminina',
  'basic_latin_word_order': 'Ordem Canônica das Palavras (SOV)',
  'caso nominativo': '1ª Declinação: Caso Nominativo',
  'caso acusativo': '1ª Declinação: Caso Acusativo',
  'caso genitivo': '1ª Declinação: Caso Genitivo',
  'caso vocativo': 'Caso Vocativo',
  'est / sunt': 'Verbo Esse (est / sunt)',
  'perguntas com -ne': 'Interrogações Clássicas (-ne)',
  'preposição in + ablativo': 'Preposição In + Ablativo',
  'vocabulário familiar': 'Vocabulário Familiar Romano',
  '2ª declinação masculina (-us, -i)': '2ª Declinação Masculina (-us, -i)',
  'concordância nominal': 'Concordância Nominal',
  'conjugações regulares (-are, -ere, -ere, -ire)': 'Conjugações Verbais Regulares',
  'desinências pessoais (-o, -s, -t, -mus, -tis, -nt)': 'Desinências Pessoais Ativas',
};

export const formatTopicName = (key: string): string => {
  if (!key) return '';
  // 1. Direct match
  if (TOPIC_DISPLAY_NAMES[key]) return TOPIC_DISPLAY_NAMES[key];

  // 2. Normalized lowercase match (strip spaces, hyphens, underscores)
  const cleaned = key.toLowerCase().replace(/[\s\-]+/g, '_').trim();
  if (TOPIC_DISPLAY_NAMES[cleaned]) return TOPIC_DISPLAY_NAMES[cleaned];

  // 3. Match against entries in TOPIC_DISPLAY_NAMES case-insensitively
  const directLower = key.toLowerCase().trim();
  for (const [k, v] of Object.entries(TOPIC_DISPLAY_NAMES)) {
    if (k.toLowerCase() === directLower || k.toLowerCase().replace(/[\s\-]+/g, '_') === cleaned) {
      return v;
    }
  }

  // 4. Clean fallback with proper title-casing (never all uppercase)
  return key
    .replace(/[_\-]+/g, ' ')
    .trim()
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
};

export const AdaptiveProficiencyWidget: React.FC<AdaptiveProficiencyWidgetProps> = ({
  className = '',
}) => {
  const [data, setData] = useState<StudentProficiencyProfileResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isDetailedView, setIsDetailedView] = useState<boolean>(false);
  const [selectedTopic, setSelectedTopic] = useState<TopicProficiencyItem | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchProficiency = async () => {
      try {
        const overview = await proficiencyApi.getMyProficiency();
        if (isMounted) {
          setData(overview);
          const topics = overview?.topic_details || [];
          if (topics.length > 0) {
            setSelectedTopic(topics[0]);
          }
        }
      } catch (err) {
        console.error('Erro ao carregar dados de proficiência adaptativa:', err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchProficiency();
    return () => {
      isMounted = false;
    };
  }, []);

  if (isLoading) {
    return (
      <Card className={`p-6 border-amber-200/80 bg-white ${className}`}>
        <div className="flex items-center space-x-3 text-stone-500 animate-pulse">
          <BrainCircuit className="w-5 h-5 text-amber-600 animate-spin" />
          <span className="text-sm font-serif">
            Consultando Motor de Proficiência Adaptativa do Magister...
          </span>
        </div>
      </Card>
    );
  }

  const topics = data?.topic_details || [];
  if (!data || topics.length === 0) {
    return null;
  }

  const hasAnyAttempts = topics.some((t) => (t.attempts_count ?? 0) > 0);
  const effectiveOverallMastery = hasAnyAttempts ? (data.overall_mastery ?? 0.5) : 0;
  const overallPercent = Math.round(effectiveOverallMastery * 100);

  const getRankInfo = (mastery: number, evaluated: boolean) => {
    if (!evaluated) return { rank: 'Tiro', title: 'Recruta Inicial (Não Avaliado)' };
    if (mastery >= 0.9) return { rank: 'Magister Latium', title: 'Mestre da Sintaxe Clássica' };
    if (mastery >= 0.75) return { rank: 'Rhetor', title: 'Orador Avançado' };
    if (mastery >= 0.6) return { rank: 'Grammaticus', title: 'Gramático Intermediário' };
    if (mastery >= 0.4) return { rank: 'Discipulus', title: 'Discípulo em Formação' };
    return { rank: 'Tiro', title: 'Recruta Iniciante' };
  };

  const currentRank = getRankInfo(effectiveOverallMastery, hasAnyAttempts);
  const vulnerableTopics = hasAnyAttempts ? (data.vulnerable_topics || []) : [];

  return (
    <Card
      className={`p-6 border-amber-200/90 bg-gradient-to-br from-white via-[#fcfbf9] to-amber-50/20 shadow-md ${className}`}
    >
      {/* Header with Title & View Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-stone-200/80">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-2xl bg-amber-500/15 border border-amber-400/40 text-amber-800">
            <BrainCircuit className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-serif font-bold uppercase tracking-widest text-amber-800">
                • MOTOR ADAPTATIVO & DIAGNÓSTICO •
              </span>
            </div>
            <h3 className="font-serif text-lg font-bold text-stone-900">
              Proficiência & Adaptação do Aluno
            </h3>
          </div>
        </div>

        {/* Friendly vs Detailed Toggle */}
        <div className="flex items-center p-1 rounded-xl bg-stone-100 border border-stone-200 text-xs self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setIsDetailedView(false)}
            className={`px-3 py-1 rounded-lg font-semibold transition-all ${
              !isDetailedView
                ? 'bg-white text-stone-900 shadow-sm'
                : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            Visão Essencial
          </button>
          <button
            type="button"
            onClick={() => setIsDetailedView(true)}
            className={`px-3 py-1 rounded-lg font-semibold transition-all ${
              isDetailedView
                ? 'bg-amber-600 text-white shadow-sm'
                : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            Métricas Detalhadas
          </button>
        </div>
      </div>

      {/* Main Highlights Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-5">
        {/* Overall Mastery Gauge */}
        <div className="p-4 rounded-2xl bg-white border border-stone-200/90 shadow-sm flex items-center space-x-4">
          <div className="relative w-16 h-16 flex items-center justify-center flex-shrink-0">
            <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-stone-200"
                strokeWidth="3.5"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-amber-500"
                strokeDasharray={`${overallPercent}, 100`}
                strokeWidth="3.5"
                strokeLinecap="round"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <span className="absolute font-serif font-bold text-sm text-stone-900">
              {overallPercent}%
            </span>
          </div>
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wider text-stone-500">
              Grau Clássico Atual
            </p>
            <h4 className="font-serif font-bold text-stone-900 text-base">
              {currentRank.rank}
            </h4>
            <p className="text-xs text-stone-500">{currentRank.title}</p>
          </div>
        </div>

        {/* Suggested Focus from Professor Agent */}
        <div className="p-4 rounded-2xl bg-amber-50/60 border border-amber-200/80 shadow-sm flex flex-col justify-between md:col-span-2">
          <div className="flex items-start gap-2.5">
            <Sparkles className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-[11px] font-serif font-bold uppercase tracking-wider text-amber-900">
                Diretiva de Adaptação do Magister
              </p>
              <p className="text-xs sm:text-sm text-amber-950 font-medium mt-0.5">
                {data.recommended_focus ||
                  'Seu progresso está equilibrado em todos os tópicos gramaticais trabalhados.'}
              </p>
            </div>
          </div>
          {vulnerableTopics.length > 0 && (
            <div className="flex items-center gap-1.5 mt-2 text-[11px] text-amber-900">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
              <span>
                Tópicos vulneráveis detectados:{' '}
                <strong>
                  {vulnerableTopics.map((t) => formatTopicName(t)).join(', ')}
                </strong>
              </span>
            </div>
          )}
        </div>
      </div>

      {/* TOPIC MASTERY BARS (Visual & Intuitive) */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between text-xs font-serif font-bold text-stone-700 uppercase tracking-wider">
          <span>Domínio por Conceito Gramatical</span>
          <span>Nível de Maestria</span>
        </div>

        <div className="space-y-2.5">
          {topics.map((topicItem, idx) => {
            const attempts = topicItem.attempts_count ?? 0;
            const hasAttempts = attempts > 0;
            const score = topicItem.mastery_score ?? 0.5;
            const pct = hasAttempts ? Math.round(score * 100) : 0;
            const isVulnerable =
              hasAttempts &&
              (topicItem.status === 'vulnerable' || vulnerableTopics.includes(topicItem.topic_key));
            const isSelected = selectedTopic?.topic_key === topicItem.topic_key;

            return (
              <div
                key={idx}
                onClick={() => setSelectedTopic(topicItem)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'border-amber-400 bg-amber-50/40 shadow-sm'
                    : 'border-stone-200 bg-white hover:border-amber-300'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="font-serif font-bold text-sm text-stone-900">
                      {formatTopicName(topicItem.topic_key)}
                    </span>
                    {isVulnerable && (
                      <Badge variant="warning" size="sm">
                        Requer Reforço
                      </Badge>
                    )}
                  </div>
                  <span
                    className={`font-mono font-bold text-xs ${
                      hasAttempts ? 'text-stone-800' : 'text-slate-400'
                    }`}
                  >
                    {pct}%
                  </span>
                </div>

                {/* Progress Bar with Color Grading */}
                <div className="w-full bg-stone-100 rounded-full h-2.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      pct >= 80
                        ? 'bg-gradient-to-r from-emerald-500 to-teal-500'
                        : pct >= 50
                        ? 'bg-gradient-to-r from-amber-500 to-yellow-500'
                        : pct > 0
                        ? 'bg-gradient-to-r from-rose-500 to-orange-500'
                        : 'bg-transparent'
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>

                {/* Granular Analytical Data (Shown if Detailed View is Active or Selected) */}
                {(isDetailedView || isSelected) && (
                  <div className="mt-3 pt-2.5 border-t border-stone-100 grid grid-cols-3 gap-2 text-center text-[11px] text-stone-600 animate-fadeIn">
                    <div className="bg-stone-50 p-1.5 rounded-lg">
                      <span className="block text-stone-400 font-medium">Tentativas</span>
                      <strong className="text-stone-800">{attempts}</strong>
                    </div>
                    <div className="bg-stone-50 p-1.5 rounded-lg">
                      <span className="block text-stone-400 font-medium">Acertos</span>
                      <strong className="text-emerald-700">
                        {topicItem.correct_count ?? 0} (
                        {attempts > 0
                          ? Math.round(
                              ((topicItem.correct_count ?? 0) / attempts) * 100
                            )
                          : 0}
                        %)
                      </strong>
                    </div>
                    <div className="bg-stone-50 p-1.5 rounded-lg">
                      <span className="block text-stone-400 font-medium">Classificação</span>
                      {!hasAttempts ? (
                        <strong className="text-slate-400 font-medium">
                          Não Avaliado
                        </strong>
                      ) : (
                        <strong
                          className={
                            topicItem.status === 'vulnerable'
                              ? 'text-rose-600 capitalize'
                              : topicItem.status === 'mastered'
                              ? 'text-emerald-700 capitalize'
                              : 'text-amber-700 capitalize'
                          }
                        >
                          {topicItem.status === 'vulnerable'
                            ? 'Vulnerável'
                            : topicItem.status === 'mastered'
                            ? 'Consolidado'
                            : 'Em Progresso'}
                        </strong>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Explanatory Roman Footer */}
      <div className="mt-4 pt-3 border-t border-stone-200/70 flex items-center justify-between text-[11px] text-stone-500">
        <div className="flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-stone-400" />
          <span>
            O algoritmo utiliza Média Móvel Exponencial (EMA) com amortecimento temporal.
          </span>
        </div>
      </div>
    </Card>
  );
};
