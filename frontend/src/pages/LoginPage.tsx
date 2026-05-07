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
  Mail,
  Shield,
  Headphones,
  FileSearch,
  BarChart3,
  Scale
} from 'lucide-react';

/* USE THE CLEAN BACKGROUND TO AVOID CUTOFFS AND DOUBLE LOGINS */
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
    <div className="min-h-screen flex bg-[#021C33] font-sans antialiased overflow-hidden selection:bg-emerald-200">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Outfit:wght@300;400;500;600;700&display=swap');
        
        .font-serif-juricob { font-family: 'Cinzel', serif; }
        .font-sans-juricob { font-family: 'Outfit', sans-serif; }

        .branding-area {
          flex: 0 0 62%;
          position: relative;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          padding: 4rem;
        }

        .clean-bg-layer {
          position: absolute;
          inset: 0;
          background-image: url(${CLEAN_BG});
          background-size: cover;
          background-position: left center;
          z-index: 1;
        }

        .dark-overlay {
          position: absolute;
          inset: 0;
          background: radial-gradient(circle at 30% 50%, rgba(2, 28, 51, 0.3) 0%, rgba(2, 28, 51, 0.9) 100%);
          z-index: 2;
        }

        .curve-transition {
          position: absolute;
          top: 0;
          right: -150px;
          height: 100%;
          width: 300px;
          background: white;
          clip-path: ellipse(100% 100% at 100% 50%);
          z-index: 20;
          box-shadow: -30px 0 60px rgba(0,0,0,0.4);
        }

        .login-area {
          flex: 1;
          background: white;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          position: relative;
          z-index: 30;
          padding: 2rem;
        }

        .premium-form-card {
          width: 100%;
          max-width: 440px;
          border-radius: 3rem;
          background: white;
          box-shadow: 0 40px 100px -20px rgba(0, 0, 0, 0.12);
          padding: 4rem 3rem;
        }

        .btn-premium-gradient {
          background: linear-gradient(90deg, #021C33 0%, #064e3b 60%, #10b981 100%);
        }

        .logo-decoration {
          height: 1.5px;
          width: 260px;
          background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.6), transparent);
          margin-top: 1.5rem;
        }

        .feature-item-row {
          display: flex;
          align-items: center;
          gap: 1.5rem;
          opacity: 0.9;
          transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .feature-item-row:hover { transform: translateX(10px); opacity: 1; }
      `}</style>

      {/* LEFT: Branding with Clean Background */}
      <div className="hidden lg:flex branding-area">
        <div className="clean-bg-layer" />
        <div className="dark-overlay" />
        <div className="curve-transition" />

        {/* Content Container shifted slightly left to avoid curve cutoff */}
        <div className="relative z-10 flex flex-col items-center mb-20 -translate-x-12">
           <div className="w-16 h-16 bg-white rotate-45 rounded-2xl shadow-2xl mb-8 flex items-center justify-center border border-emerald-100">
              <div className="-rotate-45">
                 <Scale className="text-[#021C33] w-8 h-8" />
              </div>
           </div>
           <h1 className="text-7xl font-bold text-white tracking-[0.2em] font-serif-juricob">
             JURICOB
           </h1>
           <div className="logo-decoration" />
        </div>

        <div className="relative z-10 space-y-10 -translate-x-12">
          <div className="feature-item-row">
            <div className="w-12 h-12 rounded-full border border-white/20 flex items-center justify-center bg-white/5 backdrop-blur-sm">
              <Shield className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h4 className="text-white font-bold text-base font-sans-juricob">Seguro y confiable</h4>
              <p className="text-white/40 text-xs">Protegemos tu información con altos estándares.</p>
            </div>
          </div>
          <div className="feature-item-row">
            <div className="w-12 h-12 rounded-full border border-white/20 flex items-center justify-center bg-white/5 backdrop-blur-sm">
              <FileSearch className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h4 className="text-white font-bold text-base font-sans-juricob">Gestión eficiente</h4>
              <p className="text-white/40 text-xs">Administra tus casos y documentos de manera ágil.</p>
            </div>
          </div>
          <div className="feature-item-row">
            <div className="w-12 h-12 rounded-full border border-white/20 flex items-center justify-center bg-white/5 backdrop-blur-sm">
              <BarChart3 className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h4 className="text-white font-bold text-base font-sans-juricob">Información al día</h4>
              <p className="text-white/40 text-xs">Accede a legislación y novedades actualizadas.</p>
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT: Functional Login */}
      <div className="login-area">
        <Card className="premium-form-card border-none animate-in fade-in zoom-in duration-700">
          <CardContent className="p-0 space-y-12">
            <div className="text-center">
              <h2 className="text-3xl font-normal text-[#021C33] font-serif-juricob uppercase tracking-widest mb-8">Acceso seguro</h2>
              <div className="flex items-center justify-center gap-6">
                <div className="h-[1px] flex-1 bg-slate-100"></div>
                <div className="w-20 h-20 rounded-full border-2 border-emerald-400/20 flex items-center justify-center bg-white shadow-inner">
                   <Lock className="w-8 h-8 text-[#021C33]" />
                </div>
                <div className="h-[1px] flex-1 bg-slate-100"></div>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">
              <div className="space-y-3">
                <Label htmlFor="u" className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Usuario</Label>
                <div className="relative group">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500 transition-colors" />
                  <Input id="u" type="text" placeholder="ejemplo@correo.com" value={username} onChange={(e) => setUsername(e.target.value)} className="pl-12 h-14 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-2xl" />
                </div>
              </div>

              <div className="space-y-3">
                <Label htmlFor="p" className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Contraseña</Label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500 transition-colors" />
                  <Input id="p" type={showPassword ? 'text' : 'password'} placeholder="••••••••••••" value={password} onChange={(e) => setPassword(e.target.value)} className="pl-12 pr-12 h-14 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-2xl" />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-300 hover:text-emerald-500 transition-colors">
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between px-1">
                <div className="flex items-center space-x-2">
                  <input type="checkbox" id="rem" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} className="w-4 h-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-600 cursor-pointer" />
                  <label htmlFor="rem" className="text-xs text-slate-500 font-medium cursor-pointer">Recordarme</label>
                </div>
                <button type="button" className="text-xs font-bold text-emerald-700 hover:opacity-80">¿Olvidaste tu contraseña?</button>
              </div>

              {loginError && <p className="text-red-500 text-[11px] text-center font-bold bg-red-50 py-2 rounded-lg">{loginError}</p>}

              <Button type="submit" disabled={isSubmitting} className="btn-premium-gradient w-full h-16 text-white rounded-2xl font-bold text-xl flex items-center justify-center gap-4 shadow-xl shadow-emerald-900/10 active:scale-[0.98] transition-all">
                {isSubmitting ? <Loader2 className="h-6 w-6 animate-spin" /> : <><span>Iniciar sesión</span><ArrowRight className="h-5 w-5" /></>}
              </Button>

              <div className="relative pt-2">
                 <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-100"></div></div>
                 <div className="relative flex justify-center text-[10px]"><span className="bg-white px-6 text-slate-400 font-bold uppercase tracking-widest">¿No tienes una cuenta?</span></div>
              </div>

              <Button variant="outline" className="w-full h-14 border-slate-200 text-[#021C33] font-bold rounded-2xl hover:bg-slate-50 transition-all">Solicitar acceso</Button>
            </form>
          </CardContent>
        </Card>

        {/* Footer Info */}
        <div className="flex items-center gap-12 mt-20 text-slate-400">
           <div className="flex items-center gap-3">
              <Shield className="w-6 h-6 text-[#021C33]" />
              <span className="uppercase tracking-[0.2em] text-[10px] font-bold">Plataforma Segura</span>
           </div>
           <div className="w-[1px] h-10 bg-slate-100" />
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
