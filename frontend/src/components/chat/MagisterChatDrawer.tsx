import React, { useState, useRef, useEffect } from 'react';
import {
  X,
  Send,
  Bot,
  BookOpen,
  Globe,
  Scroll,
  Loader2,
} from 'lucide-react';
import { chatApi } from '../../api/chatApi';
import { ChatConversationMessage } from '../../types/chat';
import { Button } from '../ui/Button';

interface MagisterChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  lessonId?: string | null;
  lessonTitle?: string;
  contextTopics?: string[];
}

export const MagisterChatDrawer: React.FC<MagisterChatDrawerProps> = ({
  isOpen,
  onClose,
  lessonId,
  lessonTitle,
  contextTopics = [],
}) => {
  const [messages, setMessages] = useState<ChatConversationMessage[]>([
    {
      id: 'init-1',
      sender: 'magister',
      text: `Salve, discipule! Sou o Magister Latium. Estou aqui para esclarecer qualquer dúvida sobre gramática, sintaxe ou história romana. Como posso auxiliá-lo hoje?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      suggested_questions: [
        'Como funciona a ordem das palavras em latim?',
        'Quem eram os Belgae na Gália de Júlio César?',
        'Qual a diferença entre o Nominativo e o Acusativo?',
      ],
    },
  ]);
  const [inputText, setInputText] = useState<string>('');
  const [isSending, setIsSending] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || inputText).trim();
    if (!text || isSending) return;

    const userMsg: ChatConversationMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsSending(true);

    try {
      const response = await chatApi.sendMessage({
        message: text,
        lesson_id: lessonId,
        context_topics: contextTopics,
      });

      const magisterMsg: ChatConversationMessage = {
        id: `magister-${Date.now()}`,
        sender: 'magister',
        text: response.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources_consulted: response.sources_consulted || [],
        historical_trivia_snippet: response.historical_trivia_snippet,
        suggested_questions: [
          'Como funciona a ordem das palavras em latim?',
          'O que era a Pronuntiatio Restituta?',
          'Pode me dar um exemplo de frase com acusativo?',
        ],
      };

      setMessages((prev) => [...prev, magisterMsg]);
    } catch (err) {
      console.error('Erro ao enviar mensagem ao Magister:', err);
      const errorMsg: ChatConversationMessage = {
        id: `err-${Date.now()}`,
        sender: 'magister',
        text: 'Peço escusas, discipule. Não consegui consultar a Biblioteca de Alexandria no momento. Por favor, reformule sua pergunta.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/40 backdrop-blur-sm animate-fadeIn">
      {/* Click outside to close */}
      <div className="flex-1" onClick={onClose} />

      {/* Slide-over Drawer Panel */}
      <div className="w-full max-w-lg bg-[#fdfbf7] h-full shadow-2xl border-l border-amber-300/60 flex flex-col relative z-10 animate-slideLeft">
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-stone-900 via-stone-800 to-amber-950 text-white border-b border-amber-500/30 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-400/40 text-amber-300 flex items-center justify-center">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-serif font-bold uppercase tracking-widest text-amber-400">
                  • MAGISTER INTERACTIVUS •
                </span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              </div>
              <h3 className="font-serif text-lg font-bold text-stone-100">
                Magister Latium
              </h3>
              {lessonTitle && (
                <p className="text-xs text-stone-300 truncate max-w-xs">
                  Aula: {lessonTitle}
                </p>
              )}
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-stone-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Message Thread */}
        <div className="flex-1 p-5 overflow-y-auto space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${
                msg.sender === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              {/* Message Bubble */}
              <div
                className={`max-w-[88%] rounded-2xl p-4 shadow-sm text-sm leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-slate-900 text-white rounded-br-none'
                    : 'bg-white text-stone-900 border border-amber-200/80 rounded-bl-none'
                }`}
              >
                <div className="flex items-center justify-between mb-1 text-[10px] opacity-70">
                  <span className="font-serif font-bold">
                    {msg.sender === 'user' ? 'Você' : 'Magister Latium'}
                  </span>
                  <span>{msg.timestamp}</span>
                </div>
                <p className="whitespace-pre-line">{msg.text}</p>

                {/* Sources Consulted Badges */}
                {msg.sources_consulted && msg.sources_consulted.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-amber-100 space-y-1.5">
                    <span className="text-[10px] font-serif font-bold uppercase tracking-wider text-amber-800 flex items-center gap-1">
                      <BookOpen className="w-3 h-3" />
                      <span>Fontes Clássicas Consultadas:</span>
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.sources_consulted.map((source, sIdx) => (
                        <span
                          key={sIdx}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#faf8f4] border border-amber-200/80 text-[11px] text-stone-700 font-serif"
                        >
                          {source.toLowerCase().includes('web') ||
                          source.toLowerCase().includes('arqueol') ? (
                            <Globe className="w-3 h-3 text-blue-600" />
                          ) : (
                            <Scroll className="w-3 h-3 text-amber-700" />
                          )}
                          <span>{source}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Historical Trivia Snippet */}
                {msg.historical_trivia_snippet && (
                  <div className="mt-2.5 p-2.5 rounded-xl bg-amber-50/60 border border-amber-200/80 text-xs space-y-1">
                    <span className="text-[10px] font-serif font-bold uppercase tracking-wider text-amber-900 block">
                      🏛️ Curiosidade da Roma Antiga:
                    </span>
                    <p className="text-[11px] text-stone-800 italic">
                      "{msg.historical_trivia_snippet}"
                    </p>
                  </div>
                )}
              </div>

              {/* Suggested Questions Pills */}
              {msg.suggested_questions && msg.suggested_questions.length > 0 && (
                <div className="mt-2.5 flex flex-wrap gap-1.5 max-w-[88%]">
                  {msg.suggested_questions.map((q, qIdx) => (
                    <button
                      key={qIdx}
                      type="button"
                      onClick={() => handleSend(q)}
                      className="px-2.5 py-1 rounded-full bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-900 text-[11px] font-medium transition-colors text-left"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* Typing / Sending indicator */}
          {isSending && (
            <div className="flex items-center gap-2 p-3 rounded-2xl bg-white border border-amber-200 max-w-xs animate-pulse text-xs text-stone-600 font-serif">
              <Loader2 className="w-4 h-4 animate-spin text-amber-600" />
              <span>Magister pesquisando nos códices clássicos...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-white border-t border-stone-200/80">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Pergunte sobre sintaxe, César, Cícero..."
              disabled={isSending}
              className="flex-1 px-4 py-2.5 rounded-xl border border-stone-300 focus:outline-none focus:ring-2 focus:ring-amber-500/50 text-sm bg-stone-50/50"
            />
            <Button
              variant="primary"
              onClick={() => handleSend()}
              disabled={!inputText.trim() || isSending}
              className="px-4 py-2.5 rounded-xl shadow-sm flex-shrink-0"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <p className="text-[10px] text-stone-400 mt-1.5 text-center">
            Respostas embasadas pelo acervo da Biblioteca de Alexandria e Web Clássica.
          </p>
        </div>
      </div>
    </div>
  );
};
