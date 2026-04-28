import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { 
  Scale, 
  Lock, 
  User,
  Mail,
  Eye, 
  EyeOff,
  Loader2,
  ArrowLeft
} from 'lucide-react';
import { apiFetch } from '@/services/api';

export default function RegisterPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [nombre, setNombre] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username || !email || !password || !nombre) {
      toast({ title: 'Campos requeridos', description: 'Por favor complete todos los campos', variant: 'destructive' });
      return;
    }

    if (password !== confirmPassword) {
      toast({ title: 'Contraseñas no coinciden', description: 'Asegúrese de que ambas contraseñas sean iguales', variant: 'destructive' });
      return;
    }

    setError(null);
    setIsSubmitting(true);
    
    try {
      await apiFetch('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, nombre, password })
      }, false);

      toast({ title: 'Registro exitoso', description: 'Ahora puede iniciar sesión con sus credenciales' });
      navigate('/login');
    } catch (err: any) {
      const errMsg = err.message || 'Error al registrar el usuario';
      setError(errMsg);
      toast({ title: 'Error de registro', description: errMsg, variant: 'destructive' });
    } finally {
      setIsSubmitting(false);
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
        <div className="relative z-10 flex flex-col justify-center items-center w-full px-12">
          <div className="flex items-center gap-4 mb-12">
            <div className="w-16 h-16 rounded-xl bg-primary/20 flex items-center justify-center border border-primary/30">
              <Scale className="w-9 h-9 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-foreground">EMDECOB</h1>
              <p className="text-muted-foreground text-sm">Registro de Usuarios</p>
            </div>
          </div>
          <div className="text-center max-w-sm">
            <h2 className="text-xl font-medium text-foreground mb-4">Bienvenido al sistema jurídico de EMDECOB</h2>
            <p className="text-muted-foreground">Cree su cuenta para comenzar a gestionar sus procesos y tareas de manera eficiente y segura.</p>
          </div>
        </div>
      </div>

      {/* Panel derecho - Register Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 overflow-y-auto">
        <div className="w-full max-w-md space-y-8 py-8">
          <Link to="/login" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors mb-4">
            <ArrowLeft className="w-4 h-4" />
            Volver al inicio de sesión
          </Link>

          <Card className="border-border/50 shadow-2xl">
            <CardHeader className="space-y-1 pb-6">
              <CardTitle className="text-2xl font-bold text-center">
                Crear Cuenta
              </CardTitle>
              <CardDescription className="text-center">
                Complete el formulario para registrarse
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="nombre" className="text-sm font-medium">Nombre Completo</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="nombre"
                      placeholder="Juan Pérez"
                      value={nombre}
                      onChange={(e) => setNombre(e.target.value)}
                      className="pl-10 h-10"
                      autoFocus
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="username" className="text-sm font-medium">Usuario</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="username"
                      placeholder="juanp"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="pl-10 h-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium">Correo Electrónico</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="juan@emdecob.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="pl-10 h-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium">Contraseña</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-10 pr-10 h-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-sm font-medium">Confirmar Contraseña</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="confirmPassword"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="pl-10 h-10"
                    />
                  </div>
                </div>

                {error && (
                  <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/30 text-destructive text-sm">
                    {error}
                  </div>
                )}

                <Button 
                  type="submit" 
                  className="w-full h-11 font-semibold mt-4"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Registrando...</>
                  ) : (
                    'Registrarse'
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
          
          <p className="text-center text-sm text-muted-foreground">
            ¿Ya tiene una cuenta?{' '}
            <Link to="/login" className="text-primary font-medium hover:underline">
              Inicie sesión aquí
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
