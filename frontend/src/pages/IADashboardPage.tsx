import React, { useState, useEffect } from "react";
import { 
  Sparkles, 
  MessageSquare, 
  FileText, 
  Calendar, 
  AlertTriangle, 
  Send, 
  Bot, 
  User, 
  Clock, 
  ArrowRight, 
  ChevronRight, 
  TrendingUp, 
  ShieldAlert, 
  CheckCircle2, 
  Play, 
  RefreshCw 
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

// Mock data reflecting Colombian legal cases and terminology
const MOCK_DEADLINES = [
  {
    id: 1,
    radicado: "11001400300220260012300",
    demandado: "CREDIVALORES S.A.",
    abogado: "Erick Santiago Garzón",
    termino: "Traslado de excepciones de mérito",
    diasRestantes: 2,
    prioridad: "alta",
    fechaVencimiento: "2026-08-07",
    fuenteActuacion: "Auto del 2026-07-28 que corre traslado de las excepciones de mérito propuestas por la parte demandada por el término de tres (3) días."
  },
  {
    id: 2,
    radicado: "25000234100020260045600",
    demandado: "COLPATRIA MULTIBANCA",
    abogado: "Santiago Quintero Rojas",
    termino: "Subsanación de demanda",
    diasRestantes: 4,
    prioridad: "media",
    fechaVencimiento: "2026-08-09",
    fuenteActuacion: "Auto del 2026-08-02 inadmitiendo la demanda para que en el término de cinco (5) días se allegue certificado catastral actualizado."
  },
  {
    id: 3,
    radicado: "05001310300420260078900",
    demandado: "BANCO GNB SUDAMERIS",
    abogado: "Heriberto Montealegre",
    termino: "Recurso de reposición contra auto de pruebas",
    diasRestantes: 6,
    prioridad: "media",
    fechaVencimiento: "2026-08-11",
    fuenteActuacion: "Auto del 2026-08-04 resolviendo decretar pruebas documentales y negando exhibición de documentos. Término de ejecutoria de tres (3) días."
  },
  {
    id: 4,
    radicado: "76001400302220260098700",
    demandado: "Javier Eduardo Gómez",
    abogado: "Erick Santiago Garzón",
    termino: "Alegatos de conclusión por escrito",
    diasRestantes: 9,
    prioridad: "baja",
    fechaVencimiento: "2026-08-14",
    fuenteActuacion: "Auto del 2026-08-03 que da por finalizada la audiencia de pruebas y concede diez (10) días comunes para presentar alegatos."
  }
];

const MOCK_RISK_CASES = [
  {
    id: 1,
    radicado: "11001400300220260012300",
    demandante: "FNA - Fondo Nacional del Ahorro",
    demandado: "CREDIVALORES S.A.",
    riesgo: "alto",
    porcentajeRiesgo: 82,
    razonamiento: "Alta probabilidad de pérdida o demora extrema debido a que el demandado alegó indebida notificación y el Juzgado 22 Civil del Circuito tiene un precedente del 87% de aceptación de nulidades por esta causal.",
    accionRecomendada: "Revisar inmediatamente la planilla de envío de la empresa de mensajería y preparar memorial de oposición aportando la guía de entrega certificada."
  },
  {
    id: 2,
    radicado: "25000234100020260045600",
    demandante: "FNA - Fondo Nacional del Ahorro",
    demandado: "COLPATRIA MULTIBANCA",
    riesgo: "medio",
    porcentajeRiesgo: 48,
    razonamiento: "Proceso en etapa de subsanación de demanda. Riesgo moderado asociado a posible archivo si no se allega a tiempo el certificado catastral solicitado por el despacho.",
    accionRecomendada: "Gestionar el certificado catastral a través del portal de Catastro Distrital antes del vencimiento del término de 5 días."
  },
  {
    id: 3,
    radicado: "05001310300420260078900",
    demandante: "FNA - Fondo Nacional del Ahorro",
    demandado: "BANCO GNB SUDAMERIS",
    riesgo: "bajo",
    porcentajeRiesgo: 15,
    razonamiento: "Garantía hipotecaria debidamente registrada y admitida por el despacho. No se registran excepciones de fondo complejas ni nulidades por parte de la entidad demandada.",
    accionRecomendada: "Esperar a que se fije fecha para la audiencia de conciliación y saneamiento procesal (Art. 372 CGP)."
  }
];

const SAMPLE_COURT_ACTS = [
  {
    title: "Inadmisión de Demanda (Exigencia de Certificado)",
    text: "JUZGADO VEINTICINCO CIVIL MUNICIPAL DE BOGOTÁ D.C. Bogotá D.C., dos (2) de agosto de dos mil veintiséis (2026). Procede el despacho a resolver sobre la admisibilidad de la demanda ejecutiva singular de menor cuantía presentada por el FONDO NACIONAL DEL AHORRO contra COLPATRIA MULTIBANCA. Al revisar los anexos exigidos por el artículo 84 del Código General del Proceso (CGP), se observa que la parte actora omitió aportar el correspondiente certificado catastral de vigencia del inmueble objeto de la medida cautelar previa, documento indispensable para la debida individualización y avalúo del bien. Por lo anterior, de conformidad con lo normado en el artículo 90 de la citada obra legal, se resuelve: INADMITIR la presente demanda ejecutiva para que la parte demandante, en el término de cinco (5) días hábiles contados a partir del día siguiente al de la notificación del presente auto, proceda a subsanar el defecto señalado, so pena de rechazo procesal."
  },
  {
    title: "Auto que Corre Traslado de Excepciones",
    text: "JUZGADO VEINTIDÓS CIVIL DEL CIRCUITO DE BOGOTÁ D.C. Radicación: 11001400300220260012300. Bogotá D.C., veintiocho (28) de julio de dos mil veintiséis (2026). Al despacho el proceso de la referencia. Habiéndose notificado en debida forma la parte ejecutada CREDIVALORES S.A., y habiendo esta formulado oportunamente excepciones de mérito consistentes en 'Falta de exigibilidad del título ejecutivo' y 'Cobro de lo no debido', el Despacho, en cumplimiento de lo establecido en el inciso segundo del artículo 443 del Código General del Proceso (CGP), resuelve: CORRER TRASLADO de las excepciones de mérito propuestas por la parte ejecutada a la parte ejecutante Fondo Nacional del Ahorro (FNA), por el término legal de tres (3) días hábiles, para que ejerza su derecho de contradicción, solicite pruebas y presente los argumentos que estime pertinentes. Notifíquese."
  },
  {
    title: "Fijación de Audiencia Inicial (Art. 372 CGP)",
    text: "JUZGADO QUINTO CIVIL DEL CIRCUITO DE MEDELLÍN. Proceso Ejecutorio Singular. Demandante: Fondo Nacional del Ahorro. Demandado: BANCO GNB SUDAMERIS. Radicado: 05001310300420260078900. Medellín, cuatro (4) de agosto de dos mil veintiséis (2026). Estando el presente asunto procesal libre de nulidades de carácter constitucional y legal, y habiéndose agotado el término de ejecutoria del auto que resolvió sobre las pruebas propuestas, este Despacho judicial procede a dar aplicación a las normas del juicio oral. En consecuencia, de conformidad con lo prescrito en el artículo 372 del Código General del Proceso (CGP), se resuelve: SEÑALAR el día VEINTICINCO (25) DE AGOSTO DE DOS MIL VEINTISÉIS (2026) a las NUEVE DE LA MAÑANA (09:00 A.M.) para llevar a cabo la AUDIENCIA INICIAL de que trata la norma citada. La presente diligencia se realizará de manera virtual a través de la plataforma Microsoft Teams, para lo cual la Secretaría enviará oportunamente el respectivo enlace de conexión a las direcciones electrónicas de las partes constituidas en el proceso. Notifíquese."
  }
];

export default function IADashboardPage() {
  const [activeTab, setActiveTab] = useState("chat");
  
  // Chat state
  const [messages, setMessages] = useState<Array<{ sender: "ai" | "user", text: string, listData?: any }>>([
    {
      sender: "ai",
      text: "¡Hola! Soy el asistente de IA para JURICOB. Puedo ayudarte a analizar tus procesos del Fondo Nacional del Ahorro (FNA), resumir actuaciones del juzgado, predecir plazos y clasificar riesgos. ¿Qué te gustaría saber hoy?"
    }
  ]);
  const [inputText, setInputText] = useState("");
  const [isAiTyping, setIsAiTyping] = useState(false);

  // Summarizer state
  const [selectedSampleAct, setSelectedSampleAct] = useState(0);
  const [actText, setActText] = useState(SAMPLE_COURT_ACTS[0].text);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [summaryResult, setSummaryResult] = useState<any | null>(null);

  useEffect(() => {
    setActText(SAMPLE_COURT_ACTS[selectedSampleAct].text);
  }, [selectedSampleAct]);

  // Handle preset questions from the screenshot
  const handlePresetQuestion = (question: string, answerType: string) => {
    // Add user message
    setMessages(prev => [...prev, { sender: "user", text: question }]);
    setIsAiTyping(true);

    setTimeout(() => {
      let aiResponseText = "";
      let listData = null;

      if (answerType === "no_movement") {
        aiResponseText = "Al analizar la base de datos de los procesos de la empresa CODE / Fondo Nacional del Ahorro, identifiqué **2 procesos** que llevan más de seis meses sin registrar ninguna actuación judicial o cambio de estado:";
        listData = {
          headers: ["Radicado", "Demandado", "Última Actuación", "Días Inactivo", "Abogado Asignado"],
          rows: [
            ["11001400300220250085400", "Inversiones Bogotá SAS", "2025-10-15 (Auto ordena notificar)", "295 días", "Erick Santiago Garzón"],
            ["25000234100020250096600", "Distribuidora del Norte", "2025-11-20 (Remisión al despacho)", "258 días", "Santiago Quintero"]
          ]
        };
      } else if (answerType === "unfavorable") {
        aiResponseText = "En el último trimestre (Mayo - Julio 2026), se han registrado **3 procesos con sentencias desfavorables o autos de terminación anticipada** que impactan al Fondo Nacional del Ahorro:";
        listData = {
          headers: ["Radicado", "Juzgado", "Demandado", "Fecha Sentencia", "Motivo de Decisión"],
          rows: [
            ["11001400308820250099400", "Juzgado 14 Civil Circuito Bogotá", "Héctor Fabio Castro", "2026-06-12", "Declarada prescripción del título por inactividad procesal (Art. 95 CGP)."],
            ["05001310300220250041200", "Juzgado 2 Civil Circuito Medellín", "Constructoras Asociadas D.C.", "2026-07-04", "Excepción de contrato no cumplido declarada probada en primera instancia."],
            ["76001400302220250051100", "Juzgado 22 Civil Circuito Cali", "Comercializadora Pacífico Ltda", "2026-07-19", "Nulidad absoluta del pagaré por falta de firma del codeudor solidario."]
          ]
        };
      } else if (answerType === "attention") {
        aiResponseText = "Esta semana requieren atención prioritaria **3 procesos** debido a términos procesales próximos a vencer o solicitudes de subsanación urgentes detectadas por nuestro motor de IA:";
        listData = {
          headers: ["Radicado", "Término Procesal", "Fecha Límite", "Abogado", "Acción Pendiente"],
          rows: [
            ["11001400300220260012300", "Traslado de excepciones (3 días)", "2026-08-07 (En 2 días)", "Erick Santiago Garzón", "Contestar excepciones de CREDIVALORES S.A."],
            ["25000234100020260045600", "Subsanación de demanda (5 días)", "2026-08-09 (En 4 días)", "Santiago Quintero Rojas", "Adjuntar certificado catastral actualizado."],
            ["05001310300420260078900", "Ejecutoria de auto de pruebas", "2026-08-11 (En 6 días)", "Heriberto Montealegre", "Radicar recurso de reposición por pruebas negadas."]
          ]
        };
      }

      setMessages(prev => [...prev, { sender: "ai", text: aiResponseText, listData }]);
      setIsAiTyping(false);
    }, 1500);
  };

  // Handle custom user questions
  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const userMsg = inputText.trim();
    setMessages(prev => [...prev, { sender: "user", text: userMsg }]);
    setInputText("");
    setIsAiTyping(true);

    setTimeout(() => {
      // General fallbacks
      let aiResponseText = "Entiendo tu consulta sobre el proceso. Actualmente estoy simulando este asistente inteligente para JURICOB. En el tablero puedes ver los módulos interactivos de Resumen de Actuaciones, Plazos Críticos y Clasificación de Riesgos.";
      
      const lower = userMsg.toLowerCase();
      if (lower.includes("resumen") || lower.includes("resumir")) {
        aiResponseText = "Para resumir una actuación judicial, por favor navega a la pestaña **'Resumidor de Actuaciones'** arriba, selecciona uno de los autos del juzgado de ejemplo, y haz clic en 'Generar Resumen con IA'.";
      } else if (lower.includes("riesgo") || lower.includes("riesgos")) {
        aiResponseText = "Para revisar la clasificación del riesgo de cada proceso, dirígete a la pestaña **'Análisis de Riesgo'** arriba. Allí encontrarás la justificación del porcentaje de riesgo asociado a cada radicado.";
      } else if (lower.includes("plazo") || lower.includes("vencer") || lower.includes("término")) {
        aiResponseText = "Los plazos extraídos por IA para esta semana se encuentran listados en la pestaña **'Alertas de Plazos'**. El proceso con radicado finalizado en *12300* (abogado Erick Santiago Garzón) vence este 7 de agosto.";
      }

      setMessages(prev => [...prev, { sender: "ai", text: aiResponseText }]);
      setIsAiTyping(false);
    }, 1200);
  };

  // Handle AI Summarization simulation
  const handleSummarize = () => {
    setIsSummarizing(true);
    setSummaryResult(null);

    setTimeout(() => {
      let decision = "";
      let termDays = "";
      let actions = [];
      let riskImpact = "";

      if (selectedSampleAct === 0) {
        decision = "Inadmisión de la demanda ejecutiva singular contra COLPATRIA MULTIBANCA.";
        termDays = "Cinco (5) días hábiles contados a partir del día siguiente a la notificación por estado.";
        actions = [
          "Solicitar y expedir el certificado catastral de vigencia del inmueble objeto de embargo preventivo.",
          "Elaborar memorial de subsanación adjuntando el certificado respectivo antes del vencimiento.",
          "Radicar el memorial a través de los canales digitales asignados por el juzgado veinticinco municipal."
        ];
        riskImpact = "Bajo. Es una inadmisión subsanable y de trámite común que no compromete el cobro de la obligación ejecutada.";
      } else if (selectedSampleAct === 1) {
        decision = "Se corre traslado de las excepciones de mérito presentadas por la parte demandada (CREDIVALORES S.A.) a la parte demandante (FNA).";
        termDays = "Tres (3) días hábiles.";
        actions = [
          "Analizar los argumentos de excepción ('Falta de exigibilidad del título' y 'Cobro de lo no debido').",
          "Revisar el estado de cuenta y el historial de pagos del FNA con el deudor para verificar si existen abonos no imputados.",
          "Redactar y radicar memorial descorriendo el traslado de excepciones y solicitando pruebas de soporte de la deuda."
        ];
        riskImpact = "Alto. De no contestarse en término, el juzgado asumirá que no se contradicen los hechos alegados por la contraparte.";
      } else {
        decision = "Se señala fecha y hora para llevar a cabo la audiencia inicial establecida en el artículo 372 del Código General del Proceso (CGP).";
        termDays = "Audiencia fijada para el día 25 de agosto de 2026 a las 09:00 A.M. vía virtual (Microsoft Teams).";
        actions = [
          "Notificar al cliente y al abogado asignado (Heriberto Montealegre) sobre la programación.",
          "Agendar la reunión de Teams respectiva y preparar el interrogatorio de parte.",
          "Verificar la disponibilidad de los poderes del Fondo Nacional del Ahorro debidamente incorporados en el expediente."
        ];
        riskImpact = "Medio. Etapa crítica del proceso CGP donde se fijan los hechos del litigio, se realiza la conciliación y el saneamiento procesal.";
      }

      setSummaryResult({
        decision,
        termDays,
        actions,
        riskImpact
      });
      setIsSummarizing(false);
    }, 1800);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6 animate-fade-in pb-12">
      {/* AI Dashboard Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-violet-700 to-indigo-800 bg-clip-text text-transparent dark:from-violet-400 dark:to-indigo-300">
              Módulo de Inteligencia Artificial (IA)
            </h1>
            <span className="px-2 py-0.5 text-xs font-semibold text-violet-700 bg-violet-100 dark:bg-violet-950/50 dark:text-violet-300 rounded-full border border-violet-200 animate-pulse">
              Piloto IA
            </span>
          </div>
          <p className="text-muted-foreground mt-1">
            Propuesta de valor para incorporar herramientas inteligentes de análisis, clasificación de plazos y automatización judicial en JURICOB.
          </p>
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <div className="flex flex-wrap gap-2 border-b pb-2 border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab("chat")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
            activeTab === "chat"
              ? "bg-violet-600 text-white shadow-sm"
              : "hover:bg-slate-100 dark:hover:bg-slate-850 text-slate-600 dark:text-slate-300"
          }`}
        >
          <MessageSquare className="w-4.5 h-4.5" /> Asistente Chat IA
        </button>
        <button
          onClick={() => setActiveTab("summarizer")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
            activeTab === "summarizer"
              ? "bg-violet-600 text-white shadow-sm"
              : "hover:bg-slate-100 dark:hover:bg-slate-850 text-slate-600 dark:text-slate-300"
          }`}
        >
          <FileText className="w-4.5 h-4.5" /> Resumidor de Actuaciones
        </button>
        <button
          onClick={() => setActiveTab("deadlines")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
            activeTab === "deadlines"
              ? "bg-violet-600 text-white shadow-sm"
              : "hover:bg-slate-100 dark:hover:bg-slate-850 text-slate-600 dark:text-slate-300"
          }`}
        >
          <Calendar className="w-4.5 h-4.5" /> Alertas de Plazos
        </button>
        <button
          onClick={() => setActiveTab("risk")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
            activeTab === "risk"
              ? "bg-violet-600 text-white shadow-sm"
              : "hover:bg-slate-100 dark:hover:bg-slate-850 text-slate-600 dark:text-slate-300"
          }`}
        >
          <AlertTriangle className="w-4.5 h-4.5" /> Análisis de Riesgo
        </button>
      </div>

      {/* Tab 1: AI Chat Assistant */}
      {activeTab === "chat" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 flex flex-col h-[550px] border rounded-xl overflow-hidden bg-card shadow-sm">
            {/* Chat Box Header */}
            <div className="px-4 py-3 bg-slate-50 dark:bg-slate-900 border-b flex items-center gap-2">
              <Bot className="w-5 h-5 text-violet-600" />
              <div>
                <span className="font-semibold text-sm">Asistente Judicial JURICOB AI</span>
                <p className="text-[11px] text-muted-foreground leading-none">Motor de análisis NLP activo</p>
              </div>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50/30 dark:bg-slate-950/20">
              {messages.map((m, idx) => (
                <div 
                  key={idx} 
                  className={`flex gap-3 max-w-[85%] ${m.sender === "user" ? "ml-auto flex-row-reverse" : ""}`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                    m.sender === "ai" ? "bg-violet-100 dark:bg-violet-950/50 text-violet-600" : "bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                  }`}>
                    {m.sender === "ai" ? <Bot className="w-4.5 h-4.5" /> : <User className="w-4.5 h-4.5" />}
                  </div>

                  <div className="space-y-3">
                    <div className={`p-3.5 rounded-2xl text-sm leading-relaxed ${
                      m.sender === "user" 
                        ? "bg-violet-600 text-white rounded-tr-none" 
                        : "bg-white dark:bg-slate-900 border text-slate-800 dark:text-slate-200 rounded-tl-none shadow-sm"
                    }`}>
                      {m.text.split("\n\n").map((para, pIdx) => (
                        <p key={pIdx} className={pIdx > 0 ? "mt-2" : ""}>
                          {para.startsWith("- ") || para.startsWith("* ") 
                            ? para.split("\n").map((bullet, bIdx) => (
                                <span key={bIdx} className="block pl-4 relative before:content-['•'] before:absolute before:left-0 before:text-violet-500">
                                  {bullet.substring(2)}
                                </span>
                              ))
                            : para
                          }
                        </p>
                      ))}
                    </div>

                    {/* Render table if AI response contains structured lists */}
                    {m.listData && (
                      <div className="border rounded-lg overflow-x-auto bg-white dark:bg-slate-900 shadow-sm max-w-full">
                        <table className="w-full text-xs text-left border-collapse">
                          <thead>
                            <tr className="bg-slate-50 dark:bg-slate-850 border-b text-slate-600 dark:text-slate-400 font-semibold">
                              {m.listData.headers.map((h: string, hIdx: number) => (
                                <th key={hIdx} className="p-2 border-r last:border-r-0">{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {m.listData.rows.map((row: string[], rIdx: number) => (
                              <tr key={rIdx} className="border-b last:border-b-0 hover:bg-slate-50/50 dark:hover:bg-slate-850/50">
                                {row.map((val: string, vIdx: number) => (
                                  <td key={vIdx} className="p-2 border-r last:border-r-0 text-slate-700 dark:text-slate-350">{val}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isAiTyping && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-violet-100 dark:bg-violet-950/50 text-violet-600 flex items-center justify-center shrink-0">
                    <Bot className="w-4.5 h-4.5" />
                  </div>
                  <div className="bg-white dark:bg-slate-900 border p-3.5 rounded-2xl rounded-tl-none shadow-sm flex items-center gap-1">
                    <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                    <span className="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                    <span className="w-2 h-2 bg-violet-600 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                  </div>
                </div>
              )}
            </div>

            {/* Chat Input Form */}
            <form onSubmit={handleSendMessage} className="p-3 border-t bg-white dark:bg-slate-900 flex gap-2">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Escribe una pregunta sobre tus procesos..."
                className="flex-1 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                disabled={isAiTyping}
              />
              <Button type="submit" disabled={isAiTyping} className="bg-violet-600 hover:bg-violet-700 text-white shrink-0">
                <Send className="w-4 h-4" />
              </Button>
            </form>
          </div>

          {/* Preset Questions Panel */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-violet-600" />
                  Consultas Rápidas
                </CardTitle>
                <CardDescription>
                  Preguntas clave planteadas para el análisis automatizado de procesos en JURICOB.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2.5">
                <button
                  onClick={() => handlePresetQuestion("¿Cuáles procesos llevan más de seis meses sin movimiento?", "no_movement")}
                  className="w-full text-left p-3 text-xs bg-slate-50 hover:bg-violet-50 dark:bg-slate-900 dark:hover:bg-violet-955 border rounded-lg hover:border-violet-300 transition-all flex items-center justify-between group"
                  disabled={isAiTyping}
                >
                  <span className="text-slate-700 dark:text-slate-300 group-hover:text-violet-700 dark:group-hover:text-violet-400">
                    ¿Cuáles procesos llevan más de seis meses sin movimiento?
                  </span>
                  <ChevronRight className="w-4.5 h-4.5 shrink-0 text-slate-400 group-hover:translate-x-1 transition-transform" />
                </button>

                <button
                  onClick={() => handlePresetQuestion("Muéstrame las sentencias desfavorables del último trimestre.", "unfavorable")}
                  className="w-full text-left p-3 text-xs bg-slate-50 hover:bg-violet-50 dark:bg-slate-900 dark:hover:bg-violet-955 border rounded-lg hover:border-violet-300 transition-all flex items-center justify-between group"
                  disabled={isAiTyping}
                >
                  <span className="text-slate-700 dark:text-slate-300 group-hover:text-violet-700 dark:group-hover:text-violet-400">
                    Muéstrame las sentencias desfavorables del último trimestre.
                  </span>
                  <ChevronRight className="w-4.5 h-4.5 shrink-0 text-slate-400 group-hover:translate-x-1 transition-transform" />
                </button>

                <button
                  onClick={() => handlePresetQuestion("¿Qué procesos requieren atención esta semana?", "attention")}
                  className="w-full text-left p-3 text-xs bg-slate-50 hover:bg-violet-50 dark:bg-slate-900 dark:hover:bg-violet-955 border rounded-lg hover:border-violet-300 transition-all flex items-center justify-between group"
                  disabled={isAiTyping}
                >
                  <span className="text-slate-700 dark:text-slate-300 group-hover:text-violet-700 dark:group-hover:text-violet-400">
                    ¿Qué procesos requieren atención esta semana?
                  </span>
                  <ChevronRight className="w-4.5 h-4.5 shrink-0 text-slate-400 group-hover:translate-x-1 transition-transform" />
                </button>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-violet-500/5 to-indigo-500/10 border-violet-100 dark:border-violet-950">
              <CardContent className="pt-6 space-y-3">
                <div className="flex items-center gap-2 text-violet-700 dark:text-violet-300">
                  <Bot className="w-5 h-5" />
                  <span className="font-semibold text-sm">Cómo funciona la IA</span>
                </div>
                <p className="text-xs text-slate-650 dark:text-slate-350 leading-relaxed">
                  Esta simulación utiliza modelos lingüísticos avanzados (NLP) adaptados al vocabulario procesal de la Rama Judicial de Colombia para extraer términos procesales, fechas límite implícitas y ponderar el riesgo legal con base en estadísticas de fallos anteriores.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Tab 2: Act Summarizer */}
      {activeTab === "summarizer" && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">1. Seleccionar Ejemplo</CardTitle>
                <CardDescription>
                  Prueba el analizador de autos judiciales con plantillas del FNA.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {SAMPLE_COURT_ACTS.map((act, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedSampleAct(idx)}
                    className={`w-full text-left p-3 text-xs border rounded-lg transition-all flex items-center gap-2.5 ${
                      selectedSampleAct === idx
                        ? "border-violet-500 bg-violet-50/50 text-violet-850 dark:bg-violet-950/20 dark:text-violet-300 font-semibold"
                        : "hover:bg-slate-50 dark:hover:bg-slate-850 text-slate-700 dark:text-slate-350"
                    }`}
                  >
                    <FileText className={`w-4.5 h-4.5 ${selectedSampleAct === idx ? "text-violet-600" : "text-slate-400"}`} />
                    <span className="truncate">{act.title}</span>
                  </button>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Texto de la Actuación</CardTitle>
                <CardDescription>
                  Texto crudo del boletín judicial o PDF cargado por el scraper.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <textarea
                  value={actText}
                  onChange={(e) => setActText(e.target.value)}
                  className="w-full h-48 p-3 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-lg focus:outline-none focus:ring-2 focus:ring-violet-500 font-mono"
                />
                
                <Button 
                  onClick={handleSummarize} 
                  disabled={isSummarizing || !actText.trim()}
                  className="w-full bg-violet-600 hover:bg-violet-700 text-white flex items-center justify-center gap-2 text-xs"
                >
                  {isSummarizing ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Analizando actuación con IA...
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5 fill-current" />
                      Generar Resumen de Actuación
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-3">
            <Card className="h-full flex flex-col">
              <CardHeader className="border-b bg-slate-50/50 dark:bg-slate-900/30">
                <CardTitle className="text-base flex items-center gap-2">
                  <Bot className="w-5 h-5 text-violet-600" />
                  Resultado del Análisis Inteligente
                </CardTitle>
                <CardDescription>
                  Resumen estructurado y detección de términos extraídos del documento legal.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 p-6 flex flex-col justify-center">
                {isSummarizing ? (
                  <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                    <RefreshCw className="w-10 h-10 text-violet-600 animate-spin" />
                    <div>
                      <p className="font-semibold text-slate-850 dark:text-slate-200 text-sm">Extrayendo información clave</p>
                      <p className="text-xs text-muted-foreground mt-1">El motor NLP está parseando los artículos del CGP y las fechas límite...</p>
                    </div>
                  </div>
                ) : summaryResult ? (
                  <div className="space-y-6 text-sm animate-fade-in">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-violet-600 tracking-wider">Decisión Principal del Despacho</span>
                      <p className="font-semibold text-slate-850 dark:text-slate-100 text-base mt-0.5 leading-snug">
                        {summaryResult.decision}
                      </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-3 bg-amber-500/5 border border-amber-500/10 rounded-lg">
                        <span className="text-[10px] uppercase font-bold text-amber-600 tracking-wider flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" /> Plazo Extraído de IA
                        </span>
                        <p className="font-medium text-slate-800 dark:text-slate-200 mt-1 leading-snug">
                          {summaryResult.termDays}
                        </p>
                      </div>

                      <div className="p-3 bg-red-500/5 border border-red-500/10 rounded-lg">
                        <span className="text-[10px] uppercase font-bold text-red-650 tracking-wider flex items-center gap-1">
                          <TrendingUp className="w-3.5 h-3.5" /> Impacto y Nivel de Riesgo
                        </span>
                        <p className="font-medium text-slate-800 dark:text-slate-200 mt-1 leading-snug">
                          {summaryResult.riskImpact}
                        </p>
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-bold text-violet-600 tracking-wider">Acciones Sugeridas para el Apoderado</span>
                      <ul className="mt-2 space-y-2">
                        {summaryResult.actions.map((act: string, idx: number) => (
                          <li key={idx} className="flex gap-2.5 items-start">
                            <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                            <span className="text-slate-700 dark:text-slate-300 text-xs">{act}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-20 text-center text-muted-foreground">
                    <FileText className="w-12 h-12 text-slate-350 dark:text-slate-750 mb-3" />
                    <p className="text-sm font-semibold">Sin datos procesados</p>
                    <p className="text-xs mt-1 max-w-sm">
                      Selecciona un ejemplo a la izquierda y presiona el botón para ver cómo la IA extrae plazos y resume providencias del juzgado.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Tab 3: Deadlines & Terms */}
      {activeTab === "deadlines" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Calendar className="w-5.5 h-5.5 text-violet-600" />
              Alertas de Plazos Inteligentes (Extracción NLP)
            </CardTitle>
            <CardDescription>
              Términos próximos a vencer detectados de forma autónoma a partir de la redacción de los autos notificados.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0 border-t">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-900 border-b text-slate-650 dark:text-slate-400 font-semibold">
                    <th className="p-4">Prioridad / Estado</th>
                    <th className="p-4">Radicado del Proceso</th>
                    <th className="p-4">Término Judicial</th>
                    <th className="p-4">Vencimiento Calculado</th>
                    <th className="p-4">Acción Requerida</th>
                    <th className="p-4">Abogado</th>
                  </tr>
                </thead>
                <tbody>
                  {MOCK_DEADLINES.map((d) => (
                    <tr key={d.id} className="border-b last:border-b-0 hover:bg-slate-50/50 dark:hover:bg-slate-850/50">
                      <td className="p-4">
                        <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${
                          d.prioridad === "alta" 
                            ? "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/20 dark:text-red-300 dark:border-red-900" 
                            : d.prioridad === "media" 
                            ? "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/20 dark:text-amber-300 dark:border-amber-900"
                            : "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/20 dark:text-blue-300 dark:border-blue-900"
                        }`}>
                          {d.prioridad === "alta" ? "Crítico" : d.prioridad === "media" ? "Próximo" : "Pendiente"} ({d.diasRestantes}d)
                        </span>
                      </td>
                      <td className="p-4 font-mono text-xs">{d.radicado}</td>
                      <td className="p-4 font-medium text-slate-850 dark:text-slate-200">{d.termino}</td>
                      <td className="p-4 text-xs font-medium">{d.fechaVencimiento}</td>
                      <td className="p-4 max-w-xs text-xs text-muted-foreground leading-relaxed">
                        {d.fuenteActuacion}
                      </td>
                      <td className="p-4 text-xs font-medium">{d.abogado}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tab 4: Risk Analysis */}
      {activeTab === "risk" && (
        <div className="space-y-6">
          {/* Overview Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="border-l-4 border-l-red-500">
              <CardContent className="pt-6">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Alto Riesgo</span>
                    <h3 className="text-3xl font-extrabold mt-1 text-slate-800 dark:text-slate-100">1 Proceso</h3>
                  </div>
                  <div className="p-2 rounded-full bg-red-50 dark:bg-red-950/20 text-red-650">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                </div>
                <p className="text-[11px] text-muted-foreground mt-3 leading-relaxed">
                  Alta probabilidad de pérdida o necesidad de saneamiento por nulidades de notificación o fallos.
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-amber-500">
              <CardContent className="pt-6">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Riesgo Medio</span>
                    <h3 className="text-3xl font-extrabold mt-1 text-slate-800 dark:text-slate-100">1 Proceso</h3>
                  </div>
                  <div className="p-2 rounded-full bg-amber-50 dark:bg-amber-950/20 text-amber-650">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                </div>
                <p className="text-[11px] text-muted-foreground mt-3 leading-relaxed">
                  Procesos con términos en curso o inadmisiones activas que requieren subsanación urgente de documentos.
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-emerald-500">
              <CardContent className="pt-6">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Riesgo Bajo</span>
                    <h3 className="text-3xl font-extrabold mt-1 text-slate-800 dark:text-slate-100">1 Proceso</h3>
                  </div>
                  <div className="p-2 rounded-full bg-emerald-50 dark:bg-emerald-950/20 text-emerald-650">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                </div>
                <p className="text-[11px] text-muted-foreground mt-3 leading-relaxed">
                  Procesos estables con garantías reales hipotecarias confirmadas y sin excepciones complejas.
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Risk Detail Cards */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Detalle de Ponderación Legal de Riesgo</CardTitle>
              <CardDescription>
                Explicación de las causales de riesgo calculadas autónomamente para los procesos activos del FNA.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {MOCK_RISK_CASES.map((rc) => (
                <div 
                  key={rc.id} 
                  className="p-4 border rounded-lg bg-slate-50/20 dark:bg-slate-900/30 flex flex-col md:flex-row gap-4 items-start justify-between"
                >
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-700 dark:text-slate-350">{rc.radicado}</span>
                      <span className={`px-2 py-0.5 text-[10px] font-semibold rounded border ${
                        rc.riesgo === "alto" 
                          ? "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/20 dark:text-red-300" 
                          : rc.riesgo === "medio" 
                          ? "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/20 dark:text-amber-300"
                          : "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/20 dark:text-emerald-300"
                      }`}>
                        Riesgo {rc.riesgo.toUpperCase()} ({rc.porcentajeRiesgo}%)
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400">Pares Procesales:</span>
                      <p className="text-xs font-medium text-slate-750 dark:text-slate-200">{rc.demandante} VS. {rc.demandado}</p>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400">Análisis Predictivo de la IA:</span>
                      <p className="text-xs text-muted-foreground leading-relaxed mt-0.5">{rc.razonamiento}</p>
                    </div>
                  </div>

                  <div className="w-full md:w-80 p-3.5 bg-violet-500/5 border border-violet-500/10 rounded-lg space-y-1.5 shrink-0 self-stretch flex flex-col justify-center">
                    <span className="text-[10px] uppercase font-bold text-violet-750 dark:text-violet-300 tracking-wider flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" /> Acción Recomendada por IA
                    </span>
                    <p className="text-xs text-slate-750 dark:text-slate-350 leading-relaxed font-medium">
                      {rc.accionRecomendada}
                    </p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
