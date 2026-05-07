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

/* USE THE ORIGINAL IMAGE AS REQUESTED FOR 100% FIDELITY */
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
    <div className="min-h-screen w-full relative bg-white flex overflow-hidden">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Outfit:wght@300;400;500;600;700&display=swap');
        
        .font-serif-juricob { font-family: 'Cinzel', serif; }
        .font-sans-juricob { font-family: 'Outfit', sans-serif; }

        .full-background {
          position: absolute;
          inset: 0;
          background-image: url(${LOGIN_BG});
          background-size: cover;
          background-position: center;
          z-index: 1;
        }

        .overlay-layer {
          position: relative;
          z-index: 10;
          width: 100%;
          height: 100vh;
          display: flex;
        }

        .branding-side {
          flex: 0 0 58%;
        }

        .login-side {
          flex: 1;
          display: flex;
          justify-content: center;
          align-items: center;
          background: white; /* This covers the mockup form in the background image on the right */
          padding: 2rem;
        }

        @media (max-width: 1024px) {
          .branding-side { display: none; }
          .login-side { flex: 1; background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(5px); }
        }

        .functional-card {
          width: 100%;
          max-width: 440px;
          background: white;
          border-radius: 2.5rem;
          box-shadow: 0 40px 100px -20px rgba(0,0,0,0.15);
          padding: 3.5rem 3rem;
          border: 1px solid #f1f5f9;
        }

        .premium-btn {
          background: linear-gradient(90deg, #021C33 0%, #064e3b 60%, #10b981 100%);
          transition: all 0.3s ease;
        }
        .premium-btn:hover {
           filter: brightness(1.1);
           transform: translateY(-1px);
        }
      `}</style>

      {/* The original image for the left side branding */}
      <div className="full-background" />

      {/* Functional Layout */}
      <div className="overlay-layer">
        {/* Left side stays empty to show the branding from the background image */}
        <div className="branding-side" />

        {/* Right side has a solid background to mask the mockup form and show the real one */}
        <div className="login-side">
          <div className="functional-card animate-in fade-in slide-in-from-right duration-700">
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
                <Label htmlFor="u" className="text-xs font-bold text-slate-700 ml-1">Correo electrónico</Label>
                <div className="relative group">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500 transition-colors" />
                  <Input id="u" type="text" placeholder="ejemplo@correo.com" value={username} onChange={(e) => setUsername(e.target.value)} className="pl-12 h-12 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-xl font-sans-juricob" />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="p" className="text-xs font-bold text-slate-700 ml-1">Contraseña</Label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500 transition-colors" />
                  <Input id="p" type={showPassword ? 'text' : 'password'} placeholder="••••••••••••" value={password} onChange={(e) => setPassword(e.target.value)} className="pl-12 pr-12 h-12 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-xl font-sans-juricob" />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-300">
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between px-1">
                <div className="flex items-center space-x-2">
                  <input type="checkbox" id="rem" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} className="w-4 h-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-600 cursor-pointer" />
                  <label htmlFor="rem" className="text-xs text-slate-500 font-medium">Recordarme</label>
                </div>
                <button type="button" className="text-xs font-bold text-emerald-700">¿Olvidaste tu contraseña?</button>
              </div>

              {loginError && <p className="text-red-500 text-[10px] text-center font-bold bg-red-50 py-2 rounded-lg">{loginError}</p>}

              <Button type="submit" disabled={isSubmitting} className="premium-btn w-full h-14 text-white rounded-xl font-bold text-lg flex items-center justify-center gap-3 shadow-xl shadow-emerald-900/10 active:scale-[0.98]">
                {isSubmitting ? <Loader2 className="h-5 w-5 animate-spin" /> : <><span>Iniciar sesión</span><ArrowRight className="h-5 w-5" /></>}
              </Button>

              <div className="relative py-2">
                 <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-100"></div></div>
                 <div className="relative flex justify-center text-[10px]"><span className="bg-white px-6 text-slate-400 font-bold uppercase tracking-widest">¿No tienes una cuenta?</span></div>
              </div>

              <Button variant="outline" className="w-full h-12 border-slate-200 text-[#021C33] font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-slate-50">Solicitar acceso</Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
