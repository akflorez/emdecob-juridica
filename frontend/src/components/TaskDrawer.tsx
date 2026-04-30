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
import { format, isValid } from "date-fns";
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
  
  const [showSubtaskForm, setShowSubtaskForm] = useState(false);
  const [newSubtaskTitle, setNewSubtaskTitle] = useState("");
  const [newSubtaskDate, setNewSubtaskDate] = useState("");

  const [editingCommentId, setEditingCommentId] = useState<number | null>(null);
  const [editingCommentText, setEditingCommentText] = useState("");

  const displayTask = fullTask || task;

  useEffect(() => {
    if (task && open) {
      setEditedTitle(task.title || '');
      setEditedDesc(task.description || '');
      setEditedDueDate(task.due_date ? format(new Date(task.due_date), 'yyyy-MM-dd') : '');
      refreshTask();
      
      getUsers().then(res => setUsers(Array.isArray(res) ? res : [])).catch(console.error);
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
      if (detail) setFullTask(detail);
    } catch (error) {
      console.error("Error refreshing task", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async (updates: Partial<TaskType>) => {
    if (!displayTask) return;
    try {
      const updated = await updateTask(displayTask.id, updates);
      onTaskUpdate(updated);
      setFullTask(updated);
    } catch (error) {
      toast({ title: "Error al actualizar", variant: "destructive" });
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
      toast({ title: "Error al comentar" });
    }
  };

  const handleUpdateComment = async (id: number) => {
    if (!editingCommentText.trim()) return;
    try {
      await updateComment(id, editingCommentText);
      setEditingCommentId(null);
      refreshTask();
    } catch (error) {
      toast({ title: "Error" });
    }
  };

  const handleDeleteComment = async (id: number) => {
    if (!confirm("¿Borrar comentario?")) return;
    try {
      await deleteComment(id);
      refreshTask();
    } catch (error) {
      toast({ title: "Error" });
    }
  };

  const handleCreateSubtask = async () => {
    if (!displayTask || !newSubtaskTitle.trim()) return;
    try {
      await createTask({
        title: newSubtaskTitle,
        parent_id: displayTask.id,
        due_date: newSubtaskDate || undefined,
        list_id: displayTask.list_id,
        case_id: displayTask.case_id,
        status: 'to do'
      });
      setNewSubtaskTitle("");
      setNewSubtaskDate("");
      setShowSubtaskForm(false);
      refreshTask();
      toast({ title: "Subtarea creada" });
    } catch (error) {
      toast({ title: "Error" });
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
    'ABIERTO', 'TO DO', 'IN PROGRESS', 'PENDIENTE', 'ALMP', '468', 'COMPLETO', 'CLOSED',
    ...(allSystemStatuses || []),
    ...(propStatuses || [])
  ])).filter(Boolean);

  const currentStatus = (displayTask.status || 'ABIERTO').toUpperCase();
  const completedChecklist = displayTask.checklists?.filter(c => c.is_completed).length || 0;
  const totalChecklist = displayTask.checklists?.length || 0;
  const checklistProgress = totalChecklist > 0 ? (completedChecklist / totalChecklist) * 100 : 0;
  
  const completedSubtasks = displayTask.subtasks?.filter(s => s.status?.toLowerCase().includes('completado') || s.status?.toLowerCase() === 'closed').length || 0;
  const totalSubtasks = displayTask.subtasks?.length || 0;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[1300px] p-0 bg-[#111111] border-none text-[#d1d1d1] flex flex-col shadow-2xl font-sans">
        <SheetHeader className="sr-only"><SheetTitle>Consola Jurídica Sync</SheetTitle></SheetHeader>
        
        <div className="flex flex-1 overflow-hidden h-full">
          {/* LEFT: MAIN TASK */}
          <div className="flex-[2.4] flex flex-col overflow-hidden bg-[#111111]">
             <ScrollArea className="flex-1 px-12 pt-8 pb-20">
                <div className="space-y-8 max-w-[1000px] mx-auto">
                   
                   {/* Breadcrumb Row */}
                   <div className="flex items-center justify-between text-[11px]">
                      <div className="flex items-center gap-2">
                         <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[#1a1a1a] rounded hover:bg-[#252525] transition-colors cursor-pointer border border-white/5">
                            <div className="h-4 w-4 bg-[#2da44e] rounded-sm flex items-center justify-center"><Check className="h-3 w-3 text-white" /></div>
                            <span className="text-gray-400 font-bold uppercase tracking-widest text-[10px]">Tarea</span>
                            <ChevronDown className="h-3.5 w-3.5 text-gray-600" />
                         </div>
                         <span className="text-gray-700">/</span>
                         <span className="text-gray-400 font-bold tracking-wider text-[12px]">{displayTask.clickup_id || displayTask.id}</span>
                      </div>
                      <div className="flex items-center gap-4">
                         <RefreshCw className={cn("h-5 w-5 text-gray-500 hover:text-white transition-all cursor-pointer", isLoading && "animate-spin")} onClick={refreshTask} />
                         <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="h-10 w-10 text-gray-500 hover:text-white">
                           <X className="h-6 w-6" />
                         </Button>
                      </div>
                   </div>

                   {/* Title */}
                   <div className="space-y-1">
                      <input 
                        className="w-full bg-transparent text-4xl font-bold tracking-tight border-none focus:ring-0 p-0 text-white placeholder:text-gray-800"
                        value={editedTitle}
                        onChange={(e) => setEditedTitle(e.target.value)}
                        onBlur={() => handleSave({ title: editedTitle })}
                      />
                   </div>

                   {/* AMPLIFIED METADATA BAR (HORIZONTAL) */}
                   <div className="flex flex-wrap items-center gap-x-12 gap-y-6 py-6 border-b border-white/5">
                      {/* Estado */}
                      <div className="flex flex-col gap-2 min-w-[160px]">
                         <div className="text-[10px] text-gray-600 font-black uppercase tracking-[0.2em] flex items-center gap-2">
                            <Activity className="h-3.5 w-3.5" /> Estado
                         </div>
                         <Select value={statusOptions.includes(currentStatus) ? currentStatus : undefined} onValueChange={(v) => handleSave({ status: v })}>
                            <SelectTrigger className="h-10 w-full bg-[#2da44e] hover:bg-[#34bc5a] text-white text-[12px] font-black uppercase rounded-lg border-none px-4 transition-all flex items-center justify-between shadow-xl">
                               <SelectValue placeholder={currentStatus} />
                               <ChevronDown className="h-4 w-4 opacity-70" />
                            </SelectTrigger>
                            <SelectContent className="bg-[#1e1e1e] border-white/10 text-white shadow-2xl">
                               {statusOptions.map(s => (
                                 <SelectItem key={s} value={s} className="uppercase text-[12px] font-black py-3 tracking-widest">{s}</SelectItem>
                               ))}
                            </SelectContent>
                         </Select>
                      </div>

                      {/* Abogados */}
                      <div className="flex flex-col gap-2 min-w-[200px]">
                         <div className="text-[10px] text-gray-600 font-black uppercase tracking-[0.2em] flex items-center gap-2">
                            <UserIcon className="h-3.5 w-3.5" /> Abogado Responsable
                         </div>
                         <Popover>
                            <PopoverTrigger asChild>
                               <Button variant="outline" className="h-10 w-full bg-white/[0.03] border-white/10 rounded-lg flex items-center justify-start gap-3 px-4 hover:bg-white/5 transition-all group">
                                  <div className="flex -space-x-2">
                                     {displayTask.assignees?.map(a => (
                                       <div key={a.id} className="h-7 w-7 rounded-full bg-[#ff7b72] border-2 border-[#111] flex items-center justify-center text-[11px] font-black text-white shadow-lg">{a.nombre?.[0] || a.username[0]}</div>
                                     )) || <div className="h-7 w-7 rounded-full border-2 border-dashed border-gray-700 bg-gray-800" />}
                                  </div>
                                  <span className="text-[12px] font-bold text-gray-200 truncate group-hover:text-primary">
                                     {displayTask.assignees?.length ? displayTask.assignees.map(a => a.nombre || a.username).join(', ') : 'Asignar Abogado'}
                                  </span>
                               </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-80 p-2 bg-[#1e1e1e] border-white/10 text-white rounded-xl shadow-2xl">
                               <ScrollArea className="h-[350px]">
                                  <div className="p-2 border-b border-white/5 mb-2 text-[10px] font-black uppercase text-gray-500">Seleccionar Equipo</div>
                                  {users.map(u => (
                                    <div key={u.id} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-lg cursor-pointer transition-all" onClick={() => toggleAssignee(u.id)}>
                                       <div className="flex flex-col">
                                          <span className="text-sm font-bold text-gray-200">{u.nombre || u.username}</span>
                                          <span className="text-[10px] text-gray-500 font-black uppercase">Jurídico</span>
                                       </div>
                                       {displayTask.assignees?.some(a => a.id === u.id) && <Check className="h-4 w-4 text-[#2da44e]" />}
                                    </div>
                                  ))}
                               </ScrollArea>
                            </PopoverContent>
                         </Popover>
                      </div>

                      {/* Vencimiento */}
                      <div className="flex flex-col gap-2 min-w-[180px]">
                         <div className="text-[10px] text-gray-600 font-black uppercase tracking-[0.2em] flex items-center gap-2">
                            <CalendarIcon className="h-3.5 w-3.5" /> Fecha Límite
                         </div>
                         <div className="h-10 bg-white/[0.03] border border-white/10 rounded-lg flex items-center gap-3 px-4 hover:border-white/20 transition-all cursor-pointer">
                            <input 
                              type="date" 
                              className="bg-transparent border-none focus:ring-0 text-[12px] font-black uppercase text-gray-200 p-0 w-full cursor-pointer"
                              value={editedDueDate}
                              onChange={(e) => {
                                setEditedDueDate(e.target.value);
                                handleSave({ due_date: e.target.value } as any);
                              }}
                            />
                         </div>
                      </div>

                      {/* Etiquetas */}
                      <div className="flex flex-col gap-2 min-w-[220px]">
                         <div className="text-[10px] text-gray-600 font-black uppercase tracking-[0.2em] flex items-center gap-2">
                            <Tag className="h-3.5 w-3.5" /> Etiquetas Judiciales
                         </div>
                         <Popover>
                            <PopoverTrigger asChild>
                               <Button variant="outline" className="h-10 w-full bg-white/[0.03] border-white/10 rounded-lg flex items-center justify-start gap-2 px-3 hover:bg-white/5 transition-all overflow-hidden">
                                  {displayTask.tags?.length ? (
                                    <div className="flex flex-wrap gap-1.5 overflow-hidden max-h-[28px]">
                                       {displayTask.tags.map(t => (
                                         <Badge key={t.id} style={{ backgroundColor: t.color || '#3b82f6', color: '#fff' }} className="h-6 text-[10px] font-black px-3 rounded-md border-none shadow-md">
                                            {t.name}
                                         </Badge>
                                       ))}
                                    </div>
                                  ) : (
                                    <span className="text-[12px] text-gray-700 font-bold">+ Agregar Etiqueta</span>
                                  )}
                               </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-80 p-3 bg-[#1e1e1e] border-white/10 text-white rounded-xl shadow-2xl">
                               <ScrollArea className="h-[250px]">
                                  <div className="p-2 border-b border-white/5 mb-3 text-[10px] font-black uppercase text-gray-500">Listado Maestro</div>
                                  <div className="space-y-1">
                                    {allTags.map(t => (
                                      <div key={t.id} className="flex items-center justify-between p-3 hover:bg-white/10 rounded-lg cursor-pointer transition-all" onClick={() => toggleTag(t.name)}>
                                         <div className="flex items-center gap-3">
                                            <div className="h-3.5 w-3.5 rounded-full shadow-lg" style={{ backgroundColor: t.color || '#3b82f6' }} />
                                            <span className="text-sm font-bold text-gray-200">{t.name}</span>
                                         </div>
                                         {displayTask.tags?.some(gt => gt.name === t.name) && <Check className="h-4 w-4 text-[#2da44e]" />}
                                      </div>
                                    ))}
                                  </div>
                                  {allTags.length === 0 && <div className="p-10 text-[11px] text-gray-600 uppercase italic text-center">No se encontraron etiquetas globales</div>}
                               </ScrollArea>
                            </PopoverContent>
                         </Popover>
                      </div>
                   </div>

                   {/* Description Area */}
                   <div className="space-y-4 pt-4">
                      <div className="flex items-center gap-3 text-gray-700 italic text-[12px] font-medium">
                         <Activity className="h-4 w-4 opacity-50 text-primary" />
                         <span>Bitácora de seguimiento técnico...</span>
                      </div>
                      <Textarea 
                        className="min-h-[220px] bg-white/[0.02] border border-white/5 rounded-2xl p-8 text-[15px] font-medium leading-relaxed text-gray-200 focus:ring-1 focus:ring-primary/20 placeholder:text-gray-800 transition-all shadow-inner"
                        placeholder="Ingresa los avances detallados del proceso aquí..."
                        value={editedDesc}
                        onChange={(e) => setEditedDesc(e.target.value)}
                        onBlur={() => handleSave({ description: editedDesc })}
                      />
                   </div>

                   {/* Subtasks Table */}
                   <div className="space-y-6 pt-10 border-t border-white/5">
                      <div className="flex items-center justify-between">
                         <div className="flex items-center gap-6">
                            <div className="flex items-center gap-3 text-gray-400 font-black text-[14px] uppercase tracking-widest">
                               <ChevronDown className="h-5 w-5" /> Subtareas
                            </div>
                            <div className="flex items-center gap-4 text-[12px] text-gray-600 bg-white/5 px-4 py-1.5 rounded-full border border-white/10">
                               <span className="font-bold">{completedSubtasks} completada</span>
                               <Progress value={totalSubtasks > 0 ? (completedSubtasks / totalSubtasks) * 100 : 0} className="w-32 h-1.5 bg-gray-900" />
                            </div>
                         </div>
                         <div className="flex items-center gap-5 text-gray-500">
                            <Search className="h-5 w-5 hover:text-white cursor-pointer transition-all" />
                            <Button size="sm" onClick={() => setShowSubtaskForm(true)} className="h-8 rounded-lg bg-primary/10 text-primary text-[10px] font-black uppercase tracking-widest hover:bg-primary/20 transition-all border border-primary/20">
                               + NUEVA TAREA
                            </Button>
                         </div>
                      </div>

                      <div className="w-full bg-white/[0.01] rounded-3xl border border-white/5 overflow-hidden shadow-2xl">
                         <div className="grid grid-cols-[1fr_140px_100px_120px] gap-6 px-8 py-4 border-b border-white/5 text-[11px] font-black uppercase text-gray-600 tracking-[0.2em] bg-white/[0.02]">
                            <div>Nombre de la Gestión</div>
                            <div className="text-center">Responsable</div>
                            <div className="text-center">Prioridad</div>
                            <div className="text-right">Vencimiento</div>
                         </div>
                         <div className="divide-y divide-white/5">
                            {displayTask.subtasks?.map(st => (
                              <div key={st.id} className="grid grid-cols-[1fr_140px_100px_120px] gap-6 px-8 py-5 hover:bg-white/[0.04] transition-all cursor-pointer group text-[14px]">
                                 <div className="flex items-center gap-4 text-gray-200">
                                    <div className={cn("h-5 w-5 rounded-full border-2 border-gray-700 flex items-center justify-center transition-all", (st.status?.toLowerCase().includes('completado') || st.status?.toLowerCase() === 'closed') && 'bg-[#2da44e] border-[#2da44e]')}>
                                       {(st.status?.toLowerCase().includes('completado') || st.status?.toLowerCase() === 'closed') && <Check className="h-3 w-3 text-white" />}
                                    </div>
                                    <span className={cn("font-bold tracking-tight", (st.status?.toLowerCase().includes('completado') || st.status?.toLowerCase() === 'closed') && "line-through text-gray-600")}>{st.title}</span>
                                 </div>
                                 <div className="flex justify-center items-center">
                                    <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center text-[11px] font-black text-primary border border-primary/30 shadow-md">{st.assignee_name?.[0] || 'U'}</div>
                                 </div>
                                 <div className="flex justify-center items-center">
                                    <Flag className={`h-5 w-5 ${st.priority === 'high' ? 'text-red-500 shadow-[0_0_10px_rgba(239,68,68,0.3)]' : 'text-gray-700'}`} />
                                 </div>
                                 <div className="text-right text-[12px] font-black text-[#2da44e] flex items-center justify-end tracking-tighter">
                                    {st.due_date ? format(new Date(st.due_date), 'd MMM, yyyy') : '-'}
                                 </div>
                              </div>
                            ))}
                            {(!displayTask.subtasks || displayTask.subtasks.length === 0) && (
                               <div className="p-12 text-center text-[12px] text-gray-600 font-bold uppercase italic tracking-widest">No hay subtareas vinculadas</div>
                            )}
                         </div>
                      </div>
                   </div>

                   {/* Technical Fields Matrix */}
                   <div className="space-y-6 pt-10 border-t border-white/5">
                      <div className="text-gray-400 font-black text-[14px] uppercase tracking-widest flex items-center gap-3">
                         <ChevronDown className="h-5 w-5" /> Campos Técnicos ClickUp
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-2">
                         {(() => {
                            try {
                              const fields = JSON.parse(displayTask.custom_fields || '[]');
                              if (Array.isArray(fields)) {
                                return fields.map((f: any, idx: number) => (
                                  <div key={idx} className="flex justify-between items-center py-3.5 px-5 hover:bg-white/[0.04] rounded-xl group transition-all text-[13px] border border-transparent hover:border-white/5">
                                     <span className="text-gray-500 font-black uppercase tracking-tight group-hover:text-gray-300 transition-colors">{f.name}</span>
                                     <span className="text-gray-200 font-black px-4 py-1.5 bg-white/5 rounded-lg border border-white/10 shadow-inner">{f.value || f.text_value || '-'}</span>
                                  </div>
                                ));
                              }
                            } catch (e) {}
                            return null;
                         })()}
                      </div>
                   </div>
                </div>
             </ScrollArea>
          </div>

          {/* RIGHT: ACTIVITY PANEL */}
          <div className="flex-1 flex flex-col bg-[#111111] border-l border-white/5 shadow-[0_0_100px_rgba(0,0,0,0.5)] overflow-hidden">
             <div className="h-16 flex items-center justify-between px-10 border-b border-white/5 bg-white/[0.01]">
                <span className="text-[13px] font-black uppercase tracking-[0.4em] text-gray-600">Activity Log</span>
                <div className="flex items-center gap-5 text-gray-600">
                   <Search className="h-5 w-5 hover:text-white cursor-pointer transition-colors" />
                   <Settings className="h-5 w-5 hover:text-white cursor-pointer transition-colors" />
                </div>
             </div>

             <ScrollArea className="flex-1 px-10 py-10">
                <div className="space-y-12">
                   {displayTask.comments?.map(comment => (
                     <div key={comment.id} className="group relative">
                        <div className="flex items-center gap-4 text-[12px] mb-4">
                           <div className="h-8 w-8 rounded-xl bg-primary/10 flex items-center justify-center text-[12px] font-black text-primary border border-primary/20 shadow-lg">
                              {comment.user_name?.[0] || 'U'}
                           </div>
                           <div className="flex flex-col">
                              <span className="text-gray-200 font-black uppercase tracking-wider">{(comment.user_name || 'System')}</span>
                              <span className="text-gray-600 text-[10px] font-bold">{isValid(new Date(comment.created_at)) ? format(new Date(comment.created_at), "d MMM 'a las' p", { locale: es }) : ''}</span>
                           </div>
                        </div>
                        
                        <div className="p-6 bg-white/[0.03] border border-white/5 rounded-3xl rounded-tl-none text-[15px] font-medium text-gray-300 leading-relaxed shadow-xl group-hover:bg-white/[0.05] group-hover:border-white/10 transition-all">
                           {editingCommentId === comment.id ? (
                             <div className="space-y-4">
                                <Textarea value={editingCommentText} onChange={(e) => setEditingCommentText(e.target.value)} className="bg-black/60 border-primary/30 text-sm min-h-[100px] rounded-2xl" />
                                <div className="flex justify-end gap-3">
                                   <Button size="sm" variant="ghost" onClick={() => setEditingCommentId(null)} className="h-8 text-[11px] font-black uppercase">Cancelar</Button>
                                   <Button size="sm" onClick={() => handleUpdateComment(comment.id)} className="h-8 text-[11px] font-black bg-primary px-6">GUARDAR</Button>
                               </div>
                             </div>
                           ) : (
                             <>
                               {comment.content}
                               <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-all flex gap-3">
                                  <button onClick={() => { setEditingCommentId(comment.id); setEditingCommentText(comment.content); }} className="h-8 w-8 rounded-xl bg-black/60 flex items-center justify-center hover:text-primary border border-white/5 transition-all shadow-lg"><Edit3 className="h-4 w-4" /></button>
                                  <button onClick={() => handleDeleteComment(comment.id)} className="h-8 w-8 rounded-xl bg-black/60 flex items-center justify-center hover:text-red-500 border border-white/5 transition-all shadow-lg"><Trash2 className="h-4 w-4" /></button>
                               </div>
                               <div className="mt-4 pt-4 border-t border-white/5 flex items-center gap-6 text-gray-600 text-[11px] font-black uppercase tracking-widest">
                                  <div className="flex items-center gap-2 hover:text-white cursor-pointer transition-colors"><Smile className="h-4 w-4" /> Reaccionar</div>
                                  <div className="hover:text-white cursor-pointer transition-colors">Responder</div>
                               </div>
                             </>
                           )}
                        </div>
                     </div>
                   ))}
                </div>
             </ScrollArea>

             <div className="p-8 bg-[#111111] border-t border-white/5">
                <div className="bg-[#1e1e1e] border-2 border-white/5 rounded-3xl p-6 space-y-4 shadow-2xl focus-within:border-primary/40 transition-all">
                   <Textarea 
                     value={newComment}
                     onChange={(e) => setNewComment(e.target.value)}
                     placeholder="Añade una nota técnica al proceso..."
                     className="bg-transparent border-none focus:ring-0 p-0 text-[15px] min-h-[80px] resize-none text-gray-200 font-medium placeholder:text-gray-800"
                   />
                   <div className="flex items-center justify-between">
                      <div className="flex items-center gap-5 text-gray-600">
                         <AttachmentIcon className="h-5 w-5 hover:text-white cursor-pointer transition-all" />
                         <Zap className="h-5 w-5 text-purple-400 hover:text-purple-300 cursor-pointer transition-all" />
                         <Smile className="h-5 w-5 hover:text-white cursor-pointer transition-all" />
                         <div className="flex items-center gap-2 px-3 py-1 bg-white/5 rounded-lg hover:bg-white/10 cursor-pointer text-[11px] font-black uppercase tracking-widest border border-white/5">
                            <MessageCircle className="h-4 w-4" /> Comentario
                         </div>
                      </div>
                      <Button size="icon" onClick={handleAddComment} disabled={!newComment.trim()} className={cn("h-11 w-11 rounded-2xl shadow-2xl transition-all", newComment.trim() ? "bg-primary text-white scale-105" : "bg-gray-800 text-gray-600 shadow-none")}>
                        <Send className="h-5 w-5" />
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
