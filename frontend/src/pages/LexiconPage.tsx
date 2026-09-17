import React, { useEffect, useState, useMemo } from 'react';
import {
  Search,
  Star,
  BookOpen,
  Filter,
  ArrowUpDown,
  Volume2,
  Bookmark,
  RefreshCw,
  Scroll,
} from 'lucide-react';
import { lexiconApi } from '../api/lexiconApi';
import { LexiconEntry, LexiconResponse } from '../types/lexicon';
import { LatinAudioButton } from '../components/common/LatinAudioButton';
import { useToast } from '../context/ToastContext';

type TabMode = 'all' | 'favorites';
type SortMode = 'alpha-asc' | 'alpha-desc' | 'chronological-desc' | 'chronological-asc';

interface LexiconPageProps {
  onBackToDashboard?: () => void;
  onNavigateToTabularium?: () => void;
}

export const LexiconPage: React.FC<LexiconPageProps> = ({
  onBackToDashboard,
  onNavigateToTabularium,
}) => {
  const [lexiconData, setLexiconData] = useState<LexiconResponse | null>(null);
  const [entries, setEntries] = useState<LexiconEntry[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<TabMode>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedClass, setSelectedClass] = useState<string>('all');
  const [sortMode, setSortMode] = useState<SortMode>('alpha-asc');

  const { showToast } = useToast();

  const fetchLexicon = async (quiet = false) => {
    if (!quiet) setIsLoading(true);
    else setIsRefreshing(true);

    try {
      const data = await lexiconApi.getLexicon();
      setLexiconData(data);
      setEntries(data.entries);
    } catch (err) {
      console.error('[LexiconPage] Erro ao carregar vocabulário:', err);
      showToast('Falha ao sincronizar o Lexicon Imperial. Tente novamente.', 'error');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchLexicon();
  }, []);

  const handleToggleFavorite = async (entry: LexiconEntry, e: React.MouseEvent) => {
    e.stopPropagation();
    const prevFavoriteState = entry.is_favorite;
    const newFavoriteState = !prevFavoriteState;

    // Optimistic UI mutation
    setEntries((prev) =>
      prev.map((item) =>
        item.word.toLowerCase() === entry.word.toLowerCase()
          ? { ...item, is_favorite: newFavoriteState }
          : item
      )
    );

    try {
      const res = await lexiconApi.toggleFavorite(entry.word);
      showToast(
        res.is_favorite
          ? `⭐ "${entry.word}" gravada nos Pugillares!`
          : `Termo "${entry.word}" removido dos Pugillares.`,
        'success'
      );
    } catch (err) {
      console.error('[LexiconPage] Erro ao favoritar termo:', err);
      // Rollback on failure
      setEntries((prev) =>
        prev.map((item) =>
          item.word.toLowerCase() === entry.word.toLowerCase()
            ? { ...item, is_favorite: prevFavoriteState }
            : item
        )
      );
      showToast('Não foi possível atualizar a tabuinha de cera.', 'error');
    }
  };

  // Filtered & Sorted vocabulary list
  const filteredEntries = useMemo(() => {
    let result = [...entries];

    // Tab filter (All vs Pugillares)
    if (activeTab === 'favorites') {
      result = result.filter((e) => e.is_favorite);
    }

    // Grammatical class filter
    if (selectedClass !== 'all') {
      result = result.filter(
        (e) => e.grammatical_class.toLowerCase() === selectedClass.toLowerCase()
      );
    }

    // Search query filter (Latin word, translation, dictionary entry)
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      result = result.filter(
        (e) =>
          e.word.toLowerCase().includes(q) ||
          e.translation.toLowerCase().includes(q) ||
          e.dictionary_entry.toLowerCase().includes(q) ||
          e.example_sentence.toLowerCase().includes(q)
      );
    }

    // Sorting
    result.sort((a, b) => {
      if (sortMode === 'alpha-asc') {
        return a.word.localeCompare(b.word);
      }
      if (sortMode === 'alpha-desc') {
        return b.word.localeCompare(a.word);
      }
      return 0; // Default chronological order from API
    });

    return result;
  }, [entries, activeTab, selectedClass, searchQuery, sortMode]);

  const favoriteCount = useMemo(() => {
    return entries.filter((e) => e.is_favorite).length;
  }, [entries]);

  const getClassBadgeColor = (gramClass: string) => {
    const lower = gramClass.toLowerCase();
    if (lower.includes('substantivo')) {
      return 'bg-emerald-50 text-emerald-800 border-emerald-200/80';
    }
    if (lower.includes('verbo')) {
      return 'bg-indigo-50 text-indigo-800 border-indigo-200/80';
    }
    if (lower.includes('adjetivo')) {
      return 'bg-amber-50 text-amber-800 border-amber-200/80';
    }
    if (lower.includes('preposição') || lower.includes('adverbio') || lower.includes('advérbio')) {
      return 'bg-purple-50 text-purple-800 border-purple-200/80';
    }
    return 'bg-stone-100 text-stone-700 border-stone-200';
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-6 animate-fade-in pb-24">
      {/* 1. Hero Imperial Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#1c1815] via-[#241e1a] to-[#120f0d] text-[#fdfbf7] p-6 sm:p-8 shadow-xl border border-amber-900/30">
        <div className="absolute -right-10 -bottom-10 w-72 h-72 rounded-full bg-amber-500/5 blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium tracking-wider uppercase bg-amber-500/15 text-amber-300 border border-amber-500/30">
                <Bookmark className="w-3.5 h-3.5" />
                Lexicon Universale • Pugillares
              </span>
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono tracking-wider bg-emerald-950/70 text-emerald-300 border border-emerald-800/50">
                ⚡ Custo Zero de IA (PostgreSQL Puro)
              </span>
            </div>

            <button
              onClick={() => fetchLexicon(true)}
              disabled={isRefreshing}
              className="flex items-center gap-1.5 text-xs text-stone-400 hover:text-stone-200 transition-colors px-2 py-1 rounded-lg bg-stone-800/40 border border-stone-700/40"
              title="Atualizar vocabulário"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Sincronizar</span>
            </button>
          </div>

          <div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-serif font-bold tracking-wide text-stone-100 flex items-center gap-3">
              <span className="text-amber-500">LEXICON</span> UNIVERSALE
            </h1>
            <p className="text-xs sm:text-sm text-stone-300/90 font-serif leading-relaxed max-w-2xl mt-1.5">
              Dicionário vivo e consolidado de todo o vocabulário assimilado em suas lições concluídas.
              Ouça a pronúncia clássica e guarde termos para revisão em suas tabuinhas de cera (<em>Pugillares</em>).
            </p>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2 border-t border-stone-800/80">
            <div className="bg-stone-900/50 backdrop-blur-xs rounded-xl p-3 border border-stone-800/60">
              <span className="text-[11px] uppercase tracking-wider text-stone-400 font-sans block">
                Vocábulos no Acervo
              </span>
              <span className="text-xl sm:text-2xl font-bold font-serif text-amber-200 mt-0.5 block">
                {entries.length} {entries.length === 1 ? 'palavra' : 'palavras'}
              </span>
            </div>

            <div className="bg-stone-900/50 backdrop-blur-xs rounded-xl p-3 border border-stone-800/60">
              <span className="text-[11px] uppercase tracking-wider text-stone-400 font-sans block">
                Pugillares (Favoritos)
              </span>
              <span className="text-xl sm:text-2xl font-bold font-serif text-amber-400 mt-0.5 block flex items-center gap-1.5">
                <Star className="w-4 h-4 fill-amber-400 text-amber-400 inline" />
                {favoriteCount} {favoriteCount === 1 ? 'termo' : 'termos'}
              </span>
            </div>

            <div className="col-span-2 sm:col-span-1 bg-stone-900/50 backdrop-blur-xs rounded-xl p-3 border border-stone-800/60">
              <span className="text-[11px] uppercase tracking-wider text-stone-400 font-sans block">
                Preservação de Áudio
              </span>
              <span className="text-xl sm:text-2xl font-bold font-serif text-emerald-400 mt-0.5 block flex items-center gap-1.5">
                <Volume2 className="w-4 h-4 text-emerald-400 inline" />
                100% Permanente
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Controls & Search Toolbar */}
      <div className="bg-[#fdfbf7] p-4 rounded-2xl border border-stone-200/80 shadow-xs space-y-4">
        {/* Top Row: Search Input & Tab Switcher */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar termo latino, tradução ou lema..."
              className="w-full pl-10 pr-4 py-2 text-sm bg-white border border-stone-200 rounded-xl text-stone-800 placeholder-stone-400 focus:outline-hidden focus:ring-2 focus:ring-amber-500/30 focus:border-amber-500 transition-all font-sans"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-stone-400 hover:text-stone-600"
              >
                Limpar
              </button>
            )}
          </div>

          {/* Tab Switcher: All vs Pugillares */}
          <div className="flex items-center gap-1 bg-stone-100 p-1 rounded-xl border border-stone-200 self-start sm:self-auto text-xs font-semibold">
            <button
              onClick={() => setActiveTab('all')}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                activeTab === 'all'
                  ? 'bg-white text-stone-900 shadow-xs font-bold'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Omnia Verba ({entries.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('favorites')}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                activeTab === 'favorites'
                  ? 'bg-white text-amber-900 shadow-xs font-bold border border-amber-200/80'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-500" />
              <span>Pugillares ({favoriteCount})</span>
            </button>
          </div>
        </div>

        {/* Bottom Row: Grammatical Class Chips & Sort Dropdown */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-stone-100">
          {/* Grammatical Class Pills */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <span className="text-stone-400 text-[11px] uppercase tracking-wider font-semibold mr-1 flex items-center gap-1">
              <Filter className="w-3 h-3" /> Classe:
            </span>

            <button
              onClick={() => setSelectedClass('all')}
              className={`px-2.5 py-1 rounded-lg transition-all text-xs ${
                selectedClass === 'all'
                  ? 'bg-stone-800 text-white font-medium'
                  : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
              }`}
            >
              Todas
            </button>

            {lexiconData?.available_classes.map((cls) => (
              <button
                key={cls}
                onClick={() => setSelectedClass(cls)}
                className={`px-2.5 py-1 rounded-lg transition-all text-xs ${
                  selectedClass === cls
                    ? 'bg-amber-700 text-white font-medium'
                    : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                }`}
              >
                {cls}
              </button>
            ))}
          </div>

          {/* Sort Selector */}
          <div className="flex items-center gap-1.5 text-xs text-stone-600 ml-auto">
            <ArrowUpDown className="w-3.5 h-3.5 text-stone-400" />
            <select
              value={sortMode}
              onChange={(e) => setSortMode(e.target.value as SortMode)}
              className="bg-white border border-stone-200 rounded-lg px-2.5 py-1 text-xs text-stone-700 focus:outline-hidden focus:ring-1 focus:ring-amber-500"
            >
              <option value="alpha-asc">Ordem Alfabética (A - Z)</option>
              <option value="alpha-desc">Ordem Alfabética (Z - A)</option>
              <option value="chronological-desc">Ordem Pedagógica</option>
            </select>
          </div>
        </div>
      </div>

      {/* 3. Vocabulary Cards Grid */}
      {isLoading ? (
        <div className="py-16 text-center space-y-3">
          <div className="w-12 h-12 rounded-xl bg-amber-100 border border-amber-300 mx-auto flex items-center justify-center text-2xl shadow-sm animate-pulse">
            📜
          </div>
          <p className="text-sm font-serif text-stone-600">
            Consultando os pergaminhos lexicográficos do Senado...
          </p>
        </div>
      ) : filteredEntries.length === 0 ? (
        /* Empty State */
        <div className="p-12 text-center bg-[#fdfbf7] rounded-2xl border border-dashed border-stone-300 space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 mx-auto flex items-center justify-center text-3xl">
            {activeTab === 'favorites' ? '⭐' : '🏛️'}
          </div>

          <div className="max-w-md mx-auto space-y-1.5">
            <h3 className="font-serif font-bold text-lg text-stone-800">
              {activeTab === 'favorites'
                ? 'Nenhum termo gravado nos Pugillares'
                : searchQuery
                ? 'Nenhum vocábulo encontrado'
                : 'Seu Lexicon está vazio'}
            </h3>
            <p className="text-xs text-stone-500 font-sans leading-relaxed">
              {activeTab === 'favorites'
                ? 'Você ainda não marcou palavras como favoritas. Clique no ícone de estrela em qualquer card para guardar termos importantes em sua tabuinha de cera.'
                : searchQuery
                ? `Nenhum termo corresponde à pesquisa "${searchQuery}". Tente buscar por outra palavra ou limpe o filtro.`
                : 'Conclua suas primeiras lições na Trilha de Estudos para inaugurar seu acervo com vocabulário canônico.'}
            </p>
          </div>

          {activeTab === 'favorites' ? (
            <button
              onClick={() => setActiveTab('all')}
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white shadow-xs transition-all"
            >
              <BookOpen className="w-3.5 h-3.5" />
              Ver Todas as Palavras
            </button>
          ) : (
            <div className="flex flex-wrap items-center justify-center gap-2">
              {onBackToDashboard && (
                <button
                  onClick={onBackToDashboard}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-xl bg-stone-900 hover:bg-stone-800 text-white shadow-xs transition-all"
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  Ir para a Lição Ativa
                </button>
              )}
              {onNavigateToTabularium && (
                <button
                  onClick={onNavigateToTabularium}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-xl bg-amber-100 hover:bg-amber-200 text-amber-900 border border-amber-300 shadow-xs transition-all"
                >
                  <Scroll className="w-3.5 h-3.5 text-amber-700" />
                  Ver Lições no Tabularium
                </button>
              )}
            </div>
          )}
        </div>
      ) : (
        /* Cards Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredEntries.map((entry) => (
            <div
              key={`${entry.lesson_id}-${entry.word}`}
              className={`relative bg-[#fdfbf7] rounded-2xl p-5 border transition-all duration-200 hover:shadow-md flex flex-col justify-between group ${
                entry.is_favorite
                  ? 'border-amber-300/80 shadow-xs bg-gradient-to-br from-amber-50/20 via-[#fdfbf7] to-[#fdfbf7]'
                  : 'border-stone-200/90 hover:border-stone-300'
              }`}
            >
              {/* Card Header: Word, Dictionary Entry, Audio & Favorite Star */}
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-xl font-serif font-bold text-stone-900 tracking-wide truncate">
                      {entry.word}
                    </h3>
                    <p className="text-xs font-serif italic text-stone-500 mt-0.5 truncate">
                      {entry.dictionary_entry}
                    </p>
                  </div>

                  {/* Actions: Audio Pronunciation & Pugillares Star */}
                  <div className="flex items-center gap-1 shrink-0">
                    <LatinAudioButton
                      text={entry.word}
                      audioUrl={entry.audio_url}
                      size="sm"
                    />

                    <button
                      onClick={(e) => handleToggleFavorite(entry, e)}
                      className={`p-1.5 rounded-lg transition-all ${
                        entry.is_favorite
                          ? 'text-amber-500 bg-amber-100/60 hover:bg-amber-200/70 hover:scale-110'
                          : 'text-stone-300 hover:text-amber-500 hover:bg-stone-100 hover:scale-110'
                      }`}
                      title={
                        entry.is_favorite
                          ? 'Remover dos Pugillares'
                          : 'Guardar nos Pugillares (Favoritos)'
                      }
                      aria-label={
                        entry.is_favorite
                          ? `Remover ${entry.word} dos favoritos`
                          : `Favoritar ${entry.word}`
                      }
                    >
                      <Star
                        className={`w-4 h-4 ${
                          entry.is_favorite ? 'fill-amber-400 text-amber-500' : ''
                        }`}
                      />
                    </button>
                  </div>
                </div>

                {/* Grammatical Class Badge */}
                <div>
                  <span
                    className={`inline-block px-2.5 py-0.5 rounded-md text-[11px] font-medium border ${getClassBadgeColor(
                      entry.grammatical_class
                    )}`}
                  >
                    {entry.grammatical_class}
                  </span>
                </div>

                {/* Portuguese Translation */}
                <div className="pt-1">
                  <p className="text-sm font-sans font-medium text-stone-800 leading-snug">
                    {entry.translation}
                  </p>
                </div>

                {/* Contextual Example Sentence */}
                {entry.example_sentence && (
                  <div className="pt-2 mt-2 border-t border-stone-100">
                    <div className="flex items-center justify-between gap-1 text-[11px] text-stone-400 uppercase tracking-wider font-semibold">
                      <span>Exemplo Clássico:</span>
                      <LatinAudioButton
                        text={entry.example_sentence}
                        size="sm"
                        className="scale-75 origin-right"
                      />
                    </div>
                    <p className="text-xs font-serif italic text-stone-700 mt-1">
                      "{entry.example_sentence}"
                    </p>
                  </div>
                )}
              </div>

              {/* Card Footer: Lesson Origin */}
              <div className="pt-3 mt-3 border-t border-stone-100 flex items-center justify-between text-[10px] text-stone-400">
                <span className="truncate" title={entry.lesson_title}>
                  📍 {entry.lesson_title}
                </span>
                {entry.is_favorite && (
                  <span className="shrink-0 text-amber-600 font-medium flex items-center gap-0.5">
                    <Star className="w-2.5 h-2.5 fill-amber-500 inline" /> Pugillaris
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
