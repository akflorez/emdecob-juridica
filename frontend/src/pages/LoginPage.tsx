import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { 
  Shield, 
  Lock, 
  User,
  Eye, 
  EyeOff,
  Loader2,
  ArrowRight,
  TrendingUp,
  Briefcase,
  Mail,
  Headphones
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
  const { toast } = useToast();

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
    <div className="min-h-screen flex bg-[#F4F7F9] font-sans antialiased overflow-hidden">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Outfit:wght@300;400;500;600&display=swap');
        .font-serif-juricob { font-family: 'Cinzel', serif; }
        .font-sans-juricob { font-family: 'Outfit', sans-serif; }
        .curve-divider {
          clip-path: ellipse(100% 100% at 0% 50%);
        }
        .login-card {
          box-shadow: 0 10px 40px rgba(0,0,0,0.08);
          border-radius: 40px;
        }
        .btn-gradient {
          background: linear-gradient(90deg, #021C33 0%, #044D29 100%);
        }
      `}</style>

      {/* Left Panel - Curve Design */}
      <div className="hidden lg:flex lg:w-[55%] relative curve-divider z-20">
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${LOGIN_BG})` }}
        />
        <div 
          className="absolute inset-0"
          style={{
            background: 'linear-gradient(90deg, rgba(2, 28, 51, 0.4) 0%, rgba(2, 28, 51, 0.9) 100%)',
          }}
        />

        <div className="relative z-30 flex flex-col justify-center items-center w-full px-16 text-white text-center">
          {/* Logo with specific Icon from image */}
          <div className="mb-12 flex flex-col items-center">
             <div className="w-14 h-14 bg-white rounded-xl flex items-center justify-center mb-4 shadow-xl">
                <div className="w-10 h-10 border-[3px] border-[#023136] rounded-md flex items-center justify-center rotate-45">
                   <div className="w-5 h-5 bg-[#023136] rounded-sm -rotate-45" />
                </div>
             </div>
             <h1 className="text-8xl font-bold font-serif-juricob tracking-tighter leading-none">JURICOB</h1>
             <div className="h-[2px] w-48 bg-gradient-to-r from-transparent via-emerald-400 to-transparent mt-4 opacity-50" />
          </div>

          {/* Features List exactly as image */}
          <div className="space-y-12 text-left max-w-md">
            <div className="flex items-start gap-6">
              <div className="mt-1 w-12 h-12 rounded-full border border-white/20 bg-white/5 flex items-center justify-center">
                <Shield className="w-6 h-6 text-white/90" />
              </div>
              <div>
                <h3 className="font-bold text-xl font-sans-juricob">Seguro y confiable</h3>
                <p className="text-white/60 text-base font-light leading-snug">Protegemos tu información con los más altos estándares.</p>
              </div>
            </div>

            <div className="flex items-start gap-6">
              <div className="mt-1 w-12 h-12 rounded-full border border-white/20 bg-white/5 flex items-center justify-center">
                <Briefcase className="w-6 h-6 text-white/90" />
              </div>
              <div>
                <h3 className="font-bold text-xl font-sans-juricob">Gestión eficiente</h3>
                <p className="text-white/60 text-base font-light leading-snug">Administra tus casos y documentos de manera ágil y centralizada.</p>
              </div>
            </div>

            <div className="flex items-start gap-6">
              <div className="mt-1 w-12 h-12 rounded-full border border-white/20 bg-white/5 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white/90" />
              </div>
              <div>
                <h3 className="font-bold text-xl font-sans-juricob">Información al día</h3>
                <p className="text-white/60 text-base font-light leading-snug">Accede a legislación, jurisprudencia y novedades jurídicas.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Card */}
      <div className="w-full lg:w-[45%] flex flex-col justify-between items-center py-12 px-8">
        <div className="w-full max-w-lg flex flex-col items-center">
          <Card className="login-card border-none bg-white w-full p-12 space-y-8 mt-12">
            <CardContent className="p-0 space-y-10">
              
              {/* Header Icon matching image circle */}
              <div className="flex items-center justify-center gap-8">
                 <div className="h-px flex-1 bg-gray-200"></div>
                 <div className="w-16 h-16 rounded-full border-[1.5px] border-emerald-500 flex items-center justify-center bg-white">
                    <Lock className="w-6 h-6 text-emerald-600" />
                 </div>
                 <div className="h-px flex-1 bg-gray-200"></div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-8">
                <div className="space-y-3">
                  <Label htmlFor="username" className="text-sm font-bold text-[#021C33] ml-1">Correo electrónico</Label>
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                    <Input
                      id="username"
                      type="text"
                      placeholder="ejemplo@correo.com"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="pl-12 h-14 bg-gray-50 border-gray-200 focus:border-emerald-500 rounded-xl font-sans-juricob"
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  <Label htmlFor="password" className="text-sm font-bold text-[#021C33] ml-1">Contraseña</Label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-12 pr-12 h-14 bg-gray-50 border-gray-200 focus:border-emerald-500 rounded-xl font-sans-juricob"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400"
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
                      className="w-4 h-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                    />
                    <label htmlFor="remember" className="text-sm text-slate-500 cursor-pointer font-medium">Recordarme</label>
                  </div>
                  <button
                    type="button"
                    className="text-sm font-bold text-emerald-600 hover:text-emerald-700"
                  >
                    ¿Olvidaste tu contraseña?
                  </button>
                </div>

                {loginError && (
                  <p className="text-red-500 text-sm text-center font-medium">{loginError}</p>
                )}

                <button 
                  type="submit" 
                  disabled={isSubmitting}
                  className="btn-gradient w-full h-16 text-white rounded-xl font-bold text-xl flex items-center justify-center gap-4 shadow-xl hover:opacity-90 transition-all active:scale-[0.98]"
                >
                  {isSubmitting ? <Loader2 className="h-6 w-6 animate-spin" /> : (
                    <>
                      <span>Iniciar sesión</span>
                      <ArrowRight className="h-6 w-6" />
                    </>
                  )}
                </button>

                <div className="relative py-2">
                   <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-100"></div>
                   </div>
                   <div className="relative flex justify-center text-sm">
                      <span className="bg-white px-4 text-gray-400 font-medium">¿No tienes una cuenta?</span>
                   </div>
                </div>

                <Button 
                   variant="outline" 
                   className="w-full h-16 border-emerald-500/30 text-slate-600 font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-emerald-50"
                >
                   <User className="w-5 h-5 text-emerald-600" />
                   Solicitar acceso
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Footer exactly like image */}
        <div className="flex items-center gap-12 text-slate-400 text-sm font-medium mt-8">
           <div className="flex items-center gap-3">
              <Shield className="w-6 h-6 text-[#021C33]" />
              <span className="uppercase tracking-wider text-xs">Plataforma Segura</span>
           </div>
           <div className="w-px h-10 bg-gray-200" />
           <div className="flex items-center gap-3">
              <Headphones className="w-6 h-6 text-[#021C33]" />
              <div className="flex flex-col text-[10px] leading-tight">
                 <span className="uppercase tracking-wider font-bold">Soporte Especializado</span>
                 <span>Asistencia profesional.</span>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
