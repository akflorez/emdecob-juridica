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
    <section id="inicio" className="bg-gradient-hero pt-40 pb-32 md:pt-52 md:pb-40 lg:pt-56 lg:pb-44 text-white relative overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute inset-0 opacity-[0.02] pointer-events-none" style={{ backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>
      <div className="absolute top-1/4 right-0 w-[500px] h-[500px] rounded-full bg-[#00B873]/10 blur-[100px] pointer-events-none"></div>

      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-10">
        {/* Lado izquierdo */}
        <div className="lg:col-span-6 space-y-6">
          <div className="text-2xl font-bold tracking-wider text-[#00B873] uppercase mb-1">
            JURICOB
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-extrabold tracking-tight leading-[1.1]">
            Gestión judicial inteligente en una sola plataforma
          </h1>
          <p className="text-slate-300 text-lg md:text-xl leading-relaxed max-w-2xl font-light">
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
                className="border border-white/30 hover:border-white hover:bg-white/10 text-white px-6 py-4 rounded-lg text-sm font-semibold bg-transparent transition-all h-auto"
              >
                Solicitar demo
              </Button>
              <Button 
                onClick={() => navigate('/register-company')} 
                className="border border-white/30 hover:border-white hover:bg-white/10 text-white px-6 py-4 rounded-lg text-sm font-semibold bg-transparent transition-all h-auto"
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
                    <div className="w-10 h-10 rounded-full border border-[#00B873]/30 flex items-center justify-center text-[#00B873] bg-transparent group-hover:border-[#00B873] group-hover:bg-[#00B873]/10 transition-all duration-300">
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
          <div className="relative w-full max-w-[720px] transition-all duration-500 hover:scale-[1.02]">
            <img 
              src="/juricob-hero-mockup.png" 
              alt="JURICOB Dashboard and Mobile View Mockup" 
              className="w-full h-auto object-contain drop-shadow-[0_20px_50px_rgba(0,184,115,0.25)]"
            />
          </div>
        </div>
      </div>
    </section>

    {/* 3. SECCIÓN DE CONFIANZA / EQUIPO */}
    <section className="py-32 md:py-40 bg-white">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-20 items-center">
        {/* Lado izquierdo: Foto de equipo */}
        <div className="lg:col-span-7 flex justify-center w-full">
          <div className="relative max-w-[850px] w-full overflow-hidden rounded-3xl shadow-[0_20px_45px_rgba(0,0,0,0.12)] border border-slate-100 bg-slate-50 transition-all duration-500 hover:scale-[1.015]">
            <img 
              src="/juricob-team-three.png" 
              alt="Equipo de EMDECOB" 
              className="w-full h-auto object-cover"
            />
          </div>
        </div>

        {/* Lado derecho: Respaldo */}
        <div className="lg:col-span-5 space-y-8 lg:pl-4">
          <div className="text-sm font-bold text-[#00B873] uppercase tracking-widest">Respaldo por EMDECOB</div>
          <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-[#031827] leading-tight">
            Experiencia, tecnología y compromiso al servicio de la gestión judicial
          </h2>
          <p className="text-slate-600 leading-relaxed font-light text-lg md:text-xl">
            JURICOB nace como una solución desarrollada por <strong>EMDECOB</strong> para optimizar la consulta, vigilancia y administración de procesos judiciales, integrando tecnología, trazabilidad y gestión especializada.
          </p>
        </div>
      </div>
    </section>

    {/* 4. ¿QUÉ ES JURICOB? */}
    <section id="plataforma" className="py-32 md:py-40 bg-slate-50">
      <div className="max-w-6xl mx-auto px-6 text-center space-y-8">
        <div className="text-sm font-bold text-[#00B873] uppercase tracking-widest">¿Qué es JURICOB?</div>
        <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-[#031827] max-w-3xl mx-auto">
          Una plataforma diseñada para la gestión judicial moderna
        </h2>
        <p className="text-slate-600 text-lg md:text-xl leading-relaxed font-light max-w-4xl mx-auto">
            JURICOB centraliza la información judicial de empresas, abogados y equipos de cartera jurídica. Permite consultar procesos de manera masiva, visualizar actuaciones en tiempo real, controlar publicaciones procesales oficiales, delegar tareas internas, monitorear vencimientos y tomar decisiones informadas con bases de datos consolidadas.
          </p>
        </div>
      </section>

    {/* 5. FUNCIONALIDADES PRINCIPALES */}
    <section id="funcionalidades" className="py-32 md:py-40 bg-white">
      <div className="max-w-7xl mx-auto px-6 space-y-20">
        <div className="text-center space-y-6">
          <div className="text-sm font-bold text-[#00B873] uppercase tracking-widest">Funcionalidades Principales</div>
          <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-[#031827]">
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
                <div key={idx} className="p-8 bg-white rounded-3xl border border-slate-100 shadow-sm hover:shadow-xl hover:border-[#00B873]/30 hover:-translate-y-1.5 transition-all duration-300 flex flex-col items-center text-center group cursor-default">
                  <div className="text-[#00B873] flex items-center justify-center mb-6 transition-transform duration-300 group-hover:scale-110">
                    <Icon className="w-10 h-10 stroke-[1.5]" />
                  </div>
                  <h3 className="text-base font-bold text-[#031827] mb-3">{card.t}</h3>
                  <p className="text-slate-500 text-sm font-light leading-relaxed">{card.d}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

    {/* 6. BENEFICIOS */}
    <section id="beneficios" className="py-32 md:py-40 bg-[#031827] text-white">
      <div className="max-w-7xl mx-auto px-6 space-y-20">
        <div className="text-center space-y-6">
          <div className="text-sm font-bold text-[#00B873] uppercase tracking-widest">Beneficios</div>
          <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight">
            Más control, menos riesgo, mejores resultados
          </h2>
        </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-8 text-center">
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
                <div key={idx} className="flex flex-col items-center gap-4 group cursor-default">
                  <div className="w-14 h-14 rounded-full border border-[#00B873]/30 flex items-center justify-center text-[#00B873] bg-transparent group-hover:border-[#00B873] group-hover:bg-[#00B873]/10 transition-all duration-300 group-hover:scale-105">
                    <Icon className="w-6 h-6 stroke-[1.5]" />
                  </div>
                  <span className="text-xs font-medium text-slate-300 group-hover:text-white transition-colors leading-relaxed max-w-[120px]">{b.t}</span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

    {/* 7. PLANES */}
    <section id="planes" className="py-32 md:py-40 bg-white">
      <div className="max-w-7xl mx-auto px-6 space-y-20">
        <div className="text-center space-y-6">
          <div className="text-sm font-bold text-[#00B873] uppercase tracking-widest">Planes flexibles para cada necesidad</div>
          <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-[#031827]">
            Elige el plan que mejor se adapta a tu empresa
          </h2>
        </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Plan Básico */}
            <div className="p-8 bg-white border border-slate-200 rounded-3xl shadow-sm flex flex-col justify-between hover:shadow-xl hover:border-slate-300 hover:-translate-y-1.5 transition-all duration-300 relative">
              <div className="space-y-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full border border-[#00B873]/30 text-[#00B873] flex items-center justify-center shrink-0">
                    <FileText className="w-6 h-6 stroke-[1.5]" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-900">Plan Básico</h3>
                    <p className="text-xs text-slate-400 font-light mt-0.5">Consulta y seguimiento de procesos judiciales.</p>
                  </div>
                </div>
                <div className="h-px bg-slate-100"></div>
                <ul className="space-y-3.5 text-sm text-slate-600">
                  <li className="flex items-center gap-2.5"><Check className="w-4.5 h-4.5 text-[#00B873] shrink-0" /> Consulta de procesos</li>
                  <li className="flex items-center gap-2.5"><Check className="w-4.5 h-4.5 text-[#00B873] shrink-0" /> Actuaciones básicas</li>
                </ul>
              </div>
              <Button onClick={() => scrollToSection('contacto')} className="w-full mt-8 bg-[#031827] hover:bg-[#082A3A] text-white py-3 h-auto font-semibold rounded-lg transition-colors">
                Solicitar cotización
              </Button>
            </div>

            {/* Plan Profesional */}
            <div className="p-8 bg-white border border-slate-200 rounded-3xl shadow-sm flex flex-col justify-between hover:shadow-xl hover:border-slate-300 hover:-translate-y-1.5 transition-all duration-300 relative">
              <div className="space-y-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full border border-[#00B873]/30 text-[#00B873] flex items-center justify-center shrink-0">
                    <Star className="w-6 h-6 stroke-[1.5]" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-900">Plan Profesional</h3>
                    <p className="text-xs text-slate-400 font-light mt-0.5">Publicaciones procesales, alertas, tareas y usuarios por empresa.</p>
                  </div>
                </div>
                <div className="h-px bg-slate-100"></div>
                <ul className="space-y-3.5 text-sm text-slate-600">
                  <li className="flex items-center gap-2.5"><Check className="w-4.5 h-4.5 text-[#00B873] shrink-0" /> Estados electrónicos</li>
                  <li className="flex items-center gap-2.5"><Check className="w-4.5 h-4.5 text-[#00B873] shrink-0" /> Alertas y vencimientos</li>
                  <li className="flex items-center gap-2.5"><Check className="w-4.5 h-4.5 text-[#00B873] shrink-0" /> Gestión de tareas</li>
                  <li className="flex items-center gap-2.5"><Check className="w-4.5 h-4.5 text-[#00B873] shrink-0" /> Usuarios por empresa</li>
                </ul>
              </div>
              <Button onClick={() => scrollToSection('contacto')} className="w-full mt-8 bg-[#031827] hover:bg-[#082A3A] text-white py-3 h-auto font-semibold rounded-lg transition-colors">
                Solicitar cotización
              </Button>
            </div>

            {/* Plan Empresarial */}
            <div className="p-8 bg-white border border-slate-200 rounded-3xl shadow-sm flex flex-col justify-between hover:shadow-xl hover:border-slate-300 hover:-translate-y-1.5 transition-all duration-300 relative">
              <div className="space-y-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full border border-[#00B873]/30 text-[#00B873] flex items-center justify-center shrink-0">
                    <Building2 className="w-6 h-6 stroke-[1.5]" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-900">Plan Empresarial</h3>
                    <p className="text-xs text-slate-400 font-light mt-0.5">Multiempresa, SuperAdmin, facturación, auditoría y analítica.</p>
                  </div>
                </div>
                <div className="h-px bg-slate-100"></div>
                <ul className="space-y-3.5 text-sm text-slate-600">
                  <li className="flex items-center gap-2.5"><Check className="w-4.5 h-4.5 text-[#00B873] shrink-0" /> Todo en Plan Profesional</li>
                  <li className="flex items-center gap-2.5"><Check className="w-4.5 h-4.5 text-[#00B873] shrink-0" /> Administración multiempresa</li>
                  <li className="flex items-center gap-2.5"><Check className="w-4.5 h-4.5 text-[#00B873] shrink-0" /> Panel SuperAdmin SaaS</li>
                  <li className="flex items-center gap-2.5"><Check className="w-4.5 h-4.5 text-[#00B873] shrink-0" /> Facturación y auditoría avanzada</li>
                </ul>
              </div>
              <Button onClick={() => scrollToSection('contacto')} className="w-full mt-8 bg-[#031827] hover:bg-[#082A3A] text-white py-3 h-auto font-semibold rounded-lg transition-colors">
                Solicitar cotización
              </Button>
            </div>
          </div>
        </div>
      </section>

    {/* 8. CONTACTO */}
    <section id="contacto" className="py-32 md:py-40 bg-slate-50 border-t border-slate-100">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
        {/* Lado izquierdo: Formulario */}
        <div className="lg:col-span-6 space-y-8">
          <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-[#031827] leading-tight">
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
                    className="border-slate-200 bg-white text-slate-900 focus-visible:ring-emerald-500"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="c_emp" className="text-xs font-semibold text-slate-500 uppercase">Empresa</Label>
                  <Input 
                    id="c_emp" 
                    value={contactForm.empresa} 
                    onChange={e => setContactForm({...contactForm, empresa: e.target.value})} 
                    className="border-slate-200 bg-white text-slate-900 focus-visible:ring-emerald-500"
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
                    className="border-slate-200 bg-white text-slate-900 focus-visible:ring-emerald-500"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="c_tel" className="text-xs font-semibold text-slate-500 uppercase">Teléfono</Label>
                  <Input 
                    id="c_tel" 
                    value={contactForm.telefono} 
                    onChange={e => setContactForm({...contactForm, telefono: e.target.value})} 
                    className="border-slate-200 bg-white text-slate-900 focus-visible:ring-emerald-500"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="c_msg" className="text-xs font-semibold text-slate-500 uppercase">Mensaje</Label>
                <Textarea 
                  id="c_msg" 
                  value={contactForm.mensaje} 
                  onChange={e => setContactForm({...contactForm, mensaje: e.target.value})} 
                  className="border-slate-200 bg-white text-slate-900 focus-visible:ring-emerald-500"
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
                    <span className="font-semibold text-sm text-slate-700 font-mono">direccionanalitica@emdecob.com</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-emerald-50 text-[#00B873] flex items-center justify-center shrink-0">
                    <Phone className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block font-semibold uppercase">TELÉFONO</span>
                    <span className="font-semibold text-sm text-slate-700 font-mono">314 247 2622</span>
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
              className="max-w-[460px] w-full h-auto object-contain opacity-95"
            />
          </div>
          </div>
        </div>
      </section>

      {/* 9. FOOTER */}
      <footer className="bg-[#031827] text-white py-16 border-t border-slate-800/85">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 border-b border-slate-800/80 pb-12 mb-8">
            {/* Column 1: Logo & Text */}
            <div className="space-y-4">
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
              <p className="text-slate-400 text-sm font-light leading-relaxed max-w-[240px]">
                Conectamos la ley, la información y la gestión judicial en una sola plataforma.
              </p>
            </div>

            {/* Column 2: Enlaces Rápidos */}
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-white uppercase tracking-wider">Enlaces rápidos</h4>
              <ul className="space-y-2.5 text-sm text-slate-400">
                <li><button onClick={() => scrollToSection('inicio')} className="hover:text-white transition-colors">Inicio</button></li>
                <li><button onClick={() => scrollToSection('plataforma')} className="hover:text-white transition-colors">Plataforma</button></li>
                <li><button onClick={() => scrollToSection('funcionalidades')} className="hover:text-white transition-colors">Funcionalidades</button></li>
              </ul>
            </div>

            {/* Column 3: Beneficios */}
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-white uppercase tracking-wider">Beneficios</h4>
              <ul className="space-y-2.5 text-sm text-slate-400">
                <li><button onClick={() => scrollToSection('beneficios')} className="hover:text-white transition-colors">Beneficios</button></li>
                <li><button onClick={() => scrollToSection('planes')} className="hover:text-white transition-colors">Planes</button></li>
                <li><button onClick={() => scrollToSection('contacto')} className="hover:text-white transition-colors">Contacto</button></li>
              </ul>
            </div>

            {/* Column 4: Recursos */}
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-white uppercase tracking-wider">Recursos</h4>
              <ul className="space-y-2.5 text-sm text-slate-400">
                <li><a href="#privacy" className="hover:text-white transition-colors">Política de privacidad</a></li>
                <li><a href="#terms" className="hover:text-white transition-colors">Términos y condiciones</a></li>
                <li><a href="#support" className="hover:text-white transition-colors">Soporte</a></li>
              </ul>
            </div>

            {/* Column 5: Desarrollado por EMDECOB */}
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-white uppercase tracking-wider">Desarrollado por EMDECOB</h4>
              <div className="flex items-center gap-2.5 mt-2">
                <svg className="w-8 h-8" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="20" cy="20" r="18" stroke="#00B873" strokeWidth="2.5" fill="none" />
                  <path d="M14 13C14 12.4477 14.4477 12 15 12H25C25.5523 12 26 12.4477 26 13V15C26 15.5523 25.5523 16 25 16H18V18H23C23.5523 18 24 18.4477 24 19V21C24 21.5523 23.5523 22 23 22H18V24H25C25.5523 24 26 24.4477 26 25V27C26 27.5523 25.5523 28 25 28H15C14.4477 28 14 27.5523 14 27V13Z" fill="white" />
                </svg>
                <span className="font-bold text-white text-base tracking-widest font-sans uppercase">EMDECOB</span>
              </div>
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
