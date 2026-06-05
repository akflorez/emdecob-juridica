import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import {
  Search,
  RefreshCw,
  FileText,
  Bell,
  CheckSquare,
  Building2,
  Users,
  Shield,
  BarChart3,
  Database,
  ArrowRight,
  Mail,
  Phone,
  Check,
  Menu,
  X,
  Globe,
  Star,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  Clock
} from 'lucide-react';

export default function LandingPage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('inicio');

  const [contactForm, setContactForm] = useState({
    nombre: '',
    empresa: '',
    correo: '',
    telefono: '',
    mensaje: ''
  });
  const [sending, setSending] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
      
      const sections = ['inicio', 'plataforma', 'funcionalidades', 'beneficios', 'planes', 'contacto'];
      for (const section of sections) {
        const el = document.getElementById(section);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= 200 && rect.bottom >= 200) {
            setActiveSection(section);
            break;
          }
        }
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleContactSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!contactForm.nombre || !contactForm.correo || !contactForm.mensaje) {
      toast({
        title: "Campos incompletos",
        description: "Por favor complete todos los campos obligatorios.",
        variant: "destructive"
      });
      return;
    }
    setSending(true);
    setTimeout(() => {
      toast({
        title: "¡Solicitud enviada!",
        description: "Nos pondremos en contacto contigo a la brevedad.",
      });
      setContactForm({
        nombre: '',
        empresa: '',
        correo: '',
        telefono: '',
        mensaje: ''
      });
      setSending(false);
    }, 1000);
  };

  const scrollToSection = (id: string) => {
    setMobileMenuOpen(false);
    setActiveSection(id);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="min-h-screen font-sans bg-[#F5F7FA] text-[#111827] overflow-x-hidden selection:bg-[#00B873] selection:text-white">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        .font-sans-juricob { font-family: 'Outfit', sans-serif; }
        
        .bg-gradient-hero {
          background: linear-gradient(135deg, #031827 0%, #061B2E 50%, #082A3A 100%);
        }
      `}</style>

      {/* 1. HEADER / NAVBAR */}
      <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled 
          ? 'bg-[#031827]/90 backdrop-blur-md py-3 shadow-lg border-b border-white/5' 
          : 'bg-transparent py-5'
      }`}>
        <div className="max-w-7xl mx-auto px-6 flex justify-between items-center">
          {/* Logo JURICOB */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => scrollToSection('inicio')}>
            <img 
              src="/juricob-shield.png" 
              alt="JURICOB Shield" 
              className="w-14 h-14 object-contain transition-transform duration-300 hover:scale-105"
            />
            <div className="flex flex-col justify-center">
              <span className="font-sans font-bold text-2xl tracking-widest text-white leading-none">JURICOB</span>
              <span className="text-[10px] tracking-[0.2em] text-[#00B873] font-bold mt-1.5 leading-none uppercase">PORTAL JURÍDICO</span>
            </div>
          </div>

          {/* Nav links (Desktop) */}
          <nav className="hidden md:flex items-center gap-8">
            {[
              { id: 'inicio', label: 'Inicio' },
              { id: 'plataforma', label: 'Plataforma' },
              { id: 'funcionalidades', label: 'Funcionalidades' },
              { id: 'beneficios', label: 'Beneficios' },
              { id: 'planes', label: 'Planes' },
              { id: 'contacto', label: 'Contacto' }
            ].map((link) => (
              <button 
                key={link.id} 
                onClick={() => scrollToSection(link.id)} 
                className={`text-sm font-semibold transition-colors relative py-1 ${
                  activeSection === link.id ? 'text-white' : 'text-slate-300 hover:text-white'
                }`}
              >
                {link.label}
                {activeSection === link.id && (
                  <span className="absolute -bottom-1.5 left-0 w-full h-[2px] bg-[#00B873]"></span>
                )}
              </button>
            ))}
          </nav>

          {/* Action buttons (Desktop) */}
          <div className="hidden md:flex items-center gap-4">
            <Button 
              onClick={() => navigate('/login')} 
              className="border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 bg-transparent text-sm font-semibold px-5 py-2 h-auto rounded-lg transition-all"
            >
              Ingresar
            </Button>
            <Button 
              onClick={() => navigate('/register-company')} 
              className="bg-[#00B873] hover:bg-[#00A86B] text-white text-sm font-semibold px-5 py-2 h-auto rounded-lg shadow-md shadow-[#00B873]/10 transition-all"
            >
              Crear cuenta
            </Button>
          </div>

          {/* Mobile Menu Toggle */}
          <button className="md:hidden text-white" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-[#031827] border-b border-[#082A3A] px-6 py-6 space-y-4 animate-in slide-in-from-top-5 duration-200">
            <nav className="flex flex-col gap-3">
              {[
                { id: 'inicio', label: 'Inicio' },
                { id: 'plataforma', label: 'Plataforma' },
                { id: 'funcionalidades', label: 'Funcionalidades' },
                { id: 'beneficios', label: 'Beneficios' },
                { id: 'planes', label: 'Planes' },
                { id: 'contacto', label: 'Contacto' }
              ].map((link) => (
                <button 
                  key={link.id}
                  onClick={() => scrollToSection(link.id)} 
                  className={`text-left text-sm font-semibold py-1 ${
                    activeSection === link.id ? 'text-[#00B873]' : 'text-slate-300 hover:text-white'
                  }`}
                >
                  {link.label}
                </button>
              ))}
            </nav>
            <div className="flex flex-col gap-2 pt-4 border-t border-slate-800">
              <Button 
                onClick={() => navigate('/login')} 
                className="border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 bg-transparent text-sm font-semibold w-full justify-center py-2.5 h-auto rounded-lg"
              >
                Ingresar
              </Button>
              <Button 
                onClick={() => navigate('/register-company')} 
                className="bg-[#00B873] hover:bg-[#00A86B] text-white text-sm font-semibold w-full justify-center py-2.5 h-auto rounded-lg"
              >
                Crear cuenta
              </Button>
            </div>
          </div>
        )}
      </header>

      {/* 2. HERO PRINCIPAL */}
      <section id="inicio" className="bg-gradient-hero pt-36 pb-28 md:pt-48 md:pb-36 text-white relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute inset-0 opacity-[0.02] pointer-events-none" style={{ backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>
        <div className="absolute top-1/4 right-0 w-[500px] h-[500px] rounded-full bg-[#00B873]/10 blur-[100px] pointer-events-none"></div>

        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-10">
          {/* Lado izquierdo */}
          <div className="lg:col-span-6 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#00B873]/10 border border-[#00B873]/25 text-xs font-semibold text-[#00B873] mb-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00B873] animate-pulse"></span>
              Plataforma Premium de Gestión Judicial
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-5xl font-bold tracking-tight leading-tight">
              Gestión judicial inteligente en una sola plataforma
            </h1>
            <p className="text-slate-300 text-lg leading-relaxed max-w-xl font-light">
              Consulta, monitorea y administra procesos judiciales con actuaciones, estados electrónicos, publicaciones procesales, alertas, tareas y control multi-empresa desde una solución segura en la nube.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 pt-2">
              <Button 
                onClick={() => navigate('/login')} 
                className="bg-[#00B873] hover:bg-[#00A86B] text-white px-6 py-4 rounded-lg text-sm font-semibold shadow-lg shadow-[#00B873]/15 flex items-center justify-center gap-2 group transition-all h-auto"
              >
                Ingresar a la plataforma
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button 
                onClick={() => scrollToSection('contacto')} 
                className="border border-slate-700 hover:border-slate-500 text-white px-6 py-4 rounded-lg text-sm font-semibold bg-transparent transition-all h-auto"
              >
                Solicitar demo
              </Button>
              <Button 
                onClick={() => navigate('/register-company')} 
                className="border border-slate-700 hover:border-slate-500 text-white px-6 py-4 rounded-lg text-sm font-semibold bg-transparent transition-all h-auto"
              >
                Crear cuenta
              </Button>
            </div>

            {/* Row of 4 Badges */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 pt-10 border-t border-slate-800/60 max-w-xl">
              {[
                { t: "Información centralizada", icon: Database },
                { t: "Seguridad de datos", icon: Shield },
                { t: "Acceso desde cualquier lugar", icon: Globe },
                { t: "Alertas oportunas", icon: Bell }
              ].map((item, idx) => {
                const Icon = item.icon;
                return (
                  <div key={idx} className="flex flex-col gap-2 items-center sm:items-start text-center sm:text-left group">
                    <div className="w-10 h-10 rounded-full border border-slate-800 flex items-center justify-center text-[#00B873] bg-[#061B2E]/50 group-hover:border-[#00B873]/50 transition-colors">
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-semibold text-slate-300 max-w-[120px]">{item.t}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Lado derecho: Image Mockup */}
          <div className="lg:col-span-6 flex justify-center lg:justify-end w-full">
            <div className="relative w-full max-w-[650px] rounded-3xl overflow-hidden shadow-[0_20px_50px_rgba(0,184,115,0.12)] border border-slate-850 transition-all duration-500 hover:scale-[1.02] hover:shadow-[0_20px_50px_rgba(0,184,115,0.22)]">
              <img 
                src="/juricob-hero-mockup.png" 
                alt="JURICOB Dashboard and Mobile View Mockup" 
                className="w-full h-auto object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* 3. SECCIÓN DE CONFIANZA / EQUIPO */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
          {/* Lado izquierdo: Foto de equipo */}
          <div className="lg:col-span-6 flex justify-center w-full">
            <div className="relative max-w-[650px] w-full overflow-hidden rounded-3xl shadow-[0_15px_35px_rgba(0,0,0,0.12)] border border-slate-100 bg-slate-50 transition-all duration-500 hover:scale-[1.015]">
              <img 
                src="/juricob-team-premium.png" 
                alt="Equipo de EMDECOB" 
                className="w-full h-auto object-cover aspect-square"
              />
            </div>
          </div>

          {/* Lado derecho: Respaldo */}
          <div className="lg:col-span-6 space-y-6 lg:pl-4">
            <div className="text-sm font-bold text-[#00B873] uppercase tracking-widest">Respaldo por EMDECOB</div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#031827] leading-tight">
              Experiencia, tecnología y compromiso al servicio de la gestión judicial
            </h2>
            <p className="text-slate-600 leading-relaxed font-light text-lg">
              JURICOB nace como una solución desarrollada por <strong>EMDECOB</strong> para optimizar la consulta, vigilancia y administración de procesos judiciales, integrando tecnología, trazabilidad y gestión especializada.
            </p>
          </div>
        </div>
      </section>

      {/* 4. ¿QUÉ ES JURICOB? */}
      <section id="plataforma" className="py-20 bg-slate-50">
        <div className="max-w-5xl mx-auto px-6 text-center space-y-6">
          <div className="text-sm font-bold text-[#00B873] uppercase tracking-widest">¿Qué es JURICOB?</div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#031827] max-w-2xl mx-auto">
            Una plataforma diseñada para la gestión judicial moderna
          </h2>
          <p className="text-slate-600 text-lg leading-relaxed font-light max-w-3xl mx-auto">
            JURICOB centraliza la información judicial de empresas, abogados y equipos de cartera jurídica. Permite consultar procesos de manera masiva, visualizar actuaciones en tiempo real, controlar publicaciones procesales oficiales, delegar tareas internas, monitorear vencimientos y tomar decisiones informadas con bases de datos consolidadas.
          </p>
        </div>
      </section>

      {/* 5. FUNCIONALIDADES PRINCIPALES */}
      <section id="funcionalidades" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6 space-y-16">
          <div className="text-center space-y-4">
            <div className="text-sm font-bold text-[#00B873] uppercase tracking-widest">Funcionalidades Principales</div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#031827]">
              Todo lo que tu equipo jurídico necesita en un solo lugar
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
            {[
              {
                t: "Consulta de procesos",
                d: "Consulta rápida y precisa de procesos judiciales en múltiples fuentes.",
                icon: Search
              },
              {
                t: "Sincronización de actuaciones",
                d: "Actualización automática de actuaciones y movimientos del proceso.",
                icon: RefreshCw
              },
              {
                t: "Estados electrónicos",
                d: "Publicaciones procesales, traslados, autos y documentos asociados al radicado.",
                icon: FileText
              },
              {
                t: "Alertas y vencimientos",
                d: "Notificaciones de términos, audiencias, vencimientos y novedades importantes.",
                icon: Bell
              },
              {
                t: "Gestión de tareas",
                d: "Organiza tareas internas, responsables y seguimiento de actividades.",
                icon: CheckSquare
              },
              {
                t: "Administración multiempresa",
                d: "Gestiona múltiples empresas desde un panel centralizado y seguro.",
                icon: Building2
              },
              {
                t: "Usuarios y permisos",
                d: "Control de roles, permisos y alcances por empresa y por usuario.",
                icon: Users
              },
              {
                t: "Panel SuperAdmin SaaS",
                d: "Administra empresas, usuarios, consumos, estados de pago y configuraciones.",
                icon: Shield
              },
              {
                t: "Facturación por radicados",
                d: "Control de consumo por radicados activos con simulador de tarifas.",
                icon: BarChart3
              },
              {
                t: "Auditoría y trazabilidad",
                d: "Registro detallado de acciones, consumos, estados de pago y trazabilidad completa.",
                icon: Database
              }
            ].map((card, idx) => {
              const Icon = card.icon;
              return (
                <div key={idx} className="p-6 bg-white rounded-3xl border border-slate-100 shadow-sm hover:shadow-xl hover:border-[#00B873]/30 hover:-translate-y-1.5 transition-all duration-300 flex flex-col items-center text-center group cursor-default">
                  <div className="w-14 h-14 rounded-2xl bg-emerald-50 text-[#00B873] flex items-center justify-center mb-5 group-hover:bg-[#00B873] group-hover:text-white transition-all duration-300 group-hover:scale-105">
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-sm font-bold text-[#031827] mb-2">{card.t}</h3>
                  <p className="text-slate-500 text-xs font-light leading-normal">{card.d}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 6. BENEFICIOS */}
      <section id="beneficios" className="py-24 bg-[#031827] text-white">
        <div className="max-w-7xl mx-auto px-6 space-y-16">
          <div className="text-center space-y-4">
            <div className="text-sm font-bold text-[#00B873] uppercase tracking-widest">Beneficios</div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
              Más control, menos riesgo, mejores resultados
            </h2>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-6 text-center">
            {[
              { t: "Información centralizada", icon: Database },
              { t: "Reducción de falsos positivos", icon: ShieldCheck },
              { t: "Mayor trazabilidad", icon: ChevronRight },
              { t: "Ahorro de tiempo operativo", icon: Clock },
              { t: "Seguridad de la información", icon: Shield },
              { t: "Acceso desde cualquier lugar", icon: Globe },
              { t: "Alertas oportunas", icon: Bell },
              { t: "Mejor seguimiento jurídico", icon: CheckCircle2 }
            ].map((b, idx) => {
              const Icon = b.icon;
              return (
                <div key={idx} className="flex flex-col items-center gap-3 p-5 bg-white/5 rounded-2xl border border-white/10 hover:border-[#00B873]/50 hover:bg-white/10 transition-all duration-300 hover:-translate-y-1">
                  <div className="w-12 h-12 rounded-full border border-white/10 flex items-center justify-center text-[#00B873] bg-white/5">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-semibold text-slate-200">{b.t}</span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 7. PLANES */}
      <section id="planes" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6 space-y-16">
          <div className="text-center space-y-4">
            <div className="text-sm font-bold text-[#00B873] uppercase tracking-widest">Planes flexibles para cada necesidad</div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#031827]">
              Elige el plan que mejor se adapta a tu empresa
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">
            {/* Plan Básico */}
            <div className="p-8 bg-white border border-slate-100 rounded-3xl shadow-sm flex flex-col justify-between hover:shadow-xl hover:border-slate-200 hover:-translate-y-1 transition-all duration-300 relative">
              <div className="space-y-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-emerald-50 text-[#00B873] flex items-center justify-center">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-800">Plan Básico</h3>
                    <p className="text-xs text-slate-400 font-light">Consulta y seguimiento de procesos judiciales.</p>
                  </div>
                </div>
                <div className="h-px bg-slate-100"></div>
                <ul className="space-y-3 text-sm text-slate-600">
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Consulta de procesos</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Búsqueda de radicados</li>
                </ul>
              </div>
              <Button onClick={() => scrollToSection('contacto')} className="w-full mt-8 bg-[#031827] hover:bg-[#082A3A] text-white py-3 h-auto font-semibold rounded-lg">
                Solicitar cotización
              </Button>
            </div>

            {/* Plan Premium */}
            <div className="p-8 bg-[#061B2E] border-2 border-[#00B873] rounded-3xl shadow-[0_15px_35px_rgba(0,184,115,0.15)] flex flex-col justify-between text-white hover:-translate-y-1 transition-all duration-300 relative">
              <div className="absolute top-0 right-0 bg-[#00B873] text-white text-[9px] font-bold tracking-widest px-4 py-1.5 uppercase rounded-bl-2xl shadow-md">Popular</div>
              <div className="space-y-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-white/10 text-[#00B873] flex items-center justify-center">
                    <Star className="w-5 h-5 fill-[#00B873]" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">Plan Premium</h3>
                    <p className="text-xs text-slate-300 font-light">Publicaciones procesales, actuaciones avanzadas, alertas, tareas y usuarios por empresa.</p>
                  </div>
                </div>
                <div className="h-px bg-slate-800"></div>
                <ul className="space-y-3 text-sm text-slate-300">
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Consulta de procesos</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Búsqueda de radicados</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Gestión de tareas</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Alertas y vencimientos</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Usuarios por empresa</li>
                </ul>
              </div>
              <Button onClick={() => scrollToSection('contacto')} className="w-full mt-8 bg-[#00B873] hover:bg-[#00A86B] text-white py-3 h-auto font-semibold rounded-lg shadow-md shadow-[#00B873]/15">
                Solicitar cotización
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* 8. CONTACTO */}
      <section id="contacto" className="py-20 bg-slate-50 border-t border-slate-100">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Lado izquierdo: Formulario */}
          <div className="lg:col-span-6 space-y-6">
            <h2 className="text-3xl font-bold tracking-tight text-[#031827]">
              ¿Listo para transformar tu gestión judicial?
            </h2>
            <form onSubmit={handleContactSubmit} className="bg-white p-8 rounded-2xl border border-slate-100 shadow-sm space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="c_name" className="text-xs font-semibold text-slate-500 uppercase">Nombre completo</Label>
                  <Input 
                    id="c_name" 
                    value={contactForm.nombre} 
                    onChange={e => setContactForm({...contactForm, nombre: e.target.value})} 
                    className="border-slate-200"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="c_emp" className="text-xs font-semibold text-slate-500 uppercase">Empresa</Label>
                  <Input 
                    id="c_emp" 
                    value={contactForm.empresa} 
                    onChange={e => setContactForm({...contactForm, empresa: e.target.value})} 
                    className="border-slate-200"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="c_mail" className="text-xs font-semibold text-slate-500 uppercase">Correo electrónico</Label>
                  <Input 
                    id="c_mail" 
                    type="email"
                    value={contactForm.correo} 
                    onChange={e => setContactForm({...contactForm, correo: e.target.value})} 
                    className="border-slate-200"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="c_tel" className="text-xs font-semibold text-slate-500 uppercase">Teléfono</Label>
                  <Input 
                    id="c_tel" 
                    value={contactForm.telefono} 
                    onChange={e => setContactForm({...contactForm, telefono: e.target.value})} 
                    className="border-slate-200"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="c_msg" className="text-xs font-semibold text-slate-500 uppercase">Mensaje</Label>
                <Textarea 
                  id="c_msg" 
                  value={contactForm.mensaje} 
                  onChange={e => setContactForm({...contactForm, mensaje: e.target.value})} 
                  className="border-slate-200"
                  rows={4}
                  required
                />
              </div>

              <Button type="submit" disabled={sending} className="w-full bg-[#00B873] hover:bg-[#00A86B] text-white font-semibold py-3 h-auto rounded-lg shadow-md shadow-[#00B873]/10">
                {sending ? 'Enviando...' : 'Solicitar información'}
              </Button>
            </form>
          </div>

          {/* Lado derecho: Contacto e imagen */}
          <div className="lg:col-span-6 space-y-8 h-full flex flex-col justify-between relative min-h-[400px]">
            {/* Contact Details */}
            <div className="space-y-6 relative z-10 pt-6">
              <h3 className="text-xl font-bold text-[#031827]">Contáctanos</h3>
              
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-emerald-50 text-[#00B873] flex items-center justify-center shrink-0">
                    <Mail className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block font-semibold uppercase">CORREO ELECTRÓNICO</span>
                    <span className="font-semibold text-sm text-slate-700 font-mono">direccionejecutiva@emdecob.com</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-emerald-50 text-[#00B873] flex items-center justify-center shrink-0">
                    <Phone className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block font-semibold uppercase">TELÉFONO</span>
                    <span className="font-semibold text-sm text-slate-700 font-mono">314 892 3929</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-emerald-50 text-[#00B873] flex items-center justify-center shrink-0">
                    <Globe className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block font-semibold uppercase">UBICACIÓN</span>
                    <span className="font-semibold text-sm text-slate-700 font-mono">Colombia</span>
                  </div>
                </div>
              </div>
              <p className="text-xs text-slate-400 font-light mt-4">
                Estamos listos para ayudarte a llevar tu gestión judicial al siguiente nivel.
              </p>
            </div>

            {/* Background Image of Scale */}
            <div className="w-full h-auto mt-6 flex justify-end">
              <img 
                src="/juricob-contact-scale.png" 
                alt="Balanza de la justicia" 
                className="max-w-[380px] h-auto object-contain opacity-90"
              />
            </div>
          </div>
        </div>
      </section>

      {/* 9. FOOTER */}
      <footer className="bg-[#031827] text-white py-12 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-8 border-b border-slate-800 pb-8 mb-8">
            <div className="flex items-center gap-3">
              <img 
                src="/juricob-shield.png" 
                alt="JURICOB Shield Logo" 
                className="w-12 h-12 object-contain"
              />
              <div className="flex flex-col">
                <span className="font-sans text-lg tracking-widest font-bold leading-none">JURICOB</span>
                <span className="text-[8px] text-[#00B873] uppercase tracking-widest block mt-1 leading-none font-bold">PORTAL JURÍDICO</span>
              </div>
            </div>

            <div className="flex flex-wrap justify-center gap-6 text-sm text-slate-400">
              <button onClick={() => scrollToSection('inicio')} className="hover:text-white transition-colors">Inicio</button>
              <button onClick={() => scrollToSection('plataforma')} className="hover:text-white transition-colors">Plataforma</button>
              <button onClick={() => scrollToSection('funcionalidades')} className="hover:text-white transition-colors">Funcionalidades</button>
              <button onClick={() => scrollToSection('beneficios')} className="hover:text-white transition-colors">Beneficios</button>
              <button onClick={() => scrollToSection('planes')} className="hover:text-white transition-colors">Planes</button>
              <button onClick={() => scrollToSection('contacto')} className="hover:text-white transition-colors">Contacto</button>
            </div>
          </div>

          <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-slate-500 font-mono">
            <div>
              © {new Date().getFullYear()} EMDECOB. Todos los derechos reservados.
            </div>
            <div className="flex items-center gap-1">
              Desarrollado por <span className="font-bold text-[#00B873]">EMDECOB</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
