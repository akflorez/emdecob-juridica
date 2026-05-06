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
  CheckCircle2
} from 'lucide-react';

// Import the generated background
// Note: In a real environment, this would be in the assets folder
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
      const msg = 'Por favor ingrese usuario y contraseña';
      setLoginError(msg);
      toast({ title: 'Campos requeridos', description: msg, variant: 'destructive' });
      return;
    }

    setLoginError(null);
    setIsSubmitting(true);
    const result = await login({ username, password });
    setIsSubmitting(false);

    if (result.success) {
      toast({ title: '¡Bienvenido!', description: 'Sesión iniciada correctamente' });
      navigate(from, { replace: true });
    } else {
      const errMsg = result.error || 'Usuario o contraseña incorrectos';
      setLoginError(errMsg);
      toast({ title: 'Error de autenticación', description: errMsg, variant: 'destructive' });
    }
  };

  return (
    <div className="min-h-screen flex font-sans antialiased overflow-hidden">
      {/* Google Font for the Serif logo */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Outfit:wght@300;400;600&display=swap');
        .font-serif-juricob { font-family: 'Cinzel', serif; }
        .font-sans-juricob { font-family: 'Outfit', sans-serif; }
      `}</style>

      {/* Left Panel - Premium Branding */}
      <div className="hidden lg:flex lg:w-[60%] relative">
        {/* Background Image with optimized quality */}
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${LOGIN_BG})` }}
        />
        {/* Gradient Overlay to match the design exactly */}
        <div 
          className="absolute inset-0"
          style={{
            background: 'linear-gradient(90deg, rgba(2, 28, 51, 0.2) 0%, rgba(2, 28, 51, 0.8) 100%)',
          }}
        />

        {/* Content Overlay */}
        <div className="relative z-10 flex flex-col justify-center items-start w-full px-20 text-white space-y-12">
          {/* Logo */}
          <div className="flex flex-col items-center ml-12">
             <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center mb-2">
                <div className="w-8 h-8 border-2 border-[#023136] rounded flex items-center justify-center rotate-45">
                   <div className="w-4 h-4 bg-[#023136] rounded-sm -rotate-45" />
                </div>
             </div>
             <h1 className="text-7xl font-bold font-serif-juricob tracking-wider">JURICOB</h1>
             <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-emerald-400 to-transparent mt-2" />
          </div>

          {/* Features List */}
          <div className="space-y-10 ml-20">
            <div className="flex items-start gap-5 group cursor-default">
              <div className="w-12 h-12 rounded-full border border-white/20 bg-white/5 flex items-center justify-center group-hover:bg-emerald-500/20 transition-all">
                <Shield className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg font-sans-juricob">Seguro y confiable</h3>
                <p className="text-white/60 text-sm max-w-xs font-light leading-relaxed">Protegemos tu información con los más altos estándares.</p>
              </div>
            </div>

            <div className="flex items-start gap-5 group cursor-default">
              <div className="w-12 h-12 rounded-full border border-white/20 bg-white/5 flex items-center justify-center group-hover:bg-emerald-500/20 transition-all">
                <Briefcase className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg font-sans-juricob">Gestión eficiente</h3>
                <p className="text-white/60 text-sm max-w-xs font-light leading-relaxed">Administra tus casos y documentos de manera ágil y centralizada.</p>
              </div>
            </div>

            <div className="flex items-start gap-5 group cursor-default">
              <div className="w-12 h-12 rounded-full border border-white/20 bg-white/5 flex items-center justify-center group-hover:bg-emerald-500/20 transition-all">
                <TrendingUp className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg font-sans-juricob">Información al día</h3>
                <p className="text-white/60 text-sm max-w-xs font-light leading-relaxed">Accede a legislación, jurisprudencia y novedades jurídicas.</p>
              </div>
            </div>
          </div>

          {/* Footer Branding */}
          <div className="absolute bottom-10 left-20 flex items-center gap-10 text-white/50 text-xs">
             <div className="flex items-center gap-2">
                <Shield className="w-4 h-4" />
                <span className="font-sans-juricob uppercase tracking-widest">Plataforma Segura</span>
             </div>
             <div className="w-px h-6 bg-white/20" />
             <div className="flex items-center gap-2">
                <User className="w-4 h-4" />
                <span className="font-sans-juricob uppercase tracking-widest text-left">Soporte Especializado<br/>Asistencia profesional.</span>
             </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Card */}
      <div className="w-full lg:w-[40%] flex items-center justify-center p-8 bg-[#F4F7F9]">
        <div className="w-full max-w-md space-y-8 animate-in fade-in slide-in-from-right-4 duration-700">
          
          <Card className="border-none shadow-[0_20px_50px_rgba(0,0,0,0.1)] rounded-[32px] overflow-hidden bg-white/90 backdrop-blur-md">
            <CardContent className="p-12 space-y-8">
              {/* Login Icon */}
              <div className="flex flex-col items-center space-y-4">
                <div className="w-16 h-16 rounded-full border border-emerald-100 flex items-center justify-center bg-emerald-50/50">
                   <div className="w-12 h-12 rounded-full border border-emerald-200 flex items-center justify-center">
                      <Lock className="w-5 h-5 text-emerald-600" />
                   </div>
                </div>
                <div className="h-px w-32 bg-gray-100" />
              </div>

              <div className="text-center space-y-1">
                 <h2 className="text-2xl font-bold text-slate-800 font-sans-juricob">Iniciar Sesión</h2>
                 <p className="text-slate-400 text-sm">Ingrese sus credenciales para acceder al sistema</p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="username" className="text-sm font-semibold text-slate-700 ml-1">Correo electrónico</Label>
                  <div className="relative">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                      id="username"
                      type="text"
                      placeholder="ejemplo@correo.com"
                      value={username}
                      onChange={(e) => { setUsername(e.target.value); setLoginError(null); }}
                      className="pl-12 h-14 bg-gray-50/50 border-gray-100 focus:border-emerald-500 focus:ring-emerald-500 rounded-xl transition-all"
                      autoComplete="username"
                      autoFocus
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-semibold text-slate-700 ml-1">Contraseña</Label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-12 pr-12 h-14 bg-gray-50/50 border-gray-100 focus:border-emerald-500 focus:ring-emerald-500 rounded-xl transition-all"
                      autoComplete="current-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-emerald-600 transition-colors"
                    >
                      {showPassword ? (
                        <EyeOff className="h-5 w-5" />
                      ) : (
                        <Eye className="h-5 w-5" />
                      )}
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
                    <label htmlFor="remember" className="text-sm text-slate-500 cursor-pointer">Recordarme</label>
                  </div>
                  <button
                    type="button"
                    onClick={() => toast({ title: "Recuperación", description: "Contacte a soporte." })}
                    className="text-sm font-semibold text-emerald-600 hover:text-emerald-700"
                  >
                    ¿Olvidaste tu contraseña?
                  </button>
                </div>

                {/* Error message */}
                {loginError && (
                  <div className="p-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-xs text-center font-medium animate-shake">
                    {loginError}
                  </div>
                )}

                <button 
                  type="submit" 
                  disabled={isSubmitting}
                  className="group relative w-full h-14 bg-gradient-to-r from-[#021C33] to-[#044D29] text-white rounded-xl font-bold text-lg shadow-lg hover:shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-70 disabled:scale-100"
                >
                  <div className="flex items-center justify-center gap-3">
                    {isSubmitting ? (
                      <Loader2 className="h-6 w-6 animate-spin" />
                    ) : (
                      <>
                        <span>Iniciar sesión</span>
                        <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                      </>
                    )}
                  </div>
                </button>

                <div className="relative py-4">
                   <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-100"></div>
                   </div>
                   <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-white px-2 text-slate-400">¿No tienes una cuenta?</span>
                   </div>
                </div>

                <Button 
                   variant="outline" 
                   className="w-full h-14 border-emerald-100 text-slate-600 font-semibold hover:bg-emerald-50 hover:text-emerald-700 rounded-xl flex items-center justify-center gap-2"
                >
                   <User className="w-4 h-4" />
                   Solicitar acceso
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
