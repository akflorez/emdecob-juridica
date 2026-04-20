import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { 
  Scale, 
  Shield, 
  Gavel, 
  Lock, 
  User,
  Eye, 
  EyeOff,
  Loader2,
  Building2
} from 'lucide-react';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  
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
    <div className="min-h-screen flex bg-background">
      {/* Panel izquierdo - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div 
          className="absolute inset-0"
          style={{
            background: 'linear-gradient(135deg, hsl(220 45% 8%) 0%, hsl(220 40% 5%) 50%, hsl(174 83% 15%) 100%)',
          }}
        />
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-20 left-20 w-64 h-64 border border-primary/30 rounded-full" />
          <div className="absolute top-40 left-40 w-96 h-96 border border-primary/20 rounded-full" />
          <div className="absolute bottom-20 right-20 w-48 h-48 border border-primary/40 rounded-full" />
        </div>
        
        <div className="relative z-10 flex flex-col justify-center items-center w-full px-12">
          <div className="flex items-center gap-4 mb-12">
            <div className="w-16 h-16 rounded-xl bg-primary/20 flex items-center justify-center border border-primary/30">
              <Scale className="w-9 h-9 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-foreground">EMDECOB</h1>
              <p className="text-muted-foreground text-sm">Sistema de consulta Jurídica</p>
            </div>
          </div>

          <p className="absolute bottom-8 text-xs text-muted-foreground">
            © 2026 EMDECOB. Todos los derechos reservados.
          </p>
        </div>
      </div>

      {/* Panel derecho - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          {/* Logo móvil */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center border border-primary/30">
              <Scale className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">EMDECOB</h1>
              <p className="text-muted-foreground text-xs">Consulta Jurídica</p>
            </div>
          </div>

          <Card className="border-border/50 shadow-2xl">
            <CardHeader className="space-y-1 pb-6">
              <CardTitle className="text-2xl font-bold text-center">
                Iniciar Sesión
              </CardTitle>
              <CardDescription className="text-center">
                Ingrese sus credenciales para acceder al sistema
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="username" className="text-sm font-medium">
                    Usuario
                  </Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="username"
                      type="text"
                      placeholder="nombre_usuario"
                      value={username}
                      onChange={(e) => { setUsername(e.target.value); setLoginError(null); }}
                      className="pl-10 h-11"
                      autoComplete="username"
                      autoFocus
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium">
                    Contraseña
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-10 pr-10 h-11"
                      autoComplete="current-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Error message inline */}
                {loginError && (
                  <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/30 text-destructive text-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <span>{loginError}</span>
                  </div>
                )}

                <Button 
                  type="submit" 
                  className="w-full h-11 font-semibold"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Verificando...
                    </>
                  ) : (
                    'Ingresar'
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          <p className="text-center text-xs text-muted-foreground">
            ¿Problemas para acceder?{' '}
            <a href="mailto:direccionanalitica@emdecob.com" className="text-primary hover:underline">
              Contacte al administrador
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
