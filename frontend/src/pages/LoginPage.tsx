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
  FileSearch,
  BarChart3,
  Scale
} from 'lucide-react';

/* Use the CLEAN background without baked-in form */
const CLEAN_BG = "/juricob_login_background_1778105003101.png";

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
    <div className="min-h-screen flex bg-white font-sans antialiased overflow-hidden selection:bg-emerald-200">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Outfit:wght@300;400;500;600;700&display=swap');
        
        :root {
          --juricob-dark: #021C33;
          --juricob-accent: #10b981;
        }

        .font-serif-juricob { font-family: 'Cinzel', serif; }
        .font-sans-juricob { font-family: 'Outfit', sans-serif; }
        
        .branding-container {
          width: 58%;
          position: relative;
          background: var(--juricob-dark);
          overflow: hidden;
        }

        .bg-img-clean {
          position: absolute;
          inset: 0;
          background-image: url(${CLEAN_BG});
          background-size: cover;
          background-position: left center;
        }

        .bg-overlay-gradient {
          position: absolute;
          inset: 0;
          background: radial-gradient(circle at 40% 50%, rgba(2, 28, 51, 0.2) 0%, rgba(2, 28, 51, 0.9) 100%);
        }

        .white-curve-transition {
          position: absolute;
          top: 0;
          right: -100px;
          height: 100%;
          width: 250px;
          background: white;
          clip-path: ellipse(100% 100% at 100% 50%);
          z-index: 20;
          box-shadow: -20px 0 50px rgba(0,0,0,0.3);
        }

        .emerald-transition-line {
          position: absolute;
          top: 0;
          right: 140px;
          height: 100%;
          width: 8px;
          background: linear-gradient(to bottom, var(--juricob-accent), #059669);
          filter: blur(4px);
          z-index: 21;
          border-radius: 100% 0 0 100% / 50%;
        }

        .login-panel {
          flex: 1;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          background: white;
          z-index: 30;
          padding: 2rem;
        }

        .premium-card-v2 {
          width: 100%;
          max-width: 440px;
          background: white;
          border-radius: 2.5rem;
          box-shadow: 0 40px 100px -20px rgba(0,0,0,0.12);
          padding: 3.5rem 3rem;
        }

        .hexagon-logo-box {
           width: 60px;
           height: 60px;
           background: white;
           clip-path: polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%);
           display: flex;
           align-items: center;
           justify-content: center;
           margin-bottom: 1.5rem;
           box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        }

        .btn-gradient-target {
          background: linear-gradient(90deg, #021C33 0%, #064e3b 60%, #10b981 100%);
        }

        .logo-line-decoration {
          height: 1px;
          width: 240px;
          background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.4), transparent);
          margin-top: 1rem;
        }

        .feature-row {
          display: flex;
          align-items: center;
          gap: 1.25rem;
          opacity: 0.85;
          transition: transform 0.3s;
        }
        .feature-row:hover { transform: translateX(8px); opacity: 1; }
      `}</style>

      {/* Left Branding */}
      <div className="hidden lg:flex branding-container flex-col justify-center items-center">
        <div className="bg-img-clean" />
        <div className="bg-overlay-gradient" />
        <div className="white-curve-transition" />
        <div className="emerald-transition-line" />

        <div className="relative z-10 flex flex-col items-center mb-16">
          <div className="hexagon-logo-box">
             <Scale className="text-[#021C33] w-7 h-7" />
          </div>
          <h1 className="text-6xl font-bold text-white tracking-widest font-serif-juricob">
            JURICOB
          </h1>
          <div className="logo-line-decoration" />
        </div>

        <div className="relative z-10 space-y-8 text-white max-w-sm">
          <div className="feature-row">
            <div className="w-11 h-11 rounded-full border border-white/20 flex items-center justify-center bg-white/5">
              <Shield className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="font-bold text-sm font-sans-juricob">Seguro y confiable</p>
              <p className="text-white/50 text-[11px]">Protegemos tu información con altos estándares.</p>
            </div>
          </div>
          <div className="feature-row">
            <div className="w-11 h-11 rounded-full border border-white/20 flex items-center justify-center bg-white/5">
              <FileSearch className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="font-bold text-sm font-sans-juricob">Gestión eficiente</p>
              <p className="text-white/50 text-[11px]">Administra tus casos y documentos de manera ágil.</p>
            </div>
          </div>
          <div className="feature-row">
            <div className="w-11 h-11 rounded-full border border-white/20 flex items-center justify-center bg-white/5">
              <BarChart3 className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="font-bold text-sm font-sans-juricob">Información al día</p>
              <p className="text-white/50 text-[11px]">Accede a legislación y jurisprudencia actualizada.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Login */}
      <div className="login-panel">
        <div className="premium-card-v2 animate-in fade-in duration-700">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-normal text-[#021C33] font-serif-juricob uppercase tracking-widest mb-6">Acceso seguro</h2>
            <div className="flex items-center justify-center gap-4">
              <div className="h-[1px] flex-1 bg-slate-100"></div>
              <div className="w-16 h-16 rounded-full border-2 border-emerald-400/20 flex items-center justify-center bg-white shadow-inner">
                <Lock className="w-7 h-7 text-[#021C33]" />
              </div>
              <div className="h-[1px] flex-1 bg-slate-100"></div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-xs font-bold text-slate-600 ml-1">Correo electrónico</Label>
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500 transition-colors" />
                <Input
                  id="username"
                  type="text"
                  placeholder="ejemplo@correo.com"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="pl-12 h-12 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-xl"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-xs font-bold text-slate-600 ml-1">Contraseña</Label>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500 transition-colors" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-12 pr-12 h-12 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-xl"
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-300 hover:text-emerald-500">
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between px-1">
              <div className="flex items-center space-x-2">
                <input type="checkbox" id="rem" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} className="w-4 h-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-600" />
                <label htmlFor="rem" className="text-xs text-slate-500 font-medium">Recordarme</label>
              </div>
              <button type="button" className="text-xs font-bold text-emerald-700">¿Olvidaste tu contraseña?</button>
            </div>

            {loginError && <p className="text-red-500 text-[10px] text-center font-bold">{loginError}</p>}

            <Button type="submit" disabled={isSubmitting} className="btn-gradient-target w-full h-14 text-white rounded-xl font-bold text-lg flex items-center justify-center gap-3 shadow-xl shadow-emerald-900/10 active:scale-[0.98]">
              {isSubmitting ? <Loader2 className="h-5 w-5 animate-spin" /> : <><span>Iniciar sesión</span><ArrowRight className="h-5 w-5" /></>}
            </Button>

            <div className="relative py-2">
               <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-100"></div></div>
               <div className="relative flex justify-center text-[10px]"><span className="bg-white px-4 text-slate-400 font-bold uppercase tracking-widest">¿No tienes una cuenta?</span></div>
            </div>

            <Button variant="outline" className="w-full h-12 border-slate-200 text-[#021C33] font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-slate-50">Solicitar acceso</Button>
          </form>
        </div>

        {/* Footer */}
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
