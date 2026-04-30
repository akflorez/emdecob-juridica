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
      // Convert dates to ISO format if present
      const cleanedUpdates = { ...updates };
      if (cleanedUpdates.due_date && typeof cleanedUpdates.due_date === 'string') {
        cleanedUpdates.due_date = new Date(cleanedUpdates.due_date).toISOString();
      }

      const updated = await updateTask(displayTask.id, cleanedUpdates);
      onTaskUpdate(updated);
      setFullTask(updated);
    } catch (error) {
      toast({ title: "Sincronización interrumpida", description: "Verifica tu conexión con el servidor judicial.", variant: "destructive" });
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
      toast({ title: "Error al publicar nota" });
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
    if (!confirm("¿Eliminar este registro de actividad?")) return;
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
      // Ensure date is ISO
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
      toast({ title: "Gestión técnica creada" });
    } catch (error) {
      toast({ title: "Error al crear gestión", description: "Verifica que todos los campos sean válidos.", variant: "destructive" });
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
      <SheetContent className="sm:max-w-[1350px] p-0 bg-[#111111] border-none text-[#d1d1d1] flex flex-col shadow-2xl font-sans outline-none">
        <SheetHeader className="sr-only"><SheetTitle>Consola Judicial ClickUp V3</SheetTitle></SheetHeader>
        
        <div className="flex flex-1 overflow-hidden h-full">
          {/* MAIN PANEL (50%) */}
          <div className="flex-1 flex flex-col overflow-hidden bg-[#111111]">
             <ScrollArea className="flex-1 px-12 pt-8 pb-20">
                <div className="space-y-10 max-w-[900px] mx-auto">
                   
                   {/* Top Header */}
                   <div className="flex items-center justify-between text-[11px] font-bold text-gray-500 uppercase tracking-widest">
                      <div className="flex items-center gap-3">
                         <div className="flex items-center gap-2 px-3 py-1 bg-white/[0.03] rounded border border-white/5">
                            <Badge className="h-4 w-4 p-0 bg-[#2da44e] flex items-center justify-center rounded-sm"><Check className="h-3 w-3 text-white" /></Badge>
                            <span className="text-gray-300">Expediente Judicial</span>
                            <ChevronDown className="h-3.5 w-3.5" />
                         </div>
                         <span className="text-primary tracking-[0.3em] font-black">{displayTask.clickup_id || displayTask.id}</span>
                      </div>
                      <div className="flex items-center gap-4">
                         <Button variant="ghost" size="sm" onClick={refreshTask} disabled={isLoading} className="text-gray-400 hover:text-white gap-2 font-black text-[10px] tracking-widest">
                            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} /> SINCRONIZAR
                         </Button>
                         <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="h-10 w-10 text-gray-500 hover:text-white">
                           <X className="h-7 w-7" />
                         </Button>
                      </div>
                   </div>

                   {/* Title */}
                   <input 
                     className="w-full bg-transparent text-4xl font-black tracking-tight border-none focus:ring-0 p-0 text-white placeholder:text-gray-800"
                     value={editedTitle}
                     onChange={(e) => setEditedTitle(e.target.value)}
                     onBlur={() => handleSave({ title: editedTitle })}
                   />

                   {/* Metadata Horizontal Strip */}
                   <div className="flex flex-wrap items-center gap-x-12 gap-y-8 py-8 border-b border-white/5">
                      {/* Estado */}
                      <div className="flex flex-col gap-3 min-w-[170px]">
                         <span className="text-[10px] text-gray-600 font-black uppercase tracking-[0.3em] flex items-center gap-2"><Activity className="h-4 w-4" /> Estado Procesal</span>
                         <Select value={statusOptions.includes(currentStatus) ? currentStatus : undefined} onValueChange={(v) => handleSave({ status: v })}>
                            <SelectTrigger className="h-11 w-full bg-[#2da44e] hover:bg-[#34bc5a] text-white text-[12px] font-black uppercase rounded-xl border-none px-5 transition-all shadow-xl">
                               <SelectValue placeholder={currentStatus} />
                            </SelectTrigger>
                            <SelectContent className="bg-[#1e1e1e] border-white/10 text-white shadow-2xl rounded-xl">
                               {statusOptions.map(s => (
                                 <SelectItem key={s} value={s} className="uppercase text-[12px] font-black py-3 tracking-widest">{s}</SelectItem>
                               ))}
                            </SelectContent>
                         </Select>
                      </div>

                      {/* Abogados */}
                      <div className="flex flex-col gap-3 min-w-[220px]">
                         <span className="text-[10px] text-gray-600 font-black uppercase tracking-[0.3em] flex items-center gap-2"><UserIcon className="h-4 w-4" /> Abogado Responsable</span>
                         <Popover>
                            <PopoverTrigger asChild>
                               <Button variant="outline" className="h-11 w-full bg-white/[0.02] border-white/10 rounded-xl flex items-center justify-start gap-4 px-4 hover:bg-white/5 transition-all group shadow-inner">
                                  <div className="flex -space-x-2.5">
                                     {displayTask.assignees?.length ? (
                                        displayTask.assignees.map(a => (
                                          <div key={a.id} className="h-8 w-8 rounded-full bg-gradient-to-br from-[#ff7b72] to-[#f85149] border-2 border-[#111] flex items-center justify-center text-[12px] font-black text-white shadow-lg">{a.nombre?.[0] || a.username[0]}</div>
                                        ))
                                     ) : (
                                        <div className="h-8 w-8 rounded-full border-2 border-dashed border-gray-700 bg-gray-900 flex items-center justify-center text-gray-700"><UserIcon className="h-4 w-4" /></div>
                                     )}
                                  </div>
                                  <span className="text-[13px] font-black text-gray-200 truncate group-hover:text-primary transition-colors">
                                     {displayTask.assignees?.length ? displayTask.assignees.map(a => a.nombre || a.username).join(', ') : (displayTask.assignee_name || 'Asignar Abogado')}
                                  </span>
                               </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-80 p-3 bg-[#1e1e1e] border-white/10 text-white rounded-2xl shadow-2xl">
                               <ScrollArea className="h-[350px]">
                                  <div className="p-3 border-b border-white/5 mb-3 text-[10px] font-black uppercase text-gray-500 tracking-widest text-center">Equipo de Despacho</div>
                                  <div className="space-y-1">
                                    {users.map(u => (
                                      <div key={u.id} className="flex items-center justify-between p-3.5 hover:bg-white/10 rounded-xl cursor-pointer transition-all border border-transparent hover:border-white/5" onClick={() => toggleAssignee(u.id)}>
                                         <div className="flex flex-col">
                                            <span className="text-[14px] font-bold text-gray-200">{u.nombre || u.username}</span>
                                            <span className="text-[10px] text-gray-500 font-black uppercase">Jurídico</span>
                                         </div>
                                         <Checkbox checked={displayTask.assignees?.some(a => a.id === u.id)} className="h-6 w-6 border-white/20 data-[state=checked]:bg-primary" />
                                      </div>
                                    ))}
                                    {users.length === 0 && <div className="p-10 text-center italic text-gray-600 text-xs">No hay abogados registrados en el sistema.</div>}
                                  </div>
                               </ScrollArea>
                            </PopoverContent>
                         </Popover>
                      </div>

                      {/* Fecha Límite */}
                      <div className="flex flex-col gap-3 min-w-[190px]">
                         <span className="text-[10px] text-gray-600 font-black uppercase tracking-[0.3em] flex items-center gap-2"><CalendarIcon className="h-4 w-4" /> Vencimiento</span>
                         <div className="h-11 bg-white/[0.02] border border-white/10 rounded-xl flex items-center gap-4 px-5 hover:border-white/20 transition-all shadow-inner">
                            <input 
                              type="date" 
                              className="bg-transparent border-none focus:ring-0 text-[13px] font-black uppercase text-gray-200 p-0 w-full cursor-pointer"
                              value={editedDueDate}
                              onChange={(e) => {
                                setEditedDueDate(e.target.value);
                                handleSave({ due_date: e.target.value } as any);
                              }}
                            />
                         </div>
                      </div>

                      {/* Etiquetas Strip */}
                      <div className="flex flex-col gap-3 min-w-[220px]">
                         <span className="text-[10px] text-gray-600 font-black uppercase tracking-[0.3em] flex items-center gap-2"><Tag className="h-4 w-4" /> Clasificación</span>
                         <Popover>
                            <PopoverTrigger asChild>
                               <Button variant="outline" className="h-11 w-full bg-white/[0.02] border-white/10 rounded-xl flex flex-wrap gap-2 px-4 hover:bg-white/5 transition-all justify-start overflow-hidden py-2 shadow-inner">
                                  {displayTask.tags?.length ? (
                                    displayTask.tags.map(t => (
                                      <Badge key={t.id} style={{ backgroundColor: t.color || '#3b82f6', color: '#fff' }} className="h-6 text-[10px] font-black px-3 rounded-md border-none shadow-lg">
                                         {t.name}
                                      </Badge>
                                    ))
                                  ) : (
                                    <span className="text-[12px] text-gray-700 font-bold tracking-widest">+ ETIQUETAS</span>
                                  )}
                               </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-80 p-4 bg-[#1e1e1e] border-white/10 text-white rounded-2xl shadow-2xl">
                               <ScrollArea className="h-[300px]">
                                  <div className="p-2 border-b border-white/5 mb-4 text-[10px] font-black uppercase text-gray-500 tracking-widest text-center">Tags Maestros</div>
                                  <div className="grid grid-cols-1 gap-2">
                                    {allTags.map(t => (
                                      <div key={t.id} className="flex items-center justify-between p-3.5 hover:bg-white/10 rounded-xl cursor-pointer transition-all border border-transparent hover:border-white/5" onClick={() => toggleTag(t.name)}>
                                         <div className="flex items-center gap-3">
                                            <div className="h-4 w-4 rounded-full shadow-lg ring-2 ring-white/10" style={{ backgroundColor: t.color || '#3b82f6' }} />
                                            <span className="text-sm font-bold text-gray-200">{t.name}</span>
                                         </div>
                                         {displayTask.tags?.some(gt => gt.name === t.name) && <CheckCircle2 className="h-5 w-5 text-[#2da44e]" />}
                                      </div>
                                    ))}
                                  </div>
                               </ScrollArea>
                            </PopoverContent>
                         </Popover>
                      </div>
                   </div>

                   {/* Description Area */}
                   <div className="space-y-4 pt-4">
                      <div className="flex items-center gap-3 text-gray-700 italic text-[12px] font-bold tracking-widest uppercase">
                         <Activity className="h-4 w-4 text-primary opacity-50" /> Bitácora de Actuaciones Jurídicas
                      </div>
                      <Textarea 
                        className="min-h-[220px] bg-white/[0.01] border-none p-8 text-[16px] leading-relaxed text-gray-200 focus:ring-0 placeholder:text-gray-800 transition-all shadow-inner font-medium"
                        placeholder="Escribe los avances procesales aquí..."
                        value={editedDesc}
                        onChange={(e) => setEditedDesc(e.target.value)}
                        onBlur={() => handleSave({ description: editedDesc })}
                      />
                   </div>

                   {/* Subtasks (Gestiones) Section */}
                   <div className="space-y-8 pt-10 border-t border-white/5">
                      <div className="flex items-center justify-between">
                         <div className="flex items-center gap-6">
                            <div className="flex items-center gap-3 text-gray-400 font-black text-[15px] uppercase tracking-[0.3em]">
                               <ChevronDown className="h-6 w-6" /> Gestiones Técnicas
                            </div>
                            <div className="flex items-center gap-4 text-[12px] text-gray-500 font-black tracking-widest bg-white/[0.03] px-5 py-2 rounded-full border border-white/5">
                               <span>{doneSub}/{totalSub} FINALIZADAS</span>
                               <Progress value={progressSub} className="w-40 h-2 bg-gray-900" />
                            </div>
                         </div>
                         <div className="flex items-center gap-4">
                            <Button variant="ghost" size="icon" onClick={refreshTask} className="text-gray-600 hover:text-white"><RefreshCw className={cn("h-5 w-5", isLoading && "animate-spin")} /></Button>
                            <Button size="sm" onClick={() => setShowSubtaskForm(true)} className="h-10 px-6 rounded-xl bg-primary/10 text-primary font-black text-[11px] tracking-widest border border-primary/20 hover:bg-primary hover:text-white transition-all shadow-xl">
                               + NUEVA GESTIÓN
                            </Button>
                         </div>
                      </div>

                      <div className="bg-white/[0.01] rounded-[2.5rem] border border-white/5 overflow-hidden shadow-2xl">
                         <div className="grid grid-cols-[1fr_160px_100px_140px] gap-8 px-10 py-5 border-b border-white/5 text-[11px] font-black uppercase text-gray-600 tracking-[0.4em] bg-white/[0.02]">
                            <div>Descripción de Gestión</div>
                            <div className="text-center">Responsable</div>
                            <div className="text-center">Prioridad</div>
                            <div className="text-right">Vencimiento</div>
                         </div>
                         <div className="divide-y divide-white/5">
                            {displayTask.subtasks?.length ? (
                               displayTask.subtasks.map(st => (
                                 <div key={st.id} className="grid grid-cols-[1fr_160px_100px_140px] gap-8 px-10 py-6 hover:bg-white/[0.04] transition-all cursor-pointer group text-[15px]">
                                    <div className="flex items-center gap-5 text-gray-100">
                                       <div className={cn("h-6 w-6 rounded-full border-2 border-gray-700 flex items-center justify-center transition-all", ['completado', 'closed', 'done'].includes(st.status?.toLowerCase() || '') && 'bg-[#2da44e] border-[#2da44e]')}>
                                          {['completado', 'closed', 'done'].includes(st.status?.toLowerCase() || '') && <Check className="h-3.5 w-3.5 text-white" />}
                                       </div>
                                       <span className={cn("font-bold tracking-tight", ['completado', 'closed', 'done'].includes(st.status?.toLowerCase() || '') && "line-through text-gray-600")}>{st.title}</span>
                                    </div>
                                    <div className="flex justify-center items-center">
                                       <div className="h-9 w-9 rounded-full bg-primary/20 border-2 border-primary/30 flex items-center justify-center text-[12px] font-black text-primary shadow-xl">{st.assignee_name?.[0] || 'U'}</div>
                                    </div>
                                    <div className="flex justify-center items-center">
                                       <Flag className={`h-6 w-6 ${st.priority === 'high' ? 'text-red-500 drop-shadow-[0_0_8px_rgba(239,68,68,0.5)]' : 'text-gray-700'}`} />
                                    </div>
                                    <div className="text-right text-[13px] font-black text-[#2da44e] tracking-tight uppercase">
                                       {st.due_date ? format(parseISO(st.due_date.toString()), 'd MMM, yyyy') : '-'}
                                    </div>
                                 </div>
                               ))
                            ) : (
                               <div className="p-16 text-center text-gray-700 italic font-bold tracking-widest uppercase">No hay gestiones técnicas para este expediente en el sistema local.</div>
                            )}
                         </div>
                      </div>
                      
                      {showSubtaskForm && (
                        <div className="p-10 bg-primary/5 border-2 border-primary/20 rounded-[3rem] space-y-8 shadow-2xl animate-in fade-in zoom-in duration-300">
                           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                              <div className="lg:col-span-2 space-y-3">
                                 <label className="text-[11px] font-black text-primary uppercase ml-4 tracking-widest">Actividad Procesal</label>
                                 <Input placeholder="Ej: Radicar memorial..." value={newSubtaskTitle} onChange={(e) => setNewSubtaskTitle(e.target.value)} className="bg-black/60 border-white/10 h-14 rounded-2xl px-6 text-[14px] font-bold text-white shadow-inner focus:border-primary/50" />
                              </div>
                              <div className="space-y-3">
                                 <label className="text-[11px] font-black text-primary uppercase ml-4 tracking-widest">Fecha Límite</label>
                                 <Input type="date" value={newSubtaskDate} onChange={(e) => setNewSubtaskDate(e.target.value)} className="bg-black/60 border-white/10 h-14 rounded-2xl px-6 text-[14px] font-bold text-white shadow-inner focus:border-primary/50" />
                              </div>
                              <div className="space-y-3">
                                 <label className="text-[11px] font-black text-primary uppercase ml-4 tracking-widest">Prioridad</label>
                                 <Select value={newSubtaskPriority} onValueChange={setNewSubtaskPriority}>
                                    <SelectTrigger className="bg-black/60 border-white/10 h-14 rounded-2xl px-6 text-[14px] font-bold text-white shadow-inner">
                                       <SelectValue placeholder="Normal" />
                                    </SelectTrigger>
                                    <SelectContent className="bg-[#1e1e1e] border-white/10 text-white rounded-xl">
                                       <SelectItem value="low">Baja</SelectItem>
                                       <SelectItem value="normal">Normal</SelectItem>
                                       <SelectItem value="high">Alta</SelectItem>
                                       <SelectItem value="urgent">Urgente</SelectItem>
                                    </SelectContent>
                                 </Select>
                              </div>
                           </div>
                           <div className="flex items-center gap-8 pt-4">
                              <div className="flex-1 space-y-3">
                                 <label className="text-[11px] font-black text-primary uppercase ml-4 tracking-widest">Abogado Responsable</label>
                                 <Select value={newSubtaskAssigneeId?.toString()} onValueChange={(v) => setNewSubtaskAssigneeId(parseInt(v))}>
                                    <SelectTrigger className="bg-black/60 border-white/10 h-14 rounded-2xl px-6 text-[14px] font-bold text-white shadow-inner">
                                       <SelectValue placeholder="Seleccionar de la lista..." />
                                    </SelectTrigger>
                                    <SelectContent className="bg-[#1e1e1e] border-white/10 text-white rounded-xl">
                                       {users.map(u => <SelectItem key={u.id} value={u.id.toString()}>{u.nombre || u.username}</SelectItem>)}
                                    </SelectContent>
                                 </Select>
                              </div>
                              <div className="flex items-end gap-5 pt-8 h-full">
                                 <Button variant="ghost" onClick={() => setShowSubtaskForm(false)} className="h-14 px-8 rounded-2xl text-[12px] font-black uppercase tracking-widest text-gray-500">Cancelar</Button>
                                 <Button onClick={handleCreateSubtask} className="h-14 px-12 rounded-2xl bg-primary text-white font-black text-[12px] uppercase tracking-widest shadow-2xl shadow-primary/30">CREAR GESTIÓN</Button>
                              </div>
                           </div>
                        </div>
                      )}
                   </div>

                   {/* Checklist Area */}
                   <div className="space-y-8 pt-10 border-t border-white/5">
                      <div className="flex items-center gap-3 text-gray-400 font-black text-[15px] uppercase tracking-[0.3em]">
                         <ChevronDown className="h-6 w-6" /> Lista de Pasos Rápidos
                      </div>
                      <div className="px-10 space-y-4">
                         {displayTask.checklists?.map(item => (
                           <div key={item.id} className="flex items-center gap-6 py-4 group hover:bg-white/[0.03] px-6 rounded-[1.5rem] transition-all border border-transparent hover:border-white/5 shadow-xl">
                              <Checkbox 
                                checked={item.is_completed} 
                                onCheckedChange={(v) => updateChecklistItem(item.id, { is_completed: !!v }).then(refreshTask)} 
                                className="h-6 w-6 border-gray-600 data-[state=checked]:bg-primary" 
                              />
                              <span className={cn("text-[15px] flex-1 font-bold tracking-tight", item.is_completed ? "line-through text-gray-700 italic" : "text-gray-200")}>
                                {item.content}
                              </span>
                              <Button variant="ghost" size="icon" onClick={() => deleteChecklistItem(item.id).then(refreshTask)} className="h-10 w-10 text-gray-700 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all rounded-xl">
                                 <Trash2 className="h-5 w-5" />
                              </Button>
                           </div>
                         ))}
                         <div className="flex items-center gap-6 py-5 px-6 bg-white/[0.01] border-2 border-dashed border-white/5 rounded-[1.5rem] group hover:border-primary/40 transition-all">
                            <Plus className="h-6 w-6 text-gray-800 group-hover:text-primary" />
                            <Input 
                               placeholder="Añadir paso rápido..." 
                               value={newChecklist} 
                               onChange={(e) => setNewChecklist(e.target.value)} 
                               onKeyDown={(e) => e.key === 'Enter' && handleAddChecklist()} 
                               className="bg-transparent border-none p-0 text-[15px] font-bold focus:ring-0 text-gray-300"
                            />
                            <Button variant="ghost" onClick={handleAddChecklist} className="h-10 px-6 rounded-xl text-[11px] font-black uppercase text-primary tracking-widest hover:bg-primary/10 transition-all">AÑADIR</Button>
                         </div>
                      </div>
                   </div>
                </div>
             </ScrollArea>
          </div>

          {/* RIGHT PANEL (ACTIVITY LOG - 50%) */}
          <div className="flex-1 flex flex-col bg-[#111111] border-l border-white/5 shadow-[0_0_120px_rgba(0,0,0,0.8)] overflow-hidden">
             <div className="h-20 flex items-center justify-between px-10 border-b border-white/5 bg-white/[0.02]">
                <span className="text-[14px] font-black uppercase tracking-[0.4em] text-gray-500">Activity Log & Historial</span>
                <div className="flex items-center gap-6 text-gray-600">
                   <Search className="h-5 w-5 hover:text-white cursor-pointer" />
                   <Settings className="h-5 w-5 hover:text-white cursor-pointer" />
                </div>
             </div>

             <ScrollArea className="flex-1 px-10 py-12">
                <div className="space-y-12">
                   {displayTask.comments?.map(comment => (
                     <div key={comment.id} className="group relative">
                        <div className="flex items-center gap-4 text-[13px] mb-4">
                           <div className="h-9 w-9 rounded-2xl bg-primary/10 flex items-center justify-center text-[14px] font-black text-primary border border-primary/20 shadow-2xl">
                              {comment.user_name?.[0] || 'U'}
                           </div>
                           <div className="flex flex-col">
                              <span className="text-gray-200 font-black uppercase tracking-widest">{(comment.user_name || 'Personal Jurídico')}</span>
                              <span className="text-gray-600 text-[11px] font-bold">{isValid(parseISO(comment.created_at.toString())) ? format(parseISO(comment.created_at.toString()), "d MMM 'a las' p", { locale: es }) : ''}</span>
                           </div>
                        </div>
                        
                        <div className="p-7 bg-white/[0.04] border border-white/5 rounded-[2.5rem] rounded-tl-none text-[16px] font-medium text-gray-300 leading-relaxed shadow-2xl group-hover:bg-white/[0.06] transition-all relative">
                           {editingCommentId === comment.id ? (
                             <div className="space-y-5">
                                <Textarea value={editingCommentText} onChange={(e) => setEditingCommentText(e.target.value)} className="bg-black/60 border-primary/40 text-sm min-h-[120px] rounded-3xl p-5 shadow-inner" />
                                <div className="flex justify-end gap-4">
                                   <Button variant="ghost" onClick={() => setEditingCommentId(null)} className="h-10 px-6 rounded-2xl text-[12px] font-black uppercase text-gray-500 tracking-widest">Cancelar</Button>
                                   <Button onClick={() => handleUpdateComment(comment.id)} className="h-10 px-8 rounded-2xl bg-primary text-white font-black text-[12px] uppercase tracking-widest">GUARDAR CAMBIOS</Button>
                               </div>
                             </div>
                           ) : (
                             <>
                               {comment.content}
                               <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-all flex gap-3">
                                  <Button variant="ghost" size="icon" onClick={() => { setEditingCommentId(comment.id); setEditingCommentText(comment.content); }} className="h-10 w-10 rounded-2xl bg-black/60 flex items-center justify-center hover:text-primary border border-white/5 shadow-2xl"><Edit3 className="h-5 w-5" /></Button>
                                  <Button variant="ghost" size="icon" onClick={() => handleDeleteComment(comment.id)} className="h-10 w-10 rounded-2xl bg-black/60 flex items-center justify-center hover:text-red-500 border border-white/5 shadow-2xl"><Trash2 className="h-5 w-5" /></Button>
                               </div>
                               <div className="mt-6 pt-5 border-t border-white/5 flex items-center gap-8 text-gray-600 text-[12px] font-black uppercase tracking-widest">
                                  <div className="flex items-center gap-3 hover:text-white cursor-pointer transition-all"><Smile className="h-5 w-5" /> Reaccionar</div>
                                  <div className="hover:text-white cursor-pointer transition-all">Responder</div>
                               </div>
                             </>
                           )}
                        </div>
                     </div>
                   ))}
                   {(!displayTask.comments || displayTask.comments.length === 0) && (
                      <div className="p-32 text-center space-y-6 opacity-10">
                         <MessageSquare className="h-24 w-24 mx-auto text-gray-500" />
                         <p className="text-[12px] font-black uppercase tracking-[0.5em]">Sin actividad técnica registrada</p>
                      </div>
                   )}
                </div>
             </ScrollArea>

             <div className="p-10 bg-[#111111] border-t border-white/5">
                <div className="bg-[#1e1e1e] border-2 border-white/10 rounded-[3rem] p-8 space-y-6 shadow-2xl focus-within:border-primary/40 transition-all">
                   <Textarea 
                     value={newComment}
                     onChange={(e) => setNewComment(e.target.value)}
                     placeholder="Añade un comentario al expediente..."
                     className="bg-transparent border-none focus:ring-0 p-0 text-[16px] min-h-[100px] resize-none text-gray-200 font-medium placeholder:text-gray-800"
                   />
                   <div className="flex items-center justify-between">
                      <div className="flex items-center gap-6 text-gray-600">
                         <AttachmentIcon className="h-6 w-6 hover:text-white cursor-pointer transition-all" />
                         <Zap className="h-6 w-6 text-purple-400" />
                         <Smile className="h-6 w-6 hover:text-white cursor-pointer transition-all" />
                         <div className="flex items-center gap-3 px-5 py-2 bg-white/5 rounded-xl hover:bg-white/10 cursor-pointer text-[12px] font-black uppercase tracking-widest border border-white/5 transition-all">
                            <MessageCircle className="h-5 w-5" /> Comentario
                         </div>
                      </div>
                      <Button size="icon" onClick={handleAddComment} disabled={!newComment.trim()} className={cn("h-14 w-14 rounded-3xl shadow-2xl shadow-primary/40 transition-all", newComment.trim() ? "bg-primary text-white scale-105" : "bg-gray-800 text-gray-700")}>
                        <Send className="h-7 w-7" />
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
