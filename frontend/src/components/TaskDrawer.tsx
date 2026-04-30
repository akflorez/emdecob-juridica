import { useState, useEffect, useMemo } from "react";
import { 
  X, Calendar as CalendarIcon, User as UserIcon, CheckCircle2, 
  Clock, Tag, Paperclip, MessageSquare, Plus, ChevronRight, 
  Send, Trash2, ListChecks, Zap, Flag, AlertCircle, Edit3,
  UserCheck, Search, Activity, CornerDownRight, Smile, MoreHorizontal,
  ChevronDown, CalendarDays, Layout, Check, Trash, RefreshCw,
  Play, Settings, Hash, Paperclip as AttachmentIcon, MessageCircle
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { 
  updateTask, addComment, deleteComment, updateComment,
  addChecklistItem, updateChecklistItem, deleteChecklistItem,
  getUsers, getTags, getStatuses, getTaskDetail, createTask,
  type Task as TaskType, type User, type Tag as TagType
} from "@/services/api";
import { useToast } from "@/hooks/use-toast";
import { format, isValid, parseISO } from "date-fns";
import { es } from "date-fns/locale";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue 
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";

interface TaskDrawerProps {
  task: TaskType | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskUpdate: (updatedTask: TaskType) => void;
  clickupToken?: string;
  allAssignees?: string[];
  allStatuses?: string[];
}

export function TaskDrawer({ task, open, onOpenChange, onTaskUpdate, clickupToken, allStatuses: propStatuses = [] }: TaskDrawerProps) {
  const { toast } = useToast();
  const [editedTitle, setEditedTitle] = useState('');
  const [editedDesc, setEditedDesc] = useState('');
  const [editedDueDate, setEditedDueDate] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [fullTask, setFullTask] = useState<TaskType | null>(null);
  const [newComment, setNewComment] = useState('');
  const [newChecklist, setNewChecklist] = useState("");
  const [allTags, setAllTags] = useState<TagType[]>([]);
  const [allSystemStatuses, setAllSystemStatuses] = useState<string[]>([]);
  
  // Subtask form states
  const [showSubtaskForm, setShowSubtaskForm] = useState(false);
  const [newSubtaskTitle, setNewSubtaskTitle] = useState("");
  const [newSubtaskDate, setNewSubtaskDate] = useState("");
  const [newSubtaskAssigneeId, setNewSubtaskAssigneeId] = useState<number | undefined>(undefined);
  const [newSubtaskPriority, setNewSubtaskPriority] = useState<string>("normal");

  const [editingCommentId, setEditingCommentId] = useState<number | null>(null);
  const [editingCommentText, setEditingCommentText] = useState("");

  const displayTask = fullTask || task;

  useEffect(() => {
    if (task && open) {
      setEditedTitle(task.title || '');
      setEditedDesc(task.description || '');
      setEditedDueDate(task.due_date ? format(parseISO(task.due_date.toString()), 'yyyy-MM-dd') : '');
      refreshTask();
      
      // Fetch users
      getUsers().then(res => {
        if (Array.isArray(res)) setUsers(res);
      }).catch(err => {
        console.error("Error al cargar abogados:", err);
      });

      getTags().then(res => {
        if (Array.isArray(res) && res.length > 0) setAllTags(res);
        else if (task.tags) setAllTags(task.tags);
      }).catch(() => {
        if (task.tags) setAllTags(task.tags);
      });

      getStatuses().then(res => setAllSystemStatuses(Array.isArray(res) ? res : [])).catch(console.error);
    }
  }, [task, open]);

  const refreshTask = async () => {
    if (!task) return;
    setIsLoading(true);
    try {
      const detail = await getTaskDetail(task.id, clickupToken);
      if (detail) {
        setFullTask(detail);
      }
    } catch (error) {
      console.error("Error refreshing task", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async (updates: Partial<TaskType>) => {
    if (!displayTask) return;
    try {
      const cleanedUpdates = { ...updates };
      if (cleanedUpdates.due_date && typeof cleanedUpdates.due_date === 'string') {
        cleanedUpdates.due_date = new Date(cleanedUpdates.due_date).toISOString();
      }

      const updated = await updateTask(displayTask.id, cleanedUpdates);
      onTaskUpdate(updated);
      setFullTask(updated);
    } catch (error) {
      toast({ title: "Error de sincronización", description: "Verifica el estado del servidor judicial.", variant: "destructive" });
    }
  };

  const toggleAssignee = (userId: number) => {
    if (!displayTask) return;
    const currentIds = (displayTask.assignees || []).map(a => a.id);
    let newIds = currentIds.includes(userId) ? currentIds.filter(id => id !== userId) : [...currentIds, userId];
    handleSave({ assignee_ids: newIds } as any);
  };

  const toggleTag = (tagName: string) => {
    if (!displayTask) return;
    const currentTags = (displayTask.tags || []).map(t => t.name);
    let newTags = currentTags.includes(tagName) ? currentTags.filter(t => t !== tagName) : [...currentTags, tagName];
    handleSave({ tags: newTags } as any);
  };

  const handleAddComment = async () => {
    if (!displayTask || !newComment.trim()) return;
    try {
      await addComment(displayTask.id, newComment);
      setNewComment('');
      refreshTask();
    } catch (error) {
      toast({ title: "Error al publicar registro" });
    }
  };

  const handleUpdateComment = async (id: number) => {
    if (!editingCommentText.trim()) return;
    try {
      await updateComment(id, editingCommentText);
      setEditingCommentId(null);
      refreshTask();
    } catch (error) {
      toast({ title: "Error al editar" });
    }
  };

  const handleDeleteComment = async (id: number) => {
    if (!confirm("¿Eliminar registro definitivo de actividad?")) return;
    try {
      await deleteComment(id);
      refreshTask();
    } catch (error) {
      toast({ title: "Error al eliminar" });
    }
  };

  const handleCreateSubtask = async () => {
    if (!displayTask || !newSubtaskTitle.trim()) return;
    try {
      const isoDate = newSubtaskDate ? new Date(newSubtaskDate).toISOString() : undefined;
      
      await createTask({
        title: newSubtaskTitle,
        parent_id: displayTask.id,
        due_date: isoDate as any,
        list_id: displayTask.list_id,
        case_id: displayTask.case_id,
        assignee_id: newSubtaskAssigneeId,
        priority: newSubtaskPriority,
        status: 'to do'
      });
      setNewSubtaskTitle("");
      setNewSubtaskDate("");
      setNewSubtaskAssigneeId(undefined);
      setNewSubtaskPriority("normal");
      setShowSubtaskForm(false);
      refreshTask();
      toast({ title: "Gestión técnica vinculada correctamente" });
    } catch (error) {
      toast({ title: "Fallo en creación de gestión", variant: "destructive" });
    }
  };

  const handleAddChecklist = async () => {
    if (!displayTask || !newChecklist.trim()) return;
    try {
      await addChecklistItem(displayTask.id, newChecklist);
      setNewChecklist("");
      refreshTask();
    } catch (error) {
      toast({ title: "Error" });
    }
  };

  if (!displayTask) return null;

  const statusOptions = Array.from(new Set([
    'ABIERTO', 'TO DO', 'IN PROGRESS', 'PENDIENTE', 'ALMP', '468', 'REMATE', 'AVALUO', 'COMPLETO', 'CLOSED',
    ...(allSystemStatuses || []),
    ...(propStatuses || [])
  ])).filter(Boolean);

  const currentStatus = (displayTask.status || 'ABIERTO').toUpperCase();
  
  const totalSub = displayTask.subtasks?.length || 0;
  const doneSub = displayTask.subtasks?.filter(s => ['completado', 'closed', 'done'].includes(s.status?.toLowerCase() || '')).length || 0;
  const progressSub = totalSub > 0 ? (doneSub / totalSub) * 100 : 0;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[1550px] p-0 bg-[#0a0a0a] border-none text-[#d1d1d1] flex flex-col shadow-2xl font-sans outline-none">
        <SheetHeader className="sr-only"><SheetTitle>Consola Judicial Expert Mode</SheetTitle></SheetHeader>
        
        <div className="flex flex-1 overflow-hidden h-full">
          {/* MAIN PANEL (EXPANDED 60%) */}
          <div className="flex-[1.5] flex flex-col overflow-hidden bg-[#0a0a0a]">
             <ScrollArea className="flex-1 px-16 pt-10 pb-24">
                <div className="space-y-12 max-w-[1100px] mx-auto">
                   
                   {/* Advanced Header */}
                   <div className="flex items-center justify-between text-[11px] font-black text-gray-600 uppercase tracking-[0.4em]">
                      <div className="flex items-center gap-4">
                         <div className="flex items-center gap-3 px-4 py-1.5 bg-white/[0.03] rounded-full border border-white/5 shadow-inner">
                            <Badge className="h-4 w-4 p-0 bg-[#2da44e] flex items-center justify-center rounded-sm ring-4 ring-[#2da44e]/10"><Check className="h-3 w-3 text-white" /></Badge>
                            <span className="text-gray-400">Carpeta Judicial Digital</span>
                            <ChevronDown className="h-3.5 w-3.5 text-gray-700" />
                         </div>
                         <span className="text-primary font-black tracking-[0.5em]">{displayTask.clickup_id || displayTask.id}</span>
                      </div>
                      <div className="flex items-center gap-6">
                         <Button variant="ghost" size="sm" onClick={refreshTask} disabled={isLoading} className="text-gray-500 hover:text-white gap-3 font-black text-[10px] tracking-[0.3em] transition-all">
                            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} /> ACTUALIZAR DATOS
                         </Button>
                         <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="h-10 w-10 text-gray-700 hover:text-white transition-all">
                           <X className="h-8 w-8" />
                         </Button>
                      </div>
                   </div>

                   {/* Master Title */}
                   <input 
                     className="w-full bg-transparent text-5xl font-black tracking-tight border-none focus:ring-0 p-0 text-white placeholder:text-gray-900 transition-all"
                     value={editedTitle}
                     onChange={(e) => setEditedTitle(e.target.value)}
                     onBlur={() => handleSave({ title: editedTitle })}
                   />

                   {/* Expanded Metadata Grid */}
                   <div className="grid grid-cols-2 lg:grid-cols-4 gap-12 py-10 border-y border-white/5 bg-white/[0.01] px-10 rounded-[3rem] shadow-inner">
                      {/* Estado */}
                      <div className="flex flex-col gap-4">
                         <span className="text-[11px] text-gray-600 font-black uppercase tracking-[0.4em] flex items-center gap-3"><Activity className="h-4 w-4 text-primary" /> Estado Actual</span>
                         <Select value={statusOptions.includes(currentStatus) ? currentStatus : undefined} onValueChange={(v) => handleSave({ status: v })}>
                            <SelectTrigger className="h-14 w-full bg-[#2da44e] hover:bg-[#34bc5a] text-white text-[13px] font-black uppercase rounded-2xl border-none px-6 transition-all shadow-2xl shadow-[#2da44e]/20 ring-4 ring-[#2da44e]/10">
                               <SelectValue placeholder={currentStatus} />
                            </SelectTrigger>
                            <SelectContent className="bg-[#1e1e1e] border-white/10 text-white shadow-2xl rounded-2xl">
                               {statusOptions.map(s => (
                                 <SelectItem key={s} value={s} className="uppercase text-[12px] font-black py-4 tracking-widest">{s}</SelectItem>
                               ))}
                            </SelectContent>
                         </Select>
                      </div>

                      {/* Abogados */}
                      <div className="flex flex-col gap-4">
                         <span className="text-[11px] text-gray-600 font-black uppercase tracking-[0.4em] flex items-center gap-3"><UserIcon className="h-4 w-4 text-primary" /> Responsable</span>
                         <Popover>
                            <PopoverTrigger asChild>
                               <Button variant="outline" className="h-14 w-full bg-white/[0.03] border-white/10 rounded-2xl flex items-center justify-start gap-4 px-5 hover:bg-white/5 transition-all group shadow-inner border-2 hover:border-primary/30">
                                  <div className="flex -space-x-3">
                                     {displayTask.assignees?.length ? (
                                        displayTask.assignees.map(a => (
                                          <div key={a.id} className="h-9 w-9 rounded-full bg-gradient-to-br from-[#ff7b72] to-[#f85149] border-2 border-[#111] flex items-center justify-center text-[13px] font-black text-white shadow-2xl ring-2 ring-white/5">{a.nombre?.[0] || a.username[0]}</div>
                                        ))
                                     ) : (
                                        <div className="h-9 w-9 rounded-full border-2 border-dashed border-gray-800 bg-gray-900 flex items-center justify-center text-gray-700"><UserIcon className="h-5 w-5" /></div>
                                     )}
                                  </div>
                                  <span className="text-[14px] font-black text-gray-200 truncate group-hover:text-primary transition-colors tracking-tight">
                                     {displayTask.assignees?.length ? displayTask.assignees.map(a => a.nombre || a.username).join(', ') : (displayTask.assignee_name || 'Sin Asignar')}
                                  </span>
                               </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-96 p-4 bg-[#1e1e1e] border-white/10 text-white rounded-[2rem] shadow-2xl ring-1 ring-white/5">
                               <ScrollArea className="h-[400px]">
                                  <div className="p-4 border-b border-white/5 mb-4 text-[11px] font-black uppercase text-gray-600 tracking-[0.5em] text-center">Equipo de Litigio</div>
                                  <div className="space-y-2">
                                    {users.map(u => (
                                      <div key={u.id} className="flex items-center justify-between p-4 hover:bg-white/10 rounded-2xl cursor-pointer transition-all border border-transparent hover:border-white/10 group" onClick={() => toggleAssignee(u.id)}>
                                         <div className="flex flex-col">
                                            <span className="text-[15px] font-black text-gray-200 group-hover:text-primary">{u.nombre || u.username}</span>
                                            <span className="text-[10px] text-gray-500 font-black uppercase tracking-widest">Jurídico Especializado</span>
                                         </div>
                                         <Checkbox checked={displayTask.assignees?.some(a => a.id === u.id)} className="h-7 w-7 border-white/20 data-[state=checked]:bg-primary rounded-lg" />
                                      </div>
                                    ))}
                                  </div>
                               </ScrollArea>
                            </PopoverContent>
                         </Popover>
                      </div>

                      {/* Fecha Vencimiento */}
                      <div className="flex flex-col gap-4">
                         <span className="text-[11px] text-gray-600 font-black uppercase tracking-[0.4em] flex items-center gap-3"><CalendarIcon className="h-4 w-4 text-primary" /> Término Legal</span>
                         <div className="h-14 bg-white/[0.03] border border-white/10 rounded-2xl flex items-center gap-5 px-6 hover:border-primary/40 transition-all shadow-inner border-2">
                            <input 
                              type="date" 
                              className="bg-transparent border-none focus:ring-0 text-[14px] font-black uppercase text-gray-100 p-0 w-full cursor-pointer"
                              value={editedDueDate}
                              onChange={(e) => {
                                setEditedDueDate(e.target.value);
                                handleSave({ due_date: e.target.value } as any);
                              }}
                            />
                         </div>
                      </div>

                      {/* Clasificación Tags */}
                      <div className="flex flex-col gap-4">
                         <span className="text-[11px] text-gray-600 font-black uppercase tracking-[0.4em] flex items-center gap-3"><Tag className="h-4 w-4 text-primary" /> Clasificación</span>
                         <Popover>
                            <PopoverTrigger asChild>
                               <Button variant="outline" className="h-14 w-full bg-white/[0.03] border-white/10 rounded-2xl flex flex-wrap gap-2 px-5 hover:bg-white/5 transition-all justify-start overflow-hidden py-3 shadow-inner border-2 hover:border-primary/30">
                                  {displayTask.tags?.length ? (
                                    displayTask.tags.map(t => (
                                      <Badge key={t.id} style={{ backgroundColor: t.color || '#3b82f6', color: '#fff' }} className="h-7 text-[10px] font-black px-4 rounded-lg border-none shadow-2xl ring-2 ring-white/10">
                                         {t.name}
                                      </Badge>
                                    ))
                                  ) : (
                                    <span className="text-[12px] text-gray-700 font-black tracking-[0.3em] uppercase">+ ETIQUETAS</span>
                                  )}
                               </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-96 p-5 bg-[#1e1e1e] border-white/10 text-white rounded-[2rem] shadow-2xl">
                               <ScrollArea className="h-[350px]">
                                  <div className="p-3 border-b border-white/5 mb-5 text-[11px] font-black uppercase text-gray-600 tracking-[0.5em] text-center">Filtros Maestros</div>
                                  <div className="grid grid-cols-1 gap-3">
                                    {allTags.map(t => (
                                      <div key={t.id} className="flex items-center justify-between p-4 hover:bg-white/10 rounded-2xl cursor-pointer transition-all border border-transparent hover:border-white/10 group" onClick={() => toggleTag(t.name)}>
                                         <div className="flex items-center gap-4">
                                            <div className="h-5 w-5 rounded-full shadow-2xl ring-4 ring-white/5" style={{ backgroundColor: t.color || '#3b82f6' }} />
                                            <span className="text-[15px] font-black text-gray-200 group-hover:text-primary transition-colors">{t.name}</span>
                                         </div>
                                         {displayTask.tags?.some(gt => gt.name === t.name) && <CheckCircle2 className="h-6 w-6 text-[#2da44e]" />}
                                      </div>
                                    ))}
                                  </div>
                               </ScrollArea>
                            </PopoverContent>
                         </Popover>
                      </div>
                   </div>

                   {/* Wide Description Area */}
                   <div className="space-y-6 pt-6">
                      <div className="flex items-center gap-4 text-gray-600 italic text-[13px] font-black tracking-[0.4em] uppercase">
                         <Activity className="h-5 w-5 text-primary opacity-70" /> Síntesis de Avance Procesal
                      </div>
                      <div className="bg-white/[0.01] rounded-[3rem] p-10 border border-white/5 shadow-2xl relative group">
                        <Textarea 
                          className="min-h-[250px] bg-transparent border-none p-0 text-[18px] leading-relaxed text-gray-200 focus:ring-0 placeholder:text-gray-900 transition-all font-medium"
                          placeholder="Describe el estado detallado de esta actuación judicial..."
                          value={editedDesc}
                          onChange={(e) => setEditedDesc(e.target.value)}
                          onBlur={() => handleSave({ description: editedDesc })}
                        />
                        <div className="absolute bottom-6 right-8 opacity-0 group-hover:opacity-100 transition-all text-[10px] font-black text-gray-700 tracking-widest uppercase">Autoguardado inteligente activo</div>
                      </div>
                   </div>

                   {/* Master Subtasks Table */}
                   <div className="space-y-10 pt-16 border-t border-white/5">
                      <div className="flex items-center justify-between">
                         <div className="flex items-center gap-8">
                            <div className="flex items-center gap-4 text-gray-300 font-black text-[18px] uppercase tracking-[0.4em]">
                               <ChevronDown className="h-8 w-8 text-primary" /> Gestiones Técnicas
                            </div>
                            <div className="flex items-center gap-5 text-[13px] text-gray-400 font-black tracking-[0.2em] bg-white/[0.03] px-8 py-3 rounded-full border border-white/5 shadow-inner">
                               <span>{doneSub}/{totalSub} COMPLETADAS</span>
                               <Progress value={progressSub} className="w-60 h-2.5 bg-gray-950 ring-1 ring-white/5" />
                            </div>
                         </div>
                         <div className="flex items-center gap-6">
                            <Button variant="outline" size="icon" onClick={refreshTask} className="h-12 w-12 rounded-2xl bg-white/5 border-white/10 hover:bg-white/10 hover:text-white transition-all shadow-xl"><RefreshCw className={cn("h-6 w-6", isLoading && "animate-spin")} /></Button>
                            <Button size="lg" onClick={() => setShowSubtaskForm(true)} className="h-14 px-10 rounded-[1.5rem] bg-primary text-white font-black text-[12px] tracking-[0.3em] uppercase hover:scale-105 active:scale-95 transition-all shadow-2xl shadow-primary/40 border-b-4 border-primary-foreground/20">
                               + NUEVA GESTIÓN
                            </Button>
                         </div>
                      </div>

                      <div className="bg-white/[0.01] rounded-[3.5rem] border border-white/5 overflow-hidden shadow-[0_0_100px_rgba(0,0,0,0.5)]">
                         <div className="grid grid-cols-[1fr_180px_120px_160px] gap-10 px-12 py-8 border-b border-white/10 text-[12px] font-black uppercase text-gray-500 tracking-[0.5em] bg-white/[0.02]">
                            <div>Detalle de Actividad</div>
                            <div className="text-center">Responsable</div>
                            <div className="text-center">Prioridad</div>
                            <div className="text-right">Vencimiento</div>
                         </div>
                         <div className="divide-y divide-white/5">
                            {displayTask.subtasks?.length ? (
                               displayTask.subtasks.map(st => (
                                 <div key={st.id} className="grid grid-cols-[1fr_180px_120px_160px] gap-10 px-12 py-8 hover:bg-white/[0.05] transition-all cursor-pointer group text-[17px] border-l-4 border-transparent hover:border-primary">
                                    <div className="flex items-center gap-6 text-gray-100">
                                       <div className={cn("h-7 w-7 rounded-lg border-2 border-gray-700 flex items-center justify-center transition-all group-hover:border-primary shadow-2xl", ['completado', 'closed', 'done'].includes(st.status?.toLowerCase() || '') && 'bg-[#2da44e] border-[#2da44e]')}>
                                          {['completado', 'closed', 'done'].includes(st.status?.toLowerCase() || '') && <Check className="h-4 w-4 text-white" />}
                                       </div>
                                       <span className={cn("font-black tracking-tight", ['completado', 'closed', 'done'].includes(st.status?.toLowerCase() || '') && "line-through text-gray-700 opacity-50")}>{st.title}</span>
                                    </div>
                                    <div className="flex justify-center items-center">
                                       <div className="h-11 w-11 rounded-2xl bg-primary/10 border-2 border-primary/20 flex items-center justify-center text-[14px] font-black text-primary shadow-2xl group-hover:bg-primary group-hover:text-white transition-all">{st.assignee_name?.[0] || 'U'}</div>
                                    </div>
                                    <div className="flex justify-center items-center">
                                       <Flag className={`h-7 w-7 ${st.priority === 'high' ? 'text-red-500 drop-shadow-[0_0_12px_rgba(239,68,68,0.7)]' : 'text-gray-800 group-hover:text-gray-600'}`} />
                                    </div>
                                    <div className="text-right text-[14px] font-black text-[#2da44e] tracking-tighter uppercase drop-shadow-[0_0_5px_rgba(45,164,78,0.3)]">
                                       {st.due_date ? format(parseISO(st.due_date.toString()), 'd MMM, yyyy') : '-'}
                                    </div>
                                 </div>
                               ))
                            ) : (
                               <div className="p-24 text-center space-y-6">
                                  <Activity className="h-20 w-20 mx-auto text-gray-900 animate-pulse" />
                                  <p className="text-gray-800 italic font-black text-[14px] tracking-[0.5em] uppercase">No hay gestiones técnicas sincronizadas para este radicado</p>
                                  <Button variant="link" onClick={refreshTask} className="text-primary font-black uppercase tracking-widest text-[11px] underline">Forzar sincronización con ClickUp</Button>
                               </div>
                            )}
                         </div>
                      </div>
                      
                      {showSubtaskForm && (
                        <div className="p-12 bg-white/[0.02] border-2 border-primary/30 rounded-[4rem] space-y-10 shadow-[0_0_150px_rgba(0,188,212,0.1)] animate-in fade-in zoom-in-95 duration-500 ring-8 ring-primary/5">
                           <div className="grid grid-cols-1 lg:grid-cols-4 gap-10">
                              <div className="lg:col-span-2 space-y-4">
                                 <label className="text-[12px] font-black text-primary uppercase ml-6 tracking-[0.4em]">Actividad Técnica</label>
                                 <Input placeholder="Ej: Radicación de demanda ejecutiva..." value={newSubtaskTitle} onChange={(e) => setNewSubtaskTitle(e.target.value)} className="bg-black/80 border-white/10 h-16 rounded-[2rem] px-8 text-[16px] font-black text-white shadow-2xl focus:border-primary/60 transition-all" />
                              </div>
                              <div className="space-y-4">
                                 <label className="text-[12px] font-black text-primary uppercase ml-6 tracking-[0.4em]">Término</label>
                                 <Input type="date" value={newSubtaskDate} onChange={(e) => setNewSubtaskDate(e.target.value)} className="bg-black/80 border-white/10 h-16 rounded-[2rem] px-8 text-[16px] font-black text-white shadow-2xl focus:border-primary/60 transition-all" />
                              </div>
                              <div className="space-y-4">
                                 <label className="text-[12px] font-black text-primary uppercase ml-6 tracking-[0.4em]">Prioridad</label>
                                 <Select value={newSubtaskPriority} onValueChange={setNewSubtaskPriority}>
                                    <SelectTrigger className="bg-black/80 border-white/10 h-16 rounded-[2rem] px-8 text-[16px] font-black text-white shadow-2xl border-2">
                                       <SelectValue placeholder="Normal" />
                                    </SelectTrigger>
                                    <SelectContent className="bg-[#1e1e1e] border-white/10 text-white rounded-2xl">
                                       <SelectItem value="low">Baja</SelectItem>
                                       <SelectItem value="normal">Normal</SelectItem>
                                       <SelectItem value="high">Alta</SelectItem>
                                       <SelectItem value="urgent">Urgente</SelectItem>
                                    </SelectContent>
                                 </Select>
                              </div>
                           </div>
                           <div className="flex items-center gap-10 pt-4">
                              <div className="flex-1 space-y-4">
                                 <label className="text-[12px] font-black text-primary uppercase ml-6 tracking-[0.4em]">Asignación de Abogado</label>
                                 <Select value={newSubtaskAssigneeId?.toString()} onValueChange={(v) => setNewSubtaskAssigneeId(parseInt(v))}>
                                    <SelectTrigger className="bg-black/80 border-white/10 h-16 rounded-[2rem] px-8 text-[16px] font-black text-white shadow-2xl border-2">
                                       <SelectValue placeholder="Seleccionar del despacho..." />
                                    </SelectTrigger>
                                    <SelectContent className="bg-[#1e1e1e] border-white/10 text-white rounded-2xl">
                                       {users.map(u => <SelectItem key={u.id} value={u.id.toString()}>{u.nombre || u.username}</SelectItem>)}
                                    </SelectContent>
                                 </Select>
                              </div>
                              <div className="flex items-end gap-6 pt-10 h-full">
                                 <Button variant="ghost" onClick={() => setShowSubtaskForm(false)} className="h-16 px-10 rounded-[2rem] text-[13px] font-black uppercase tracking-[0.3em] text-gray-600 hover:text-white transition-all">Descartar</Button>
                                 <Button onClick={handleCreateSubtask} className="h-16 px-16 rounded-[2.5rem] bg-primary text-white font-black text-[14px] uppercase tracking-[0.4em] shadow-2xl shadow-primary/50 hover:scale-105 active:scale-95 transition-all">VINCULAR GESTIÓN</Button>
                              </div>
                           </div>
                        </div>
                      )}
                   </div>
                </div>
             </ScrollArea>
          </div>

          {/* ACTIVITY PANEL (40%) */}
          <div className="flex-1 flex flex-col bg-[#0a0a0a] border-l border-white/5 shadow-[0_0_150px_rgba(0,0,0,1)] overflow-hidden">
             <div className="h-24 flex items-center justify-between px-12 border-b border-white/5 bg-white/[0.02]">
                <div className="flex items-center gap-4">
                   <Activity className="h-6 w-6 text-primary animate-pulse" />
                   <span className="text-[15px] font-black uppercase tracking-[0.5em] text-gray-500">Activity & Timeline</span>
                </div>
                <div className="flex items-center gap-8 text-gray-600">
                   <Settings className="h-6 w-6 hover:text-white cursor-pointer transition-all" />
                </div>
             </div>

             <ScrollArea className="flex-1 px-12 py-12">
                <div className="space-y-16">
                   {displayTask.comments?.map(comment => (
                     <div key={comment.id} className="group relative">
                        <div className="flex items-center gap-5 text-[14px] mb-5">
                           <div className="h-11 w-11 rounded-[1.2rem] bg-primary/10 flex items-center justify-center text-[16px] font-black text-primary border-2 border-primary/20 shadow-2xl group-hover:bg-primary group-hover:text-white transition-all">
                              {comment.user_name?.[0] || 'U'}
                           </div>
                           <div className="flex flex-col">
                              <span className="text-gray-200 font-black uppercase tracking-[0.2em] text-[13px]">{(comment.user_name || 'Personal EMDECOB')}</span>
                              <span className="text-gray-700 text-[11px] font-bold tracking-widest">{isValid(parseISO(comment.created_at.toString())) ? format(parseISO(comment.created_at.toString()), "d MMM 'a las' p", { locale: es }) : ''}</span>
                           </div>
                        </div>
                        
                        <div className="p-9 bg-white/[0.03] border border-white/5 rounded-[3rem] rounded-tl-none text-[17px] font-medium text-gray-300 leading-relaxed shadow-2xl group-hover:bg-white/[0.05] transition-all relative border-l-4 border-l-primary/20 hover:border-l-primary">
                           {editingCommentId === comment.id ? (
                             <div className="space-y-6">
                                <Textarea value={editingCommentText} onChange={(e) => setEditingCommentText(e.target.value)} className="bg-black/60 border-primary/50 text-base min-h-[150px] rounded-[2rem] p-7 shadow-inner font-medium text-white" />
                                <div className="flex justify-end gap-5">
                                   <Button variant="ghost" onClick={() => setEditingCommentId(null)} className="h-12 px-8 rounded-2xl text-[12px] font-black uppercase text-gray-600 tracking-widest">Cancelar</Button>
                                   <Button onClick={() => handleUpdateComment(comment.id)} className="h-12 px-10 rounded-2xl bg-primary text-white font-black text-[12px] uppercase tracking-widest shadow-2xl shadow-primary/30">ACTUALIZAR REGISTRO</Button>
                               </div>
                             </div>
                           ) : (
                             <>
                               {comment.content}
                               <div className="absolute top-6 right-8 opacity-0 group-hover:opacity-100 transition-all flex gap-4">
                                  <Button variant="ghost" size="icon" onClick={() => { setEditingCommentId(comment.id); setEditingCommentText(comment.content); }} className="h-10 w-10 rounded-2xl bg-black/80 flex items-center justify-center hover:text-primary border border-white/10 shadow-2xl"><Edit3 className="h-5 w-5" /></Button>
                                  <Button variant="ghost" size="icon" onClick={() => handleDeleteComment(comment.id)} className="h-10 w-10 rounded-2xl bg-black/80 flex items-center justify-center hover:text-red-500 border border-white/10 shadow-2xl"><Trash2 className="h-5 w-5" /></Button>
                               </div>
                               <div className="mt-8 pt-6 border-t border-white/5 flex items-center gap-10 text-gray-600 text-[13px] font-black uppercase tracking-[0.3em]">
                                  <div className="flex items-center gap-3 hover:text-white cursor-pointer transition-all"><Smile className="h-6 w-6" /> Reacción</div>
                                  <div className="hover:text-white cursor-pointer transition-all">Hilo Judicial</div>
                               </div>
                             </>
                           )}
                        </div>
                     </div>
                   ))}
                   {(!displayTask.comments || displayTask.comments.length === 0) && (
                      <div className="p-40 text-center space-y-8 opacity-5">
                         <MessageSquare className="h-32 w-32 mx-auto text-gray-500" />
                         <p className="text-[14px] font-black uppercase tracking-[0.8em]">Silencio Procesal</p>
                      </div>
                   )}
                </div>
             </ScrollArea>

             <div className="p-12 bg-[#0a0a0a] border-t border-white/10">
                <div className="bg-[#111111] border-2 border-white/5 rounded-[3.5rem] p-10 space-y-8 shadow-[0_0_100px_rgba(0,0,0,0.5)] focus-within:border-primary/50 focus-within:shadow-[0_0_100px_rgba(0,188,212,0.1)] transition-all">
                   <Textarea 
                     value={newComment}
                     onChange={(e) => setNewComment(e.target.value)}
                     placeholder="Añade una nota técnica al expediente..."
                     className="bg-transparent border-none focus:ring-0 p-0 text-[18px] min-h-[120px] resize-none text-gray-100 font-medium placeholder:text-gray-900"
                   />
                   <div className="flex items-center justify-between">
                      <div className="flex items-center gap-8 text-gray-600">
                         <AttachmentIcon className="h-7 w-7 hover:text-white cursor-pointer transition-all hover:scale-125" />
                         <Zap className="h-7 w-7 text-purple-500 hover:scale-125 cursor-pointer" />
                         <Smile className="h-7 w-7 hover:text-white cursor-pointer transition-all hover:scale-125" />
                         <div className="flex items-center gap-4 px-6 py-3 bg-white/5 rounded-2xl hover:bg-white/10 cursor-pointer text-[13px] font-black uppercase tracking-[0.2em] border border-white/10 transition-all shadow-inner">
                            <MessageCircle className="h-6 w-6 text-primary" /> NOTA TÉCNICA
                         </div>
                      </div>
                      <Button size="icon" onClick={handleAddComment} disabled={!newComment.trim()} className={cn("h-16 w-16 rounded-[2rem] shadow-[0_20px_50px_rgba(0,188,212,0.3)] transition-all transform hover:rotate-6", newComment.trim() ? "bg-primary text-white scale-110" : "bg-gray-950 text-gray-900 opacity-20")}>
                        <Send className="h-8 w-8" />
                      </Button>
                   </div>
                </div>
             </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(" ");
}
