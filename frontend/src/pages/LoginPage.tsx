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
  Headphones
} from 'lucide-react';

/* Use the original login.png but only for the branding side */
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
    <div className="min-h-screen flex bg-white font-sans antialiased overflow-hidden">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Outfit:wght@300;400;500;600;700&display=swap');
        
        .font-serif-juricob { font-family: 'Cinzel', serif; }
        .font-sans-juricob { font-family: 'Outfit', sans-serif; }

        .branding-container {
          flex: 0 0 60%;
          position: relative;
          background: #021C33;
          overflow: hidden;
        }

        .branding-bg-image {
          position: absolute;
          inset: 0;
          background-image: url(${LOGIN_BG});
          background-size: cover;
          background-position: left center;
          /* Ensure we only show the left 60% of the image to hide the mockup form */
          width: 100%; 
        }

        .curve-overlay-v3 {
          position: absolute;
          top: 0;
          right: -120px;
          height: 100%;
          width: 240px;
          background: white;
          clip-path: ellipse(100% 100% at 100% 50%);
          z-index: 20;
          box-shadow: -20px 0 40px rgba(0,0,0,0.2);
        }

        .login-panel-v3 {
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

        .target-card {
          width: 100%;
          max-width: 420px;
          border-radius: 2.5rem;
          background: white;
          box-shadow: 0 30px 60px -12px rgba(0,0,0,0.1);
          padding: 3rem 2.5rem;
        }

        .target-btn-gradient {
          background: linear-gradient(90deg, #021C33 0%, #064e3b 60%, #10b981 100%);
        }
      `}</style>

      {/* Left side: Branding (Original Image clipped) */}
      <div className="hidden lg:block branding-container">
        <div className="branding-bg-image" />
        <div className="curve-overlay-v3" />
      </div>

      {/* Right side: Pure functional Login */}
      <div className="login-panel-v3">
        <div className="target-card animate-in fade-in duration-500">
           <div className="text-center mb-10">
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
                <Label htmlFor="user" className="text-xs font-bold text-slate-600 ml-1">Correo electrónico</Label>
                <div className="relative group">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500" />
                  <Input
                    id="user"
                    type="text"
                    placeholder="ejemplo@correo.com"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="pl-12 h-12 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-xl font-sans-juricob"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="pass" className="text-xs font-bold text-slate-600 ml-1">Contraseña</Label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500" />
                  <Input
                    id="pass"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-12 pr-12 h-12 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-xl font-sans-juricob"
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-300">
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between px-1">
                <div className="flex items-center space-x-2">
                  <input type="checkbox" id="rem-me" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} className="w-4 h-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-600" />
                  <label htmlFor="rem-me" className="text-xs text-slate-500 font-medium">Recordarme</label>
                </div>
                <button type="button" className="text-xs font-bold text-emerald-700">¿Olvidaste tu contraseña?</button>
              </div>

              {loginError && <p className="text-red-500 text-[10px] text-center font-bold">{loginError}</p>}

              <Button type="submit" disabled={isSubmitting} className="target-btn-gradient w-full h-14 text-white rounded-xl font-bold text-lg flex items-center justify-center gap-3 shadow-xl shadow-emerald-900/10 active:scale-[0.98]">
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
