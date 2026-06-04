import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Lock, Loader2, ArrowRight } from 'lucide-react';
import { resetPassword } from '@/services/api';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { toast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) {
      toast({
        title: "Enlace inválido",
        description: "El enlace de recuperación no es válido o está incompleto.",
        variant: "destructive"
      });
      navigate('/login');
    }
  }, [token, navigate, toast]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password || !confirmPassword) {
      setError('Por favor complete ambos campos');
      return;
    }
    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    
    try {
      const res = await resetPassword({
        token,
        new_password: password,
        confirm_password: confirmPassword
      });
      toast({
        title: "¡Contraseña actualizada!",
        description: res.message,
      });
      navigate('/login');
    } catch (e: any) {
      setError(e.message || 'Error al actualizar contraseña');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#021C33] flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-3xl p-8 shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-[#021C33] uppercase tracking-wider mb-4">Nueva Contraseña</h1>
          <p className="text-sm text-slate-500">Ingrese su nueva contraseña de acceso.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-3">
            <Label className="text-sm font-bold text-slate-700 ml-1">Nueva Contraseña</Label>
            <div className="relative group">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500 transition-colors" />
              <Input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="pl-12 h-14 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-2xl text-base" />
            </div>
          </div>

          <div className="space-y-3">
            <Label className="text-sm font-bold text-slate-700 ml-1">Confirmar Contraseña</Label>
            <div className="relative group">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500 transition-colors" />
              <Input type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="pl-12 h-14 bg-slate-50/50 border-slate-100 focus:border-emerald-400 rounded-2xl text-base" />
            </div>
          </div>

          {error && <p className="text-red-500 text-[11px] text-center font-bold bg-red-50 py-2 rounded-lg">{error}</p>}

          <Button type="submit" disabled={isSubmitting} className="w-full h-14 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl font-bold text-lg flex items-center justify-center gap-2 shadow-xl transition-all">
            {isSubmitting ? <Loader2 className="h-6 w-6 animate-spin" /> : <>Guardar Contraseña <ArrowRight className="h-5 w-5" /></>}
          </Button>
        </form>
      </div>
    </div>
  );
}
