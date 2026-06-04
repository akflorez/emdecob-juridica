import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { 
  Scale, 
  Building2, 
  Users, 
  CheckCircle2, 
  FileText, 
  Bell, 
  Clock, 
  DollarSign, 
  Database, 
  Shield, 
  ArrowRight, 
  Mail, 
  Phone, 
  Lock, 
  Check, 
  Sparkles,
  HelpCircle,
  ShieldCheck,
  ChevronRight,
  Menu,
  X,
  RefreshCw
} from 'lucide-react';

export default function LandingPage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  // Scroll state for Header styling
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Contact Form State
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
      if (window.scrollY > 50) {
        setScrolled(true);
      } else {
        setScrolled(false);
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
    // Simulate sending email
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
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="min-h-screen font-sans bg-[#F5F7FA] text-[#111827] overflow-x-hidden selection:bg-[#00B873] selection:text-white">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Outfit:wght@300;400;500;600;700&display=swap');
        .font-serif-juricob { font-family: 'Cinzel', serif; }
        .font-sans-juricob { font-family: 'Outfit', sans-serif; }
        
        .bg-gradient-hero {
          background: linear-gradient(135deg, #031827 0%, #061B2E 50%, #082A3A 100%);
        }
        .text-gradient-emerald {
          background: linear-gradient(90deg, #00A86B 0%, #00B873 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        .border-emerald-glow {
          box-shadow: 0 0 15px rgba(0, 184, 115, 0.15);
        }
      `}</style>

      {/* 1. HEADER / NAVBAR */}
      <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled 
          ? 'bg-[#061B2E]/95 backdrop-blur-md py-3 shadow-lg border-b border-[#082A3A]' 
          : 'bg-transparent py-5'
      }`}>
        <div className="max-w-7xl mx-auto px-6 flex justify-between items-center">
          {/* Logo JURICOB */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => scrollToSection('inicio')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00A86B] to-[#00B873] flex items-center justify-center shadow-md shadow-[#00A86B]/20">
              <Scale className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-serif-juricob text-xl font-bold tracking-widest text-white block">JURICOB</span>
              <span className="text-[9px] uppercase tracking-[0.25em] text-slate-400 font-bold block leading-none">by EMDECOB</span>
            </div>
          </div>

          {/* Nav links (Desktop) */}
          <nav className="hidden md:flex items-center gap-8">
            <button onClick={() => scrollToSection('inicio')} className="text-sm font-medium text-slate-300 hover:text-white transition-colors">Inicio</button>
            <button onClick={() => scrollToSection('plataforma')} className="text-sm font-medium text-slate-300 hover:text-white transition-colors">Plataforma</button>
            <button onClick={() => scrollToSection('funcionalidades')} className="text-sm font-medium text-slate-300 hover:text-white transition-colors">Funcionalidades</button>
            <button onClick={() => scrollToSection('beneficios')} className="text-sm font-medium text-slate-300 hover:text-white transition-colors">Beneficios</button>
            <button onClick={() => scrollToSection('planes')} className="text-sm font-medium text-slate-300 hover:text-white transition-colors">Planes</button>
            <button onClick={() => scrollToSection('contacto')} className="text-sm font-medium text-slate-300 hover:text-white transition-colors">Contacto</button>
          </nav>

          {/* Action buttons (Desktop) */}
          <div className="hidden md:flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate('/login')} className="text-slate-300 hover:text-white hover:bg-[#082A3A]/50 font-semibold text-sm">
              Ingresar
            </Button>
            <Button onClick={() => navigate('/register-company')} className="bg-[#00B873] hover:bg-[#00A86B] text-white font-semibold text-sm shadow-md shadow-[#00B873]/10">
              Crear cuenta
            </Button>
            <Button variant="outline" onClick={() => scrollToSection('contacto')} className="border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 font-semibold text-sm bg-transparent">
              Solicitar Demo
            </Button>
          </div>

          {/* Mobile Menu Toggle */}
          <button className="md:hidden text-white" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-[#061B2E] border-b border-[#082A3A] px-6 py-6 space-y-4 animate-in slide-in-from-top-5 duration-200">
            <nav className="flex flex-col gap-3">
              <button onClick={() => scrollToSection('inicio')} className="text-left text-sm font-medium text-slate-300 hover:text-white py-1">Inicio</button>
              <button onClick={() => scrollToSection('plataforma')} className="text-left text-sm font-medium text-slate-300 hover:text-white py-1">Plataforma</button>
              <button onClick={() => scrollToSection('funcionalidades')} className="text-left text-sm font-medium text-slate-300 hover:text-white py-1">Funcionalidades</button>
              <button onClick={() => scrollToSection('beneficios')} className="text-left text-sm font-medium text-slate-300 hover:text-white py-1">Beneficios</button>
              <button onClick={() => scrollToSection('planes')} className="text-left text-sm font-medium text-slate-300 hover:text-white py-1">Planes</button>
              <button onClick={() => scrollToSection('contacto')} className="text-left text-sm font-medium text-slate-300 hover:text-white py-1">Contacto</button>
            </nav>
            <div className="flex flex-col gap-2 pt-4 border-t border-slate-800">
              <Button variant="ghost" onClick={() => navigate('/login')} className="text-slate-300 justify-start px-0 hover:text-white">
                Ingresar
              </Button>
              <Button onClick={() => navigate('/register-company')} className="bg-[#00B873] hover:bg-[#00A86B] text-white w-full justify-center">
                Crear cuenta
              </Button>
              <Button variant="outline" onClick={() => scrollToSection('contacto')} className="border-slate-700 text-slate-300 w-full justify-center bg-transparent">
                Solicitar Demo
              </Button>
            </div>
          </div>
        )}
      </header>

      {/* 2. HERO PRINCIPAL */}
      <section id="inicio" className="bg-gradient-hero pt-32 pb-24 md:pt-40 md:pb-32 text-white relative overflow-hidden">
        {/* Decorative Grid Patterns */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-[#00B873]/15 blur-3xl pointer-events-none"></div>

        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center relative z-10">
          {/* Lado izquierdo */}
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#00B873]/10 border border-[#00B873]/20 text-xs font-semibold text-[#00B873]">
              <Sparkles className="w-3.5 h-3.5" />
              SaaS Judicial Premium para Empresas
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-tight">
              <span className="font-serif-juricob text-5xl sm:text-6xl lg:text-7xl block mb-2 tracking-widest text-[#00B873]">JURICOB</span>
              Gestión judicial inteligente en una sola plataforma
            </h1>
            <p className="text-slate-300 text-lg leading-relaxed max-w-xl font-light">
              Consulta, monitorea y administra procesos judiciales con actuaciones, estados electrónicos, publicaciones procesales, alertas, tareas y control de múltiples empresas desde una solución segura y moderna en la nube.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <Button onClick={() => navigate('/login')} className="bg-[#00B873] hover:bg-[#00A86B] text-white px-8 py-6 rounded-xl text-base font-semibold shadow-lg shadow-[#00B873]/20 flex items-center justify-center gap-2 group transition-all">
                Ingresar a la plataforma
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button onClick={() => navigate('/register-company')} variant="outline" className="border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 bg-transparent px-8 py-6 rounded-xl text-base font-semibold">
                Crear cuenta
              </Button>
              <Button onClick={() => scrollToSection('contacto')} variant="ghost" className="text-slate-300 hover:text-white font-semibold text-base py-6 hover:bg-[#082A3A]/45">
                Solicitar demo
              </Button>
            </div>
          </div>

          {/* Lado derecho: Composición Visual */}
          <div className="relative flex justify-center lg:justify-end animate-in fade-in zoom-in-95 duration-1000">
            {/* Main Mockup container */}
            <div className="relative w-full max-w-[500px] border border-slate-800 rounded-3xl overflow-hidden bg-[#061B2E] shadow-2xl border-emerald-glow">
              <div className="flex items-center gap-2 bg-[#031827] px-4 py-3 border-b border-slate-800">
                <div className="w-2.5 h-2.5 rounded-full bg-rose-500"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
                <span className="text-[10px] text-slate-500 ml-4 font-mono">https://plataforma.juricob.com/dashboard</span>
              </div>
              <img 
                src="/juricob-dashboard.png" 
                alt="JURICOB SaaS Dashboard View" 
                className="w-full h-auto object-cover opacity-90"
              />
            </div>

            {/* Overlapping Floating Indicators */}
            <div className="absolute -bottom-6 -left-6 bg-white text-slate-900 px-5 py-4 rounded-2xl shadow-xl flex items-center gap-3 border border-slate-100 animate-bounce duration-5000">
              <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xs text-slate-400 block font-bold">MONITOREO ACTIVO</span>
                <span className="text-base font-bold text-[#031827] font-mono">100% Automatizado</span>
              </div>
            </div>

            <div className="absolute -top-6 right-6 bg-[#031827] text-white px-5 py-3 rounded-2xl shadow-xl flex items-center gap-3 border border-slate-800">
              <div className="w-2 h-2 rounded-full bg-[#00B873] animate-pulse"></div>
              <div>
                <span className="text-xs text-slate-400 block">Radicados Vigilados</span>
                <span className="text-sm font-bold text-white font-mono">2,934 Activos</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. SECCIÓN DE CONFIANZA / EQUIPO */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Lado izquierdo: Foto corporativa redondeada y elegante */}
          <div className="flex justify-center">
            <div className="relative group max-w-md overflow-hidden rounded-2xl shadow-lg border border-slate-100 bg-slate-50">
              <img 
                src="/juricob-equipo.png" 
                alt="Equipo Corporativo de EMDECOB" 
                className="w-full h-auto object-cover transition-transform duration-700 group-hover:scale-102"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-6">
                <p className="text-white text-xs font-semibold uppercase tracking-widest">Respaldo profesional interdisciplinario</p>
              </div>
            </div>
          </div>

          {/* Lado derecho: Mensaje de confianza */}
          <div className="space-y-6">
            <div className="text-xs font-bold text-[#00B873] uppercase tracking-widest">Respaldo e Identidad</div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#031827]">
              Respaldado por un equipo jurídico, tecnológico y operativo
            </h2>
            <p className="text-slate-600 leading-relaxed font-light">
              JURICOB nace como una solución integral desarrollada por <strong>EMDECOB</strong> para optimizar la consulta, vigilancia y administración de procesos judiciales, integrando tecnología, trazabilidad y gestión especializada.
            </p>
            <div className="grid grid-cols-2 gap-6 pt-4 border-t border-slate-100">
              <div>
                <span className="text-3xl font-bold text-[#031827] block font-mono">EMDECOB</span>
                <span className="text-xs text-slate-500 uppercase tracking-wider block mt-1">Casa Desarrolladora</span>
              </div>
              <div>
                <span className="text-3xl font-bold text-[#00B873] block font-mono">100%</span>
                <span className="text-xs text-slate-500 uppercase tracking-wider block mt-1">Seguro y en la nube</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. QUÉ ES JURICOB */}
      <section id="plataforma" className="py-20 bg-slate-50">
        <div className="max-w-5xl mx-auto px-6 text-center space-y-6">
          <div className="text-xs font-bold text-[#00B873] uppercase tracking-widest">¿Qué es JURICOB?</div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#031827] max-w-2xl mx-auto">
            Una plataforma diseñada para la gestión judicial moderna
          </h2>
          <p className="text-slate-600 text-lg leading-relaxed font-light max-w-3xl mx-auto">
            JURICOB centraliza la información judicial de empresas, abogados y equipos de cartera jurídica. Permite consultar procesos de manera masiva, visualizar actualizaciones en tiempo real, controlar publicaciones procesales oficiales, delegar tareas internas, monitorear vencimientos y tomar decisiones informadas con bases de datos consolidadas.
          </p>
        </div>
      </section>

      {/* 5. FUNCIONALIDADES PRINCIPALES */}
      <section id="funcionalidades" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6 space-y-12">
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold tracking-tight text-[#031827]">Funcionalidades Principales</h2>
            <p className="text-slate-500 font-light max-w-xl mx-auto">
              Todo lo necesario para el control y supervisión automatizada de causas jurídicas.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Card 1 */}
            <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow group">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-5 group-hover:bg-[#00B873] group-hover:text-white transition-colors">
                <Scale className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#031827] mb-2">Consulta de procesos judiciales</h3>
              <p className="text-slate-500 text-sm font-light">Acceso rápido e indexado a la base de datos nacional de radicados y procesos jurídicos.</p>
            </div>
            {/* Card 2 */}
            <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow group">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-5 group-hover:bg-[#00B873] group-hover:text-white transition-colors">
                <RefreshCw className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#031827] mb-2">Sincronización de actuaciones</h3>
              <p className="text-slate-500 text-sm font-light">Descarga y actualización en tiempo real de providencias y movimientos en despachos.</p>
            </div>
            {/* Card 3 */}
            <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow group">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-5 group-hover:bg-[#00B873] group-hover:text-white transition-colors">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#031827] mb-2">Estados electrónicos y publicaciones</h3>
              <p className="text-slate-500 text-sm font-light">Control y visualización de notificaciones procesales directamente asociadas al expediente.</p>
            </div>
            {/* Card 4 */}
            <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow group">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-5 group-hover:bg-[#00B873] group-hover:text-white transition-colors">
                <Bell className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#031827] mb-2">Alertas y vencimientos</h3>
              <p className="text-slate-500 text-sm font-light">Notificaciones preventivas sobre fechas críticas de traslados y audiencias.</p>
            </div>
            {/* Card 5 */}
            <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow group">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-5 group-hover:bg-[#00B873] group-hover:text-white transition-colors">
                <Clock className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#031827] mb-2">Gestión de tareas internas</h3>
              <p className="text-slate-500 text-sm font-light">Asignación, seguimiento y control de pendientes judiciales para abogados y auxiliares.</p>
            </div>
            {/* Card 6 */}
            <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow group">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-5 group-hover:bg-[#00B873] group-hover:text-white transition-colors">
                <Building2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#031827] mb-2">Administración de empresas</h3>
              <p className="text-slate-500 text-sm font-light">Control independiente y aislado de los portafolios y expedientes de múltiples empresas.</p>
            </div>
            {/* Card 7 */}
            <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow group">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-5 group-hover:bg-[#00B873] group-hover:text-white transition-colors">
                <Users className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#031827] mb-2">Usuarios y permisos</h3>
              <p className="text-slate-500 text-sm font-light">Roles personalizables que limitan el acceso a la información confidencial según alcances específicos.</p>
            </div>
            {/* Card 8 */}
            <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow group">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-5 group-hover:bg-[#00B873] group-hover:text-white transition-colors">
                <Lock className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#031827] mb-2">Panel SuperAdmin SaaS</h3>
              <p className="text-slate-500 text-sm font-light">Administración global del sistema, suspensión, reactivación y control de inquilinos.</p>
            </div>
            {/* Card 9 */}
            <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow group">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-5 group-hover:bg-[#00B873] group-hover:text-white transition-colors">
                <DollarSign className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#031827] mb-2">Facturación por radicados activos</h3>
              <p className="text-slate-500 text-sm font-light">Simulador de tarifas integradas y control automático de consumo por rango de casos.</p>
            </div>
            {/* Card 10 */}
            <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow group">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-5 group-hover:bg-[#00B873] group-hover:text-white transition-colors">
                <Database className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#031827] mb-2">Auditoría y trazabilidad</h3>
              <p className="text-slate-500 text-sm font-light">Registro detallado de acciones críticas para cumplir con las normativas corporativas.</p>
            </div>
          </div>
        </div>
      </section>

      {/* 6. ESTADOS ELECTRÓNICOS */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-5 space-y-6">
            <div className="text-xs font-bold text-[#00B873] uppercase tracking-widest">Publicaciones Procesales</div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#031827]">
              Estados electrónicos correctos al ingresar al radicado
            </h2>
            <p className="text-slate-600 leading-relaxed font-light">
              JURICOB identifica y muestra las publicaciones procesales oficiales asociadas al expediente judicial, validando documentos por radicado, despacho, actuación y partes involucradas para reducir falsos positivos y centralizar la información legal en el detalle del caso.
            </p>
            
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              {[
                "Publicaciones asociadas al radicado",
                "Autos y providencias relacionados",
                "Validación automática por evidencia",
                "Conservación de historial",
                "Consulta centralizada",
                "Menos revisión manual"
              ].map((bullet, index) => (
                <li key={index} className="flex items-center gap-2 text-sm text-slate-700">
                  <CheckCircle2 className="w-4 h-4 text-[#00B873] flex-shrink-0" />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-7 flex justify-center lg:justify-end">
            <div className="relative w-full max-w-lg bg-[#031827] rounded-2xl shadow-xl p-6 border border-slate-800 text-white font-mono text-xs">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                <span className="text-[#00B873] font-bold">EVIDENCIA DE ESTADO ELECTRÓNICO</span>
                <span className="text-slate-500">ID #29342</span>
              </div>
              <div className="space-y-3 font-mono text-slate-300 leading-relaxed">
                <div><span className="text-slate-500 font-bold">Radicado:</span> 11001400300720230045200</div>
                <div><span className="text-slate-500 font-bold">Despacho:</span> Juzgado 03 Civil Municipal de Bogotá</div>
                <div><span className="text-slate-500 font-bold">Fecha:</span> 2026-06-04</div>
                <div><span className="text-slate-500 font-bold">Actuación:</span> Auto Admite Demanda</div>
                <div className="p-3 bg-[#061B2E] rounded border border-slate-800 text-[11px] text-slate-400">
                  <p className="font-semibold text-white mb-1">Evidencia Documental:</p>
                  "Se deja constancia de publicación en estado electrónico del despacho correspondiente al radicado consultado con fecha del día de hoy..."
                </div>
                <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-900 text-[10px] font-bold uppercase mt-2">
                  <ShieldCheck className="w-3.5 h-3.5" /> Evidencia Validada
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. VIGILANCIA Y ALERTAS */}
      <section className="py-20 bg-white">
        <div className="max-w-4xl mx-auto px-6 text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-[#00B873] flex items-center justify-center mx-auto shadow-sm">
            <Bell className="w-8 h-8" />
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-[#031827]">
            Seguimiento judicial con alertas oportunas
          </h2>
          <p className="text-slate-600 leading-relaxed font-light text-lg">
            Monitorea actuaciones, traslados, términos, audiencias y vencimientos relevantes para reducir riesgos operativos de caducidad o preclusión y mejorar el control integral de la gestión jurídica de tus clientes.
          </p>
        </div>
      </section>

      {/* 8. PANEL MULTIEMPRESA */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <div className="text-xs font-bold text-[#00B873] uppercase tracking-widest">Arquitectura Multitenant</div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#031827]">
              Administración SaaS para empresas y equipos jurídicos
            </h2>
            <p className="text-slate-600 leading-relaxed font-light">
              JURICOB permite administrar múltiples empresas inquilinas, usuarios, roles, permisos y radicados desde un panel global SuperAdmin que centraliza la administración operativa.
            </p>
            
            <div className="space-y-4">
              <div className="flex gap-4 p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
                <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center font-bold text-sm shrink-0">SA</div>
                <div>
                  <h4 className="font-bold text-slate-800 text-sm">SuperAdmin</h4>
                  <p className="text-xs text-slate-500 font-light mt-0.5">Control global de inquilinos, creación y suspensión de empresas, facturación y simuladores.</p>
                </div>
              </div>
              <div className="flex gap-4 p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
                <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-sm shrink-0">AD</div>
                <div>
                  <h4 className="font-bold text-slate-800 text-sm">Administrador de Empresa</h4>
                  <p className="text-xs text-slate-500 font-light mt-0.5">Gestión de usuarios internos y alcance limitado a los expedientes de su respectiva empresa.</p>
                </div>
              </div>
              <div className="flex gap-4 p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
                <div className="w-10 h-10 rounded-lg bg-slate-50 text-slate-600 flex items-center justify-center font-bold text-sm shrink-0">US</div>
                <div>
                  <h4 className="font-bold text-slate-800 text-sm">Usuario Estándar</h4>
                  <p className="text-xs text-slate-500 font-light mt-0.5">Gestión de expedientes judiciales asignados con visualización y actualización propia.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-center">
            <div className="relative w-full max-w-md bg-white border rounded-2xl shadow-xl overflow-hidden p-6 border-slate-100">
              <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-[#00B873]" /> Inquilinos Activos
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border">
                  <span className="font-semibold text-sm text-slate-700">Compañía Petrolera S.A.</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold uppercase">Activo</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border">
                  <span className="font-semibold text-sm text-slate-700">Consorcio Inmobiliario Bogotá</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold uppercase">Activo</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border">
                  <span className="font-semibold text-sm text-slate-700">Carboprocesos del Caribe</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 font-bold uppercase">Inactivo</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 9. FACTURACIÓN Y CONTROL */}
      <section className="py-20 bg-white">
        <div className="max-w-5xl mx-auto px-6 text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-[#00B873] flex items-center justify-center mx-auto shadow-sm">
            <DollarSign className="w-8 h-8" />
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-[#031827]">
            Control de consumo por radicados activos
          </h2>
          <p className="text-slate-600 leading-relaxed font-light text-lg max-w-3xl mx-auto">
            El sistema permite calcular de manera inteligente el consumo mensual de cada empresa en base a sus radicados activos, simular tarifas por rangos de consumo, controlar estados de cobro y suspender administrativamente el acceso sin eliminación de datos para conservar la integridad histórica de sus causas judiciales.
          </p>
        </div>
      </section>

      {/* 10. BENEFICIOS */}
      <section id="beneficios" className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6 space-y-12">
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold tracking-tight text-[#031827]">Beneficios JURICOB</h2>
            <p className="text-slate-500 font-light max-w-xl mx-auto">
              Optimiza tus flujos de trabajo jurídicos y reduce los errores de vigilancia manual.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
            {[
              { t: "Información centralizada", d: "Todos tus expedientes en una sola interfaz." },
              { t: "Reducción de falsos positivos", d: "Validación inteligente y descarte automatizado." },
              { t: "Mayor trazabilidad", d: "Historial completo de estados y actuaciones." },
              { t: "Control de usuarios", d: "Seguridad y aislamiento de accesos." },
              { t: "Seguridad de la información", d: "Respaldo y cifrado de datos críticos." },
              { t: "Ahorro de tiempo operativo", d: "Búsqueda automática y sincronizada." },
              { t: "Gestión de multiempresa", d: "Ideal para bufetes y firmas externas." },
              { t: "Alertas oportunas", d: "Notificaciones y calendarios automáticos." },
              { t: "Acceso móvil/web", d: "Ingresa desde cualquier lugar y dispositivo." },
              { t: "Mejor seguimiento jurídico", d: "Evidencia de todas las actuaciones." }
            ].map((b, idx) => (
              <div key={idx} className="p-5 bg-white rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
                <div>
                  <h4 className="font-bold text-slate-800 text-sm mb-2">{b.t}</h4>
                  <p className="text-xs text-slate-500 font-light leading-normal">{b.d}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 11. PLANES */}
      <section id="planes" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6 space-y-12">
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold tracking-tight text-[#031827]">Planes y Suscripción</h2>
            <p className="text-slate-500 font-light max-w-xl mx-auto">
              Elige el plan ideal para el tamaño de tu firma u organización.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Plan 1 */}
            <div className="p-8 bg-white border border-slate-150 rounded-3xl shadow-sm flex flex-col justify-between hover:border-[#00B873] transition-colors relative overflow-hidden">
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-slate-800">Plan Básico</h3>
                  <p className="text-xs text-slate-400 mt-1 font-light">Para abogados independientes</p>
                </div>
                <div className="h-px bg-slate-100"></div>
                <ul className="space-y-3 text-sm text-slate-600">
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Consulta básica de radicados</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Sincronización de actuaciones</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Historial unificado</li>
                </ul>
              </div>
              <Button onClick={() => scrollToSection('contacto')} className="w-full mt-8 bg-[#031827] hover:bg-[#082A3A] text-white">
                Solicitar cotización
              </Button>
            </div>

            {/* Plan 2 - Destacado */}
            <div className="p-8 bg-[#061B2E] border border-slate-800 rounded-3xl shadow-lg flex flex-col justify-between text-white relative overflow-hidden border-emerald-glow scale-102">
              <div className="absolute top-0 right-0 bg-[#00B873] text-white text-[10px] font-bold tracking-widest px-4 py-1 uppercase rounded-bl-xl">Popular</div>
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-white">Plan Profesional</h3>
                  <p className="text-xs text-slate-400 mt-1 font-light">Para bufetes y firmas legales</p>
                </div>
                <div className="h-px bg-slate-800"></div>
                <ul className="space-y-3 text-sm text-slate-300">
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Publicaciones procesales completas</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Alertas preventivas y vencimientos</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Asignación de tareas internas</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Usuarios por empresa</li>
                </ul>
              </div>
              <Button onClick={() => scrollToSection('contacto')} className="w-full mt-8 bg-[#00B873] hover:bg-[#00A86B] text-white shadow-md shadow-[#00B873]/20">
                Solicitar cotización
              </Button>
            </div>

            {/* Plan 3 */}
            <div className="p-8 bg-white border border-slate-150 rounded-3xl shadow-sm flex flex-col justify-between hover:border-[#00B873] transition-colors relative overflow-hidden">
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-slate-800">Plan Empresarial</h3>
                  <p className="text-xs text-slate-400 mt-1 font-light">Para corporaciones y gran volumen</p>
                </div>
                <div className="h-px bg-slate-100"></div>
                <ul className="space-y-3 text-sm text-slate-600">
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Soporte corporativo multiempresa</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Módulo global SuperAdmin</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Facturación por consumo</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-[#00B873] shrink-0" /> Auditoría e integraciones API</li>
                </ul>
              </div>
              <Button onClick={() => scrollToSection('contacto')} className="w-full mt-8 bg-[#031827] hover:bg-[#082A3A] text-white">
                Solicitar cotización
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* 12. CONTACTO */}
      <section id="contacto" className="py-20 bg-slate-50 border-t">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Lado izquierdo: Información corporativa */}
          <div className="space-y-6 flex flex-col justify-center">
            <div className="text-xs font-bold text-[#00B873] uppercase tracking-widest">Contacto</div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#031827]">
              ¿Interesado en optimizar tu gestión judicial?
            </h2>
            <p className="text-slate-600 leading-relaxed font-light">
              Ponte en contacto con nosotros para recibir una cotización a tu medida o solicitar una demostración personalizada del panel SuperAdmin SaaS y las herramientas de vigilancia de JURICOB.
            </p>
            
            <div className="space-y-4 pt-4 border-t">
              <div className="flex items-center gap-3 text-slate-700">
                <div className="w-10 h-10 rounded-full bg-emerald-50 text-[#00B873] flex items-center justify-center">
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-xs text-slate-400 block font-bold">DESARROLLADO POR</span>
                  <span className="font-semibold text-sm">EMDECOB</span>
                </div>
              </div>

              <div className="flex items-center gap-3 text-slate-700">
                <div className="w-10 h-10 rounded-full bg-emerald-50 text-[#00B873] flex items-center justify-center">
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-xs text-slate-400 block font-bold">CORREO ELECTRÓNICO</span>
                  <span className="font-semibold text-sm font-mono">direccionejecutiva@emdecob.com</span>
                </div>
              </div>

              <div className="flex items-center gap-3 text-slate-700">
                <div className="w-10 h-10 rounded-full bg-emerald-50 text-[#00B873] flex items-center justify-center">
                  <Phone className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-xs text-slate-400 block font-bold">TELÉFONO / WHATSAPP</span>
                  <span className="font-semibold text-sm font-mono">+57 314 892 3929</span>
                </div>
              </div>
            </div>
          </div>

          {/* Lado derecho: Formulario */}
          <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-md">
            <h3 className="text-xl font-bold text-slate-800 mb-6">Solicitar Información</h3>
            <form onSubmit={handleContactSubmit} className="space-y-4">
              <div className="space-y-1">
                <Label htmlFor="c_name" className="text-xs font-bold text-slate-500 uppercase">Nombre Completo <span className="text-rose-500">*</span></Label>
                <Input 
                  id="c_name" 
                  value={contactForm.nombre} 
                  onChange={e => setContactForm({...contactForm, nombre: e.target.value})} 
                  placeholder="Tu nombre..."
                  required
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="c_emp" className="text-xs font-bold text-slate-500 uppercase">Empresa / Firma</Label>
                <Input 
                  id="c_emp" 
                  value={contactForm.empresa} 
                  onChange={e => setContactForm({...contactForm, empresa: e.target.value})} 
                  placeholder="Nombre de la empresa..."
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label htmlFor="c_mail" className="text-xs font-bold text-slate-500 uppercase">Correo de Contacto <span className="text-rose-500">*</span></Label>
                  <Input 
                    id="c_mail" 
                    type="email"
                    value={contactForm.correo} 
                    onChange={e => setContactForm({...contactForm, correo: e.target.value})} 
                    placeholder="ejemplo@correo.com"
                    required
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="c_tel" className="text-xs font-bold text-slate-500 uppercase">Teléfono Movil</Label>
                  <Input 
                    id="c_tel" 
                    value={contactForm.telefono} 
                    onChange={e => setContactForm({...contactForm, telefono: e.target.value})} 
                    placeholder="Ej. +57 300 123 4567"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <Label htmlFor="c_msg" className="text-xs font-bold text-slate-500 uppercase">Mensaje <span className="text-rose-500">*</span></Label>
                <Textarea 
                  id="c_msg" 
                  value={contactForm.mensaje} 
                  onChange={e => setContactForm({...contactForm, mensaje: e.target.value})} 
                  placeholder="Escribe tu mensaje..."
                  rows={4}
                  required
                />
              </div>

              <Button type="submit" disabled={sending} className="w-full mt-4 bg-[#00B873] hover:bg-[#00A86B] text-white font-semibold shadow-md shadow-[#00B873]/10">
                {sending ? 'Enviando...' : 'Solicitar Información'}
              </Button>
            </form>
          </div>
        </div>
      </section>

      {/* 13. FOOTER */}
      <footer className="bg-[#031827] text-white py-12 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#00B873] flex items-center justify-center">
              <Scale className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="font-serif-juricob text-lg tracking-widest font-bold">JURICOB</span>
              <span className="text-[8px] text-slate-400 uppercase tracking-widest block leading-none">by EMDECOB</span>
            </div>
          </div>

          <div className="flex flex-wrap justify-center gap-6 text-sm text-slate-400">
            <button onClick={() => scrollToSection('inicio')} className="hover:text-white transition-colors">Inicio</button>
            <button onClick={() => scrollToSection('plataforma')} className="hover:text-white transition-colors">Plataforma</button>
            <button onClick={() => navigate('/login')} className="hover:text-white transition-colors">Ingresar</button>
            <button onClick={() => navigate('/register-company')} className="hover:text-white transition-colors">Crear Cuenta</button>
            <button onClick={() => scrollToSection('contacto')} className="hover:text-white transition-colors">Contacto</button>
          </div>

          <div className="text-xs text-slate-500 font-mono">
            © {new Date().getFullYear()} EMDECOB. Todos los derechos reservados.
          </div>
        </div>
      </footer>
    </div>
  );
}
