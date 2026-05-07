import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { 
  Lock, 
  User,
  Eye, 
  EyeOff,
  Loader2,
  ArrowRight,
  Mail
} from 'lucide-react';

const LOGIN_BG = "/login.png";

export default function LoginPage() {
  const [username, setUsername] = useState('juricob');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [rememberMe, setRememberMe] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/consultar';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setLoginError('Por favor ingrese usuario y contraseña');
      return;
    }
    setLoginError(null);
    setIsSubmitting(true);
    const result = await login({ username, password });
    setIsSubmitting(false);
    if (result.success) {
      navigate(from, { replace: true });
    } else {
      setLoginError(result.error || 'Usuario o contraseña incorrectos');
    }
  };

  return (
    <div className="min-h-screen w-full relative flex overflow-hidden bg-[#F8FAFC]">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Outfit:wght@300;400;500;600;700&display=swap');
        
        .font-serif-juricob { font-family: 'Cinzel', serif; }
        .font-sans-juricob { font-family: 'Outfit', sans-serif; }

        .full-bg-container {
          position: absolute;
          inset: 0;
          background-image: url(${LOGIN_BG});
          background-size: cover;
          background-position: center;
          z-index: 1;
        }

        .content-overlay {
          position: relative;
          z-index: 10;
          width: 100%;
          height: 100vh;
          display: flex;
        }

        /* Responsive spacing to align with the mockup form area */
        .form-container-wrapper {
          flex: 1;
          display: flex;
          justify-content: flex-end;
          align-items: center;
          padding-right: 8%; /* Adjust to center over the mockup card */
        }

        @media (max-width: 1024px) {
          .full-bg-container {
            background-position: 75% center;
          }
          .form-container-wrapper {
            padding-right: 0;
            justify-content: center;
          }
          .branding-spacer {
             display: none;
          }
        }

        .glass-login-card {
          width: 100%;
          max-width: 420px;
          background: white;
          border-radius: 2.5rem;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
          padding: 3rem 2.5rem;
        }

        .btn-premium-gradient {
          background: linear-gradient(90deg, #021C33 0%, #064e3b 60%, #10b981 100%);
        }
      `}</style>

      {/* The actual image as background */}
      <div className="full-bg-container" />

      {/* Functional Overlay */}
      <div className="content-overlay">
        {/* Spacer for the branding side of the image */}
        <div className="hidden lg:block branding-spacer" style={{ flex: '0 0 58%' }} />

        {/* The functional form aligned over the mockup card */}
        <div className="form-container-wrapper">
          <div className="glass-login-card animate-in fade-in zoom-in duration-700">
            <div className="text-center mb-8">
               <h1 className="text-2xl font-normal text-[#021C33] font-serif-juricob uppercase tracking-widest mb-6">Acceso seguro</h1>
               <div className="flex items-center justify-center gap-4">
                  <div className="h-[1px] flex-1 bg-slate-100"></div>
                  <div className="w-16 h-16 rounded-full border border-emerald-400 flex items-center justify-center bg-white shadow-sm">
                    <Lock className="w-7 h-7 text-[#021C33]" />
                  </div>
                  <div className="h-[1px] flex-1 bg-slate-100"></div>
               </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-xs font-bold text-slate-700 font-sans-juricob ml-1">Correo electrónico</Label>
                <div className="relative group">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500 transition-colors" />
                  <Input
                    id="username"
                    type="text"
                    placeholder="ejemplo@correo.com"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="pl-12 h-12 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-xl font-sans-juricob"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-xs font-bold text-slate-700 font-sans-juricob ml-1">Contraseña</Label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500 transition-colors" />
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-12 pr-12 h-12 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-xl font-sans-juricob"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-300"
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between px-1">
                <div className="flex items-center space-x-2">
                  <input 
                    type="checkbox" 
                    id="remember" 
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-600"
                  />
                  <label htmlFor="remember" className="text-xs text-slate-500 font-medium cursor-pointer">Recordarme</label>
                </div>
                <button
                  type="button"
                  className="text-xs font-bold text-emerald-700 hover:text-emerald-500 transition-colors"
                >
                  ¿Olvidaste tu contraseña?
                </button>
              </div>

              {loginError && (
                <p className="text-red-500 text-[10px] text-center font-bold">{loginError}</p>
              )}

              <Button 
                type="submit" 
                disabled={isSubmitting}
                className="btn-premium-gradient w-full h-14 text-white rounded-xl font-bold text-lg flex items-center justify-center gap-3 shadow-lg shadow-emerald-900/10 hover:opacity-95 active:scale-[0.98] transition-all"
              >
                {isSubmitting ? <Loader2 className="h-5 w-5 animate-spin" /> : (
                  <>
                    <span>Iniciar sesión</span>
                    <ArrowRight className="h-5 w-5" />
                  </>
                )}
              </Button>

              <div className="relative py-2">
                 <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-slate-100"></div>
                 </div>
                 <div className="relative flex justify-center text-[10px]">
                    <span className="bg-white px-4 text-slate-400 font-bold uppercase tracking-widest">¿No tienes una cuenta?</span>
                 </div>
              </div>

              <Button 
                 variant="outline" 
                 className="w-full h-12 border-slate-200 text-[#021C33] font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-slate-50 transition-all active:scale-[0.98]"
              >
                 Solicitar acceso
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
