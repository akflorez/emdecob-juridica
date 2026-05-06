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
  Mail,
  Headphones
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
          box-shadow: 0 15px 50px rgba(0,0,0,0.06);
          border-radius: 40px;
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
        }
        .btn-gradient {
          background: linear-gradient(90deg, #021C33 0%, #044D29 100%);
        }
      `}</style>

      {/* Left Panel - Branding Area */}
      <div className="hidden lg:flex lg:w-[60%] relative curve-divider z-20">
        <div 
          className="absolute inset-0 bg-cover bg-left"
          style={{ backgroundImage: `url(${LOGIN_BG})` }}
        />
        {/* We keep the branding part from the original image as it's already there */}
      </div>

      {/* Right Panel - Login Form */}
      <div className="w-full lg:w-[40%] flex flex-col justify-between items-center py-12 px-8 relative z-30">
        <div className="w-full max-w-md flex flex-col items-center flex-1 justify-center">
          <Card className="login-card border-none w-full p-10 space-y-8">
            <CardContent className="p-0 space-y-8">
              
              <div className="text-center space-y-1">
                 <h2 className="text-2xl font-normal text-[#021C33] font-serif-juricob">Acceso seguro</h2>
              </div>

              {/* Icon Section with Lines */}
              <div className="flex items-center justify-center gap-6">
                 <div className="h-[1px] flex-1 bg-gray-200"></div>
                 <div className="w-14 h-14 rounded-full border border-emerald-500 flex items-center justify-center bg-white shadow-sm">
                    <Lock className="w-5 h-5 text-emerald-600" />
                 </div>
                 <div className="h-[1px] flex-1 bg-gray-200"></div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="username" className="text-sm font-bold text-[#021C33] ml-1">Correo electrónico</Label>
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                    <Input
                      id="username"
                      type="text"
                      placeholder="ejemplo@correo.com"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="pl-12 h-14 bg-gray-50 border-gray-100 focus:border-emerald-500 rounded-xl font-sans-juricob text-sm"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-bold text-[#021C33] ml-1">Contraseña</Label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-12 pr-12 h-14 bg-gray-50 border-gray-100 focus:border-emerald-500 rounded-xl font-sans-juricob text-sm"
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
                    <label htmlFor="remember" className="text-xs text-slate-500 cursor-pointer font-medium">Recordarme</label>
                  </div>
                  <button
                    type="button"
                    className="text-xs font-bold text-emerald-700 hover:opacity-80"
                  >
                    ¿Olvidaste tu contraseña?
                  </button>
                </div>

                {loginError && (
                  <p className="text-red-500 text-xs text-center font-semibold">{loginError}</p>
                )}

                <button 
                  type="submit" 
                  disabled={isSubmitting}
                  className="btn-gradient w-full h-14 text-white rounded-xl font-bold text-lg flex items-center justify-center gap-3 shadow-lg hover:shadow-emerald-900/20 transition-all"
                >
                  {isSubmitting ? <Loader2 className="h-6 w-6 animate-spin" /> : (
                    <>
                      <span>Iniciar sesión</span>
                      <ArrowRight className="h-5 w-5" />
                    </>
                  )}
                </button>

                <div className="relative py-2">
                   <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-100"></div>
                   </div>
                   <div className="relative flex justify-center text-[10px]">
                      <span className="bg-white px-2 text-gray-400 font-medium uppercase tracking-wider">¿No tienes una cuenta?</span>
                   </div>
                </div>

                <Button 
                   variant="outline" 
                   className="w-full h-14 border-emerald-500/20 text-slate-600 font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-emerald-50 hover:text-emerald-700 transition-colors"
                >
                   <User className="w-5 h-5" />
                   Solicitar acceso
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Bottom Footer Section */}
        <div className="flex items-center gap-10 text-slate-500 font-medium mt-auto">
           <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-[#021C33]" />
              <span className="uppercase tracking-[0.2em] text-[10px] font-bold">Plataforma Segura</span>
           </div>
           <div className="w-[1px] h-8 bg-gray-200" />
           <div className="flex items-center gap-2">
              <Headphones className="w-5 h-5 text-[#021C33]" />
              <div className="flex flex-col text-[9px] leading-tight font-bold">
                 <span className="uppercase tracking-[0.1em]">Soporte Especializado</span>
                 <span className="text-slate-400 font-normal">Asistencia profesional.</span>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
