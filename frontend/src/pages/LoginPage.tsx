import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { 
  Shield, 
  Lock, 
  User,
  Eye, 
  EyeOff,
  Loader2,
  ArrowRight,
  Mail,
  Headphones,
  FileSearch,
  BarChart3,
  Scale
} from 'lucide-react';

const LOGIN_BG = "/juricob_login_background_1778105003101.png";

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
    <div className="min-h-screen flex bg-white font-sans antialiased overflow-hidden selection:bg-emerald-200 selection:text-emerald-900">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&family=Outfit:wght@300;400;500;600;700&display=swap');
        
        :root {
          --juricob-dark: #021C33;
          --juricob-accent: #10b981;
          --juricob-accent-dark: #064e3b;
        }

        .font-serif-juricob { font-family: 'Cinzel', serif; }
        .font-sans-juricob { font-family: 'Outfit', sans-serif; }
        
        .branding-section {
          width: 62%;
          position: relative;
          background: var(--juricob-dark);
          overflow: hidden;
        }

        .bg-image {
          position: absolute;
          inset: 0;
          background-image: url(${LOGIN_BG});
          background-size: cover;
          background-position: left center;
          opacity: 0.9;
        }

        .bg-overlay {
          position: absolute;
          inset: 0;
          background: radial-gradient(circle at 30% 50%, rgba(2, 28, 51, 0.2) 0%, rgba(2, 28, 51, 0.85) 100%);
        }

        .curve-container {
          position: absolute;
          top: 0;
          right: 0;
          height: 100%;
          width: 250px;
          z-index: 20;
          pointer-events: none;
        }

        .curve-shape {
          position: absolute;
          top: 0;
          right: -100px;
          height: 100%;
          width: 350px;
          background: white;
          clip-path: ellipse(100% 100% at 100% 50%);
          box-shadow: -30px 0 60px rgba(0,0,0,0.4);
        }

        .emerald-curve {
          position: absolute;
          top: 0;
          right: 150px;
          height: 100%;
          width: 100px;
          background: linear-gradient(to right, transparent, var(--juricob-accent-dark), var(--juricob-accent));
          opacity: 0.8;
          clip-path: ellipse(100% 100% at 100% 50%);
          z-index: 19;
        }

        .login-section {
          flex: 1;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          background: white;
          position: relative;
          z-index: 30;
          padding: 2rem;
        }

        .premium-card {
          width: 100%;
          max-width: 440px;
          border-radius: 3rem;
          background: white;
          box-shadow: 0 40px 100px -20px rgba(0, 0, 0, 0.1);
          border: 1px solid #f1f5f9;
        }

        .btn-target-gradient {
          background: linear-gradient(90deg, #021C33 0%, #064e3b 60%, #10b981 100%);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .btn-target-gradient:hover {
          filter: brightness(1.1);
          transform: translateY(-1px);
          box-shadow: 0 12px 24px -8px rgba(16, 185, 129, 0.5);
        }

        .logo-underline {
          height: 1px;
          width: 200px;
          background: linear-gradient(90deg, transparent 0%, rgba(16, 185, 129, 0.5) 50%, transparent 100%);
          margin-top: 1rem;
        }

        .feature-box {
           transition: transform 0.3s ease;
        }
        .feature-box:hover {
           transform: translateX(10px);
        }
      `}</style>

      {/* Left Branding Area */}
      <div className="hidden lg:flex branding-section flex-col justify-center p-20">
        <div className="bg-image" />
        <div className="bg-overlay" />
        
        {/* Animated Curves */}
        <div className="curve-container">
           <div className="emerald-curve animate-pulse" style={{ animationDuration: '4s' }} />
           <div className="curve-shape" />
        </div>

        <div className="relative z-10 flex flex-col items-center mb-24 max-w-xl mx-auto">
          {/* Logo Hexagon ABOVE */}
          <div className="w-16 h-16 bg-[#F8FAFC] flex items-center justify-center rotate-45 rounded-xl shadow-2xl mb-6 border border-emerald-100">
            <div className="-rotate-45 flex items-center justify-center">
               <Scale className="text-[#021C33] w-8 h-8" />
            </div>
          </div>
          <h1 className="text-7xl font-bold text-white tracking-tighter font-serif-juricob">
            JURICOB
          </h1>
          <div className="logo-underline" />
        </div>

        {/* Features List */}
        <div className="relative z-10 space-y-10 max-w-md mx-auto">
          <div className="feature-box flex items-center gap-6">
            <div className="w-12 h-12 rounded-full border border-white/20 flex items-center justify-center bg-white/5 backdrop-blur-sm">
              <Shield className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h4 className="text-white font-bold font-sans-juricob">Seguro y confiable</h4>
              <p className="text-white/50 text-sm leading-tight">Protegemos tu información con los más altos estándares.</p>
            </div>
          </div>

          <div className="feature-box flex items-center gap-6">
            <div className="w-12 h-12 rounded-full border border-white/20 flex items-center justify-center bg-white/5 backdrop-blur-sm">
              <FileSearch className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h4 className="text-white font-bold font-sans-juricob">Gestión eficiente</h4>
              <p className="text-white/50 text-sm leading-tight">Administra tus casos y documentos de manera ágil.</p>
            </div>
          </div>

          <div className="feature-box flex items-center gap-6">
            <div className="w-12 h-12 rounded-full border border-white/20 flex items-center justify-center bg-white/5 backdrop-blur-sm">
              <BarChart3 className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h4 className="text-white font-bold font-sans-juricob">Información al día</h4>
              <p className="text-white/50 text-sm leading-tight">Accede a legislación y jurisprudencia actualizada.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Login Area */}
      <div className="login-section">
        <Card className="premium-card border-none p-12 lg:p-16 animate-in slide-in-from-right duration-700">
          <CardContent className="p-0 space-y-12">
            
            <div className="text-center space-y-4">
               <h1 className="text-3xl font-normal text-[#021C33] font-serif-juricob uppercase tracking-widest">Acceso seguro</h1>
               <div className="flex items-center justify-center">
                  <div className="w-16 h-16 rounded-full border-2 border-emerald-400/30 flex items-center justify-center bg-white">
                    <Lock className="w-7 h-7 text-[#021C33]" />
                  </div>
               </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">
              <div className="space-y-3">
                <Label htmlFor="username" className="text-xs font-bold text-slate-700 ml-1">Correo electrónico</Label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300" />
                  <Input
                    id="username"
                    type="text"
                    placeholder="ejemplo@correo.com"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="pl-12 h-14 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-2xl font-sans-juricob"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <Label htmlFor="password" className="text-xs font-bold text-slate-700 ml-1">Contraseña</Label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300" />
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-12 pr-12 h-14 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-2xl font-sans-juricob"
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
                  <label htmlFor="remember" className="text-xs text-slate-500 font-medium">Recordarme</label>
                </div>
                <button
                  type="button"
                  className="text-xs font-bold text-emerald-700"
                >
                  ¿Olvidaste tu contraseña?
                </button>
              </div>

              {loginError && (
                <p className="text-red-500 text-xs text-center font-bold">{loginError}</p>
              )}

              <button 
                type="submit" 
                disabled={isSubmitting}
                className="btn-target-gradient w-full h-16 text-white rounded-2xl font-bold text-xl flex items-center justify-center gap-4 shadow-xl shadow-emerald-900/10 active:scale-95"
              >
                {isSubmitting ? <Loader2 className="h-6 w-6 animate-spin" /> : (
                  <>
                    <span>Iniciar sesión</span>
                    <ArrowRight className="h-6 w-6" />
                  </>
                )}
              </button>

              <div className="relative pt-4">
                 <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-slate-100"></div>
                 </div>
                 <div className="relative flex justify-center text-[11px]">
                    <span className="bg-white px-6 text-slate-400 font-bold uppercase tracking-widest">¿No tienes una cuenta?</span>
                 </div>
              </div>

              <Button 
                 variant="outline" 
                 className="w-full h-14 border-slate-200 text-[#021C33] font-bold rounded-2xl flex items-center justify-center gap-2 hover:bg-slate-50 transition-all"
              >
                 <User className="w-4 h-4 text-slate-400" />
                 Solicitar acceso
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Footer Branding aligned right as in mockup */}
        <div className="flex items-center gap-10 mt-16 text-slate-400">
           <div className="flex items-center gap-3">
              <Shield className="w-6 h-6 text-[#021C33]" />
              <span className="uppercase tracking-[0.2em] text-[10px] font-bold">Plataforma Segura</span>
           </div>
           <div className="w-[1px] h-8 bg-slate-100" />
           <div className="flex items-center gap-3">
              <Headphones className="w-6 h-6 text-[#021C33]" />
              <div className="flex flex-col text-[10px] leading-tight font-bold">
                 <span className="uppercase tracking-[0.1em]">Soporte Especializado</span>
                 <span className="text-slate-400 font-normal">Asistencia profesional.</span>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
