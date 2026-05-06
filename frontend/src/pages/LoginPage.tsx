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
    <div className="min-h-screen flex bg-white font-sans antialiased overflow-hidden">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Outfit:wght@300;400;500;600&display=swap');
        .font-serif-juricob { font-family: 'Cinzel', serif; }
        .font-sans-juricob { font-family: 'Outfit', sans-serif; }
        
        .premium-curve {
          position: relative;
          width: 55%;
          height: 100vh;
          overflow: hidden;
          background: #021C33;
        }
        
        .premium-curve::after {
          content: "";
          position: absolute;
          top: 0;
          right: -150px;
          width: 300px;
          height: 100%;
          background: white;
          border-left: 8px solid #4ade80; /* The emerald green edge */
          border-radius: 100% 0 0 100% / 50%;
          box-shadow: -20px 0 50px rgba(0,0,0,0.3);
          z-index: 25;
        }

        .login-card {
          box-shadow: 0 25px 60px rgba(0,0,0,0.1);
          border-radius: 45px;
          background: white;
        }

        .btn-gradient {
          background: linear-gradient(90deg, #021C33 0%, #044D29 100%);
        }
      `}</style>

      {/* Left Panel - The real arc design */}
      <div className="hidden lg:block premium-curve z-20">
        <div 
          className="absolute inset-0 bg-cover bg-left scale-110"
          style={{ backgroundImage: `url(${LOGIN_BG})` }}
        />
        {/* Deep blue overlay for text readability */}
        <div 
          className="absolute inset-0"
          style={{
            background: 'linear-gradient(90deg, rgba(2, 28, 51, 0.4) 0%, rgba(2, 28, 51, 0.8) 100%)',
          }}
        />
      </div>

      {/* Right Panel - Login Card */}
      <div className="w-full lg:w-[45%] flex flex-col justify-center items-center py-12 px-8 bg-white z-30">
        <div className="w-full max-w-md flex flex-col items-center">
          <Card className="login-card border-none w-full p-12 space-y-8">
            <CardContent className="p-0 space-y-10">
              
              <div className="text-center">
                 <h2 className="text-2xl font-normal text-[#021C33] font-serif-juricob uppercase tracking-widest opacity-80">Acceso seguro</h2>
              </div>

              {/* Icon Section with Lines */}
              <div className="flex items-center justify-center gap-6">
                 <div className="h-[1.5px] flex-1 bg-gray-100"></div>
                 <div className="w-16 h-16 rounded-full border-[2px] border-[#4ade80] flex items-center justify-center bg-white shadow-sm">
                    <Lock className="w-6 h-6 text-[#021C33]" />
                 </div>
                 <div className="h-[1.5px] flex-1 bg-gray-100"></div>
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
                      className="pl-12 h-14 bg-gray-50/50 border-gray-100 focus:border-[#4ade80] rounded-2xl font-sans-juricob"
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
                      className="pl-12 pr-12 h-14 bg-gray-50/50 border-gray-100 focus:border-[#4ade80] rounded-2xl font-sans-juricob"
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
                      className="w-4 h-4 rounded border-gray-300 text-[#044D29] focus:ring-[#044D29]"
                    />
                    <label htmlFor="remember" className="text-xs text-slate-500 cursor-pointer font-medium">Recordarme</label>
                  </div>
                  <button
                    type="button"
                    className="text-xs font-bold text-[#044D29] hover:opacity-80"
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
                  className="btn-gradient w-full h-16 text-white rounded-2xl font-bold text-xl flex items-center justify-center gap-4 shadow-xl hover:shadow-emerald-900/20 transition-all hover:scale-[1.01]"
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
                   <div className="relative flex justify-center text-[10px]">
                      <span className="bg-white px-3 text-gray-400 font-bold uppercase tracking-widest">¿No tienes una cuenta?</span>
                   </div>
                </div>

                <Button 
                   variant="outline" 
                   className="w-full h-16 border-gray-100 text-[#021C33] font-bold rounded-2xl flex items-center justify-center gap-2 hover:bg-gray-50 transition-colors"
                >
                   <User className="w-5 h-5 text-gray-400" />
                   Solicitar acceso
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Footer exactly like image */}
          <div className="flex items-center gap-12 text-slate-400 text-sm font-medium mt-16">
             <div className="flex items-center gap-3">
                <Shield className="w-6 h-6 text-[#021C33]" />
                <span className="uppercase tracking-[0.2em] text-[10px] font-bold">Plataforma Segura</span>
             </div>
             <div className="w-[1.5px] h-10 bg-gray-100" />
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
    </div>
  );
}
