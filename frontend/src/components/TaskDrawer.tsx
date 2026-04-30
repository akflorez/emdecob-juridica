import { useState, useEffect, useMemo } from "react";
import { 
  X, Calendar as CalendarIcon, User as UserIcon, CheckCircle2, 
  Clock, Tag, Paperclip, MessageSquare, Plus, ChevronRight, 
  Send, Trash2, ListChecks, Zap, Flag, AlertCircle, Edit3,
  UserCheck, Search, Activity, CornerDownRight, Smile, MoreHorizontal,
  ChevronDown, CalendarDays, Layout, Check, Trash, RefreshCw
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
      
      // Cargar TODOS los usuarios para asignación (Abogados)
      getUsers().then(res => setUsers(Array.isArray(res) ? res : [])).catch(console.error);
      
      // Cargar Etiquetas con fallback
      getTags().then(res => {
        if (res && Array.isArray(res) && res.length > 0) {
          setAllTags(res);
        } else if (task.tags) {
          setAllTags(task.tags);
        }
      }).catch(() => {
        if (task.tags) setAllTags(task.tags);
      });

      // Cargar Estados
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
      toast({ title: "Error", description: "No se pudo actualizar" });
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
      toast({ title: "Error" });
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
      toast({ title: "Error al borrar" });
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
      toast({ title: "Géstion creada" });
    } catch (error) {
      toast({ title: "Error" });
    }
  };

  if (!displayTask) return null;

  const statusOptions = Array.from(new Set([
    'ABIERTO', 'TO DO', 'IN PROGRESS', 'PENDIENTE', 'ALMP', '468', 'NOT PERSONAL', 'NOT AVISO', 'EMPLAZAMIENTO', 'LIQUIDACION', 'AVALUO', 'REMATE', 'COMPLETO', 'CLOSED',
    ...(allSystemStatuses || []),
    ...(propStatuses || [])
  ])).filter(Boolean);

  const currentStatus = (displayTask.status || 'ABIERTO').toUpperCase();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[1100px] p-0 bg-[#0f1115] border-white/10 text-slate-100 flex flex-col shadow-2xl">
        <SheetHeader className="sr-only">
          <SheetTitle>Consola de Gestión Judicial Expert</SheetTitle>
        </SheetHeader>
        
        <div className="flex flex-1 overflow-hidden h-full">
          <div className="flex-[1.8] flex flex-col border-r border-white/5 overflow-hidden bg-[#0f1115]">
             <ScrollArea className="flex-1">
                <div className="p-8 space-y-10">
                   {/* Top Header Row */}
                   <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                         <Badge className="bg-primary/20 text-primary border-primary/30 font-black px-4 py-1.5 uppercase text-[9px] rounded-lg shadow-lg">
                           ID: {displayTask.clickup_id || displayTask.id}
                         </Badge>
                         <div className="flex items-center gap-2 px-3 py-1 bg-green-500/10 rounded-full border border-green-500/20 text-[9px] font-black text-green-400">
                            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                            SINCRONIZADO
                         </div>
                      </div>
                      <div className="flex items-center gap-2">
                         <Button variant="ghost" size="sm" onClick={refreshTask} disabled={isLoading} className="h-8 rounded-lg text-[9px] font-black uppercase text-slate-500">
                            <RefreshCw className={cn("h-3 w-3 mr-2", isLoading && "animate-spin")} /> Refrescar
                         </Button>
                         <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="rounded-full hover:bg-white/5">
                           <X className="h-6 w-6" />
                         </Button>
                      </div>
                   </div>

                   {/* Main Selector Row */}
                   <div className="space-y-8">
                      <div className="flex items-center gap-4 flex-wrap">
                        {/* Estado Selector */}
                        <Select value={statusOptions.includes(currentStatus) ? currentStatus : undefined} onValueChange={(v) => handleSave({ status: v })}>
                          <SelectTrigger className="w-auto min-w-[160px] h-10 px-5 rounded-2xl border-none font-black text-[10px] uppercase tracking-widest bg-primary/10 text-primary shadow-xl hover:bg-primary/20 transition-all">
                            <SelectValue placeholder={currentStatus} />
                          </SelectTrigger>
                          <SelectContent className="bg-[#1c1f26] border-white/10 text-white shadow-2xl">
                            {statusOptions.map(s => (
                              <SelectItem key={s} value={s} className="uppercase text-[10px] font-black py-3 tracking-widest">{s}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        {/* Abogados Selector */}
                        <Popover>
                          <PopoverTrigger asChild>
                            <button className="flex items-center gap-3 px-5 py-2.5 bg-white/5 rounded-2xl hover:bg-white/10 transition-all text-[11px] font-black uppercase tracking-widest text-slate-200 border border-white/10 shadow-lg">
                               <UserIcon className="h-4 w-4 text-primary" />
                               <span className="max-w-[300px] truncate">
                                 {displayTask.assignees && displayTask.assignees.length > 0 
                                   ? displayTask.assignees.map(a => a.nombre || a.username).join(', ') 
                                   : displayTask.assignee_name || 'Asignar Abogados'}
                               </span>
                               <ChevronDown className="h-4 w-4 opacity-50" />
                            </button>
                          </PopoverTrigger>
                          <PopoverContent className="w-80 p-3 bg-[#1c1f26] border-white/10 text-white rounded-[2rem] shadow-2xl">
                             <div className="px-3 pb-3 border-b border-white/5 mb-2">
                                <span className="text-[10px] font-black uppercase text-slate-500 tracking-[0.2em]">Seleccionar Abogados</span>
                             </div>
                             <ScrollArea className="h-[350px]">
                                <div className="space-y-1">
                                   {users.map(u => (
                                     <div key={u.id} className="flex items-center gap-3 p-3 hover:bg-white/10 rounded-2xl cursor-pointer transition-all border border-transparent" onClick={() => toggleAssignee(u.id)}>
                                        <Checkbox checked={displayTask.assignees?.some(a => a.id === u.id)} className="h-5 w-5 border-white/30 data-[state=checked]:bg-primary" />
                                        <div className="flex flex-col">
                                           <span className="text-sm font-bold">{(u.nombre || u.username)}</span>
                                           <span className="text-[9px] text-slate-500 font-black uppercase">{u.is_admin ? 'Administrador' : 'Abogado'}</span>
                                        </div>
                                     </div>
                                   ))}
                                   {users.length === 0 && <div className="p-10 text-center text-[10px] font-black text-slate-600 uppercase italic">Cargando equipo...</div>}
                                </div>
                             </ScrollArea>
                          </PopoverContent>
                        </Popover>

                        {/* Fecha Vencimiento */}
                        <div className="flex items-center gap-3 px-5 py-2.5 bg-white/5 rounded-2xl border border-white/10 shadow-lg hover:bg-white/10 transition-all">
                            <CalendarIcon className="h-4 w-4 text-primary" />
                            <input 
                              type="date" 
                              className="bg-transparent border-none focus:ring-0 text-[11px] font-black uppercase text-slate-200 p-0 w-[120px]"
                              value={editedDueDate}
                              onChange={(e) => {
                                setEditedDueDate(e.target.value);
                                handleSave({ due_date: e.target.value } as any);
                              }}
                            />
                        </div>

                        {/* Etiquetas Selector */}
                        <Popover>
                          <PopoverTrigger asChild>
                            <button className="flex items-center gap-2 px-5 py-2.5 bg-white/5 rounded-2xl hover:bg-white/10 transition-all text-[10px] font-black uppercase tracking-widest text-slate-400 border border-white/10 shadow-lg">
                               <Tag className="h-4 w-4" /> + ETIQUETAS
                            </button>
                          </PopoverTrigger>
                          <PopoverContent className="w-72 p-3 bg-[#1c1f26] border-white/10 text-white rounded-[2rem] shadow-2xl">
                             <ScrollArea className="h-[300px]">
                                <div className="space-y-1">
                                   {allTags.map(t => (
                                     <div key={t.id} className="flex items-center justify-between p-3 hover:bg-white/10 rounded-2xl cursor-pointer transition-all" onClick={() => toggleTag(t.name)}>
                                        <div className="flex items-center gap-3">
                                           <div className="h-3 w-3 rounded-full" style={{ backgroundColor: t.color || '#3b82f6' }} />
                                           <span className="text-xs font-bold">{t.name}</span>
                                        </div>
                                        {displayTask.tags?.some(gt => gt.name === t.name) && <CheckCircle2 className="h-4 w-4 text-primary" />}
                                     </div>
                                   ))}
                                   {allTags.length === 0 && <div className="p-10 text-center text-[10px] font-black text-slate-600 uppercase italic">Sin etiquetas disponibles</div>}
                                </div>
                             </ScrollArea>
                          </PopoverContent>
                        </Popover>
                      </div>

                      {/* Radicado / Title */}
                      <div className="space-y-1 relative">
                        <input 
                          className="w-full bg-transparent text-2xl font-black tracking-tight border-none focus:ring-0 p-0 text-white placeholder:text-slate-800"
                          value={editedTitle}
                          onChange={(e) => setEditedTitle(e.target.value)}
                          onBlur={() => handleSave({ title: editedTitle })}
                        />
                        <div className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] flex items-center gap-2">
                           <Activity className="h-4 w-4 text-primary" /> EXPEDIENTE RADICADO
                        </div>
                      </div>
                   </div>

                   {/* Tags Cloud */}
                   <div className="flex flex-wrap gap-2.5">
                      {displayTask.tags?.map(tag => (
                        <Badge key={tag.id} style={{ backgroundColor: `${tag.color || '#3b82f6'}33`, color: tag.color || '#3b82f6', borderColor: `${tag.color || '#3b82f6'}55` }} className="text-[9px] py-1.5 px-4 font-black uppercase tracking-widest rounded-xl border-2 shadow-md">
                          {tag.name}
                        </Badge>
                      ))}
                   </div>

                   {/* Info Matrix */}
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                      <div className="p-10 bg-white/[0.03] border border-white/10 rounded-[2.5rem] space-y-6 shadow-2xl">
                         <div className="text-[11px] font-black text-slate-400 uppercase tracking-[0.25em] flex items-center gap-3">
                           <Layout className="h-5 w-5 text-primary" /> DATOS DE CARPETA
                         </div>
                         <div className="space-y-5">
                            {(() => {
                               try {
                                 const fields = JSON.parse(displayTask.custom_fields || '[]');
                                 if (Array.isArray(fields) && fields.length > 0) {
                                   return fields.map((f: any, idx: number) => (
                                     <div key={idx} className="flex justify-between items-center py-4 border-b border-white/5 group">
                                        <span className="text-[10px] text-slate-500 font-black uppercase tracking-tight group-hover:text-slate-300 transition-colors">{f.name}</span>
                                        <span className="text-[13px] text-white font-black bg-white/5 px-4 py-1.5 rounded-xl border border-white/10 shadow-inner">{f.value || f.text_value || '-'}</span>
                                     </div>
                                   ));
                                 }
                               } catch (e) {}
                               return <div className="p-10 text-center text-[10px] font-black text-slate-600 uppercase italic tracking-widest bg-black/20 rounded-3xl border border-dashed border-white/10">No se encontraron campos técnicos</div>;
                            })()}
                         </div>
                      </div>
                      <div className="p-10 bg-white/[0.03] border border-white/10 rounded-[2.5rem] space-y-6 flex flex-col justify-between shadow-2xl relative overflow-hidden group">
                         <div className="absolute -right-10 -top-10 h-40 w-40 bg-primary/5 rounded-full blur-[60px] group-hover:bg-primary/10 transition-all" />
                         <div className="text-[11px] font-black text-slate-400 uppercase tracking-[0.25em] flex items-center gap-3">
                           <Zap className="h-5 w-5 text-yellow-500" /> VÍNCULO JURÍDICO
                         </div>
                         <div className="space-y-5">
                            <div className="text-lg font-black text-primary font-mono tracking-wider bg-black/40 p-6 rounded-3xl border border-primary/20 shadow-inner truncate">
                               {displayTask.case_radicado || '11001400305420250052800'}
                            </div>
                            <Button variant="outline" className="w-full h-12 rounded-2xl bg-white/5 border-white/10 text-[11px] font-black uppercase tracking-widest text-slate-300 hover:bg-primary/10 hover:text-primary hover:border-primary/30 transition-all flex items-center gap-3">
                               <UserCheck className="h-5 w-5" /> VER DETALLES DEL PROCESO <ChevronRight className="h-4 w-4 ml-auto" />
                            </Button>
                         </div>
                      </div>
                   </div>

                   {/* Actualización Jurídica */}
                   <div className="space-y-6">
                      <div className="flex items-center gap-3 text-[11px] font-black text-slate-400 uppercase tracking-[0.25em]">
                        <Edit3 className="h-5 w-5 text-primary" /> ACTUALIZACIÓN JURÍDICA
                      </div>
                      <Textarea 
                        className="min-h-[200px] bg-white/[0.03] border-2 border-white/10 rounded-[2.5rem] p-10 text-[15px] font-medium leading-relaxed text-slate-100 focus:border-primary/50 transition-all shadow-2xl placeholder:text-slate-800"
                        placeholder="Ingresa los avances técnicos o memoriales radicados..."
                        value={editedDesc}
                        onChange={(e) => setEditedDesc(e.target.value)}
                        onBlur={() => handleSave({ description: editedDesc })}
                      />
                   </div>

                   {/* Listado Gestión */}
                   <div className="space-y-10">
                      <div className="flex items-center justify-between bg-white/[0.02] p-8 rounded-[2rem] border border-white/10 shadow-2xl">
                         <div className="text-[11px] font-black text-slate-400 uppercase tracking-[0.25em] flex items-center gap-3">
                            <ListChecks className="h-6 w-6 text-primary" /> LISTADO DE GESTIÓN TÉCNICA
                         </div>
                         <Button size="sm" onClick={() => setShowSubtaskForm(true)} className="h-10 rounded-2xl bg-primary text-primary-foreground font-black text-[11px] uppercase tracking-widest px-8 shadow-xl shadow-primary/20 hover:scale-105 active:scale-95 transition-all">
                            + NUEVA GESTIÓN
                         </Button>
                      </div>
                      
                      <div className="space-y-5">
                         {showSubtaskForm && (
                           <div className="p-10 bg-primary/5 border-2 border-primary/20 rounded-[3rem] space-y-8 shadow-2xl animate-in fade-in zoom-in duration-300">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                 <div className="space-y-2">
                                    <label className="text-[10px] font-black text-primary uppercase ml-3 tracking-widest">Actividad</label>
                                    <Input placeholder="Ej: Radicar memorial de embargo..." value={newSubtaskTitle} onChange={(e) => setNewSubtaskTitle(e.target.value)} className="bg-black/50 border-white/10 h-14 rounded-2xl px-6 text-sm font-bold" />
                                 </div>
                                 <div className="space-y-2">
                                    <label className="text-[10px] font-black text-primary uppercase ml-3 tracking-widest">Fecha Límite</label>
                                    <Input type="date" value={newSubtaskDate} onChange={(e) => setNewSubtaskDate(e.target.value)} className="bg-black/50 border-white/10 h-14 rounded-2xl px-6 text-sm font-bold" />
                                 </div>
                              </div>
                              <div className="flex justify-end gap-5">
                                 <Button variant="ghost" onClick={() => setShowSubtaskForm(false)} className="rounded-2xl text-[11px] font-black uppercase tracking-widest text-slate-400">Cancelar</Button>
                                 <Button onClick={handleCreateSubtask} className="h-12 rounded-2xl bg-primary text-primary-foreground font-black text-[11px] uppercase tracking-widest px-10 shadow-xl shadow-primary/20">GUARDAR GESTIÓN</Button>
                              </div>
                           </div>
                         )}

                         {displayTask.checklists?.map(item => (
                           <div key={item.id} className="flex items-center gap-6 p-7 bg-white/[0.03] border-2 border-white/5 rounded-[2rem] group hover:bg-white/[0.06] hover:border-white/10 transition-all shadow-xl">
                              <Checkbox 
                                checked={item.is_completed} 
                                onCheckedChange={(v) => updateChecklistItem(item.id, { is_completed: !!v }).then(refreshTask)} 
                                className="h-7 w-7 border-2 border-white/20 data-[state=checked]:bg-green-500 data-[state=checked]:border-green-500" 
                              />
                              <span className={cn("text-[15px] flex-1 font-bold tracking-tight transition-all", item.is_completed ? "line-through text-slate-600" : "text-slate-100")}>
                                {item.content}
                              </span>
                              <Button variant="ghost" size="icon" onClick={() => deleteChecklistItem(item.id).then(refreshTask)} className="h-10 w-10 text-slate-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all rounded-xl">
                                 <Trash2 className="h-5 w-5" />
                              </Button>
                           </div>
                         ))}

                         <div className="flex items-center gap-5 bg-white/[0.01] border-2 border-dashed border-white/10 rounded-[2rem] p-3 pl-10 group hover:border-primary/40 transition-all shadow-inner">
                            <Plus className="h-6 w-6 text-slate-700 group-hover:text-primary transition-colors" />
                            <Input 
                              placeholder="Añadir paso rápido a la lista de tareas..." 
                              value={newChecklist} 
                              onChange={(e) => setNewChecklist(e.target.value)} 
                              onKeyDown={(e) => e.key === 'Enter' && handleAddChecklist()} 
                              className="bg-transparent border-none focus:ring-0 text-sm font-bold h-14" 
                            />
                            <Button onClick={handleAddChecklist} className="h-12 rounded-2xl bg-white/5 hover:bg-white/10 text-[11px] font-black uppercase tracking-widest px-8 shadow-md">AÑADIR</Button>
                         </div>
                      </div>
                   </div>
                </div>
             </ScrollArea>
          </div>

          {/* Historial Panel */}
          <div className="flex-1 flex flex-col bg-[#0b0d10] border-l border-white/5 shadow-[0_0_100px_rgba(0,0,0,0.8)] overflow-hidden">
             <div className="h-20 flex items-center px-10 border-b-2 border-white/5 font-black text-[11px] uppercase tracking-[0.3em] gap-10 bg-white/[0.02]">
                <span className="text-primary border-b-4 border-primary h-full flex items-center">HISTORIAL DE ACTIVIDAD</span>
             </div>

             <ScrollArea className="flex-1">
                <div className="p-10 space-y-12">
                   {displayTask.comments?.map(comment => (
                     <div key={comment.id} className="group relative">
                        <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-[0.15em] text-slate-600 mb-4">
                           <div className="flex items-center gap-3">
                              <div className="h-6 w-6 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/20">{comment.user_name?.[0]}</div>
                              <span className="text-slate-300">{(comment.user_name || 'Usuario System')}</span>
                           </div>
                           <span className="opacity-50">{isValid(new Date(comment.created_at)) ? format(new Date(comment.created_at), "d MMM, h:mm a", { locale: es }) : ''}</span>
                        </div>
                        {editingCommentId === comment.id ? (
                           <div className="space-y-3 animate-in slide-in-from-top-2 duration-300">
                              <Textarea value={editingCommentText} onChange={(e) => setEditingCommentText(e.target.value)} className="bg-black/60 text-sm min-h-[100px] rounded-2xl border-primary/30 p-5 font-medium leading-relaxed" />
                              <div className="flex justify-end gap-3">
                                 <Button size="sm" variant="ghost" onClick={() => setEditingCommentId(null)} className="rounded-xl text-[10px] font-black uppercase">Cancelar</Button>
                                 <Button size="sm" onClick={() => handleUpdateComment(comment.id)} className="rounded-xl bg-primary text-primary-foreground text-[10px] font-black uppercase px-6">Guardar Cambios</Button>
                              </div>
                           </div>
                        ) : (
                           <div className="p-7 bg-white/[0.04] border-2 border-white/5 rounded-[2.5rem] rounded-tl-none text-[14px] font-medium text-slate-200 leading-relaxed relative shadow-2xl group-hover:bg-white/[0.06] transition-all">
                              {comment.content}
                              <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-all flex gap-2">
                                 <button onClick={() => { setEditingCommentId(comment.id); setEditingCommentText(comment.content); }} className="h-8 w-8 rounded-xl bg-black/40 flex items-center justify-center hover:text-primary transition-colors border border-white/5"><Edit3 className="h-4 w-4" /></button>
                                 <button onClick={() => handleDeleteComment(comment.id)} className="h-8 w-8 rounded-xl bg-black/40 flex items-center justify-center hover:text-red-500 transition-colors border border-white/5"><Trash className="h-4 w-4" /></button>
                              </div>
                           </div>
                        )}
                     </div>
                   ))}
                   {(!displayTask.comments || displayTask.comments.length === 0) && (
                      <div className="p-20 text-center space-y-4 opacity-20">
                         <MessageSquare className="h-16 w-16 mx-auto text-slate-500" />
                         <p className="text-[10px] font-black uppercase tracking-widest">Sin actividad registrada</p>
                      </div>
                   )}
                </div>
             </ScrollArea>

             <div className="p-10 border-t-2 border-white/5 bg-[#16181d]/90 backdrop-blur-3xl shadow-[0_-20px_50px_rgba(0,0,0,0.5)]">
                <div className="relative group/input">
                   <Textarea 
                     value={newComment}
                     onChange={(e) => setNewComment(e.target.value)}
                     placeholder="Escribe una actualización técnica..."
                     className="bg-black/60 border-2 border-white/10 focus:border-primary/40 rounded-[2.5rem] pr-20 min-h-[140px] resize-none text-[15px] font-bold p-8 shadow-2xl transition-all placeholder:text-slate-800"
                   />
                   <Button size="icon" onClick={handleAddComment} disabled={!newComment.trim()} className="absolute bottom-6 right-6 h-14 w-14 rounded-[1.75rem] bg-primary shadow-2xl shadow-primary/40 hover:scale-110 active:scale-95 transition-all">
                     <Send className="h-7 w-7 text-white" />
                   </Button>
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
