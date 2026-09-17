import { Component, ErrorInfo, ReactNode } from 'react';
import { RotateCcw, AlertOctagon } from 'lucide-react';
import { Button } from '../ui/Button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Latium AI ErrorBoundary capturou exceção não tratada:', error, errorInfo);
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleResetSession = () => {
    localStorage.removeItem('latium_refresh_token');
    window.location.href = '/';
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#fdfbf7] flex flex-col items-center justify-center p-6 text-stone-800">
          <div className="max-w-md w-full bg-white rounded-3xl border-2 border-amber-300/80 p-8 shadow-xl text-center space-y-5 animate-fadeIn">
            <div className="w-16 h-16 rounded-2xl bg-amber-100/80 border border-amber-300/80 flex items-center justify-center mx-auto text-amber-800 shadow-inner">
              <AlertOctagon className="w-8 h-8 text-amber-700" />
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-serif font-bold uppercase tracking-widest text-amber-800">
                • LATIUM AI RECOVERY •
              </span>
              <h2 className="font-serif text-2xl font-bold text-stone-900">
                Instabilidade na Interface
              </h2>
              <p className="text-xs text-stone-600 leading-relaxed">
                Ocorreu uma discrepância inesperada ao renderizar a página. Seus dados de progresso e histórico estão seguros no banco de dados.
              </p>
            </div>

            {this.state.error && (
              <div className="p-3 rounded-xl bg-stone-50 border border-stone-200 text-left overflow-x-auto text-[11px] font-mono text-stone-600 max-h-24">
                {this.state.error.message}
              </div>
            )}

            <div className="flex flex-col sm:flex-row items-center justify-center gap-2.5 pt-2">
              <Button variant="primary" onClick={this.handleReload} className="w-full sm:w-auto shadow-md">
                <RotateCcw className="w-4 h-4 mr-1.5" />
                <span>Recarregar Página</span>
              </Button>
              <Button variant="secondary" onClick={this.handleResetSession} className="w-full sm:w-auto">
                <span>Reiniciar Sessão</span>
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
