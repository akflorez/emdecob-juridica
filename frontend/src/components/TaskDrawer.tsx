import { useState, useEffect, useMemo, useCallback } from "react";
import { 
  X, Calendar as CalendarIcon, User as UserIcon, CheckCircle2, 
  Clock, Tag, Paperclip, MessageSquare, Plus, ChevronRight, 
  Send, Trash2, ListChecks, Zap, Flag, AlertCircle, Edit3,
  UserCheck, Search, Activity, CornerDownRight, Smile, MoreHorizontal,
  ChevronDown, Layout, CalendarDays, CalendarPlus
} from "lucide-react";
import {
  Sheet,
  SheetContent,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { 
  updateTask, addComment, deleteComment,
  addChecklistItem, updateChecklistItem, deleteChecklistItem,
  getUsers, getTags, getTaskDetail, createTask,
  type Task as TaskType, type User, type Tag as TagType, type TaskComment, type ChecklistItem
} from "@/services/api";
import { useToast } from "@/hooks/use-toast";
import { format } from "date-fns";
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
import { motion, AnimatePresence } from "framer-motion";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface TaskDrawerProps {
  task: TaskType | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskUpdate: (updatedTask: TaskType) => void;
  clickupToken?: string;
  allAssignees?: string[];
  allStatuses?: string[];
}

export function TaskDrawer({ task, open, onOpenChange, onTaskUpdate, clickupToken, allAssignees = [], allStatuses = [] }: TaskDrawerProps) {
  const { toast } = useToast();
  const [editedTitle, setEditedTitle] = useState('');
  const [editedDesc, setEditedDesc] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [fullTask, setFullTask] = useState<TaskType | null>(null);
  const [newComment, setNewComment] = useState('');
  const [newChecklist, setNewChecklist] = useState("");
  const [allTags, setAllTags] = useState<TagType[]>([]);
  const [activeRightTab, setActiveRightTab] = useState<'activity' | 'comments'>('activity');
  
  // Creation state for subtasks
  const [showSubtaskForm, setShowSubtaskForm] = useState(false);
  const [newSubtaskTitle, setNewSubtaskTitle] = useState("");
  const [newSubtaskDate, setNewSubtaskDate] = useState("");

  const displayTask = fullTask || task;

  useEffect(() => {
    if (task && open) {
      setEditedTitle(task.title);
      setEditedDesc(task.description || '');
      refreshTask();
      getUsers().then(setUsers).catch(console.error);
      getTags().then(setAllTags).catch(console.error);
    }
  }, [task, open]);

  const refreshTask = async () => {
    if (!task) return;
    setIsLoading(true);
    try {
      const detail = await getTaskDetail(task.id, clickupToken);
      setFullTask(detail);
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
      toast({ title: "Error", description: "No se pudo actualizar la tarea", variant: "destructive" });
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
      toast({ title: "Subtarea creada satisfactoriamente" });
    } catch (error) {
      toast({ title: "Error al crear subtarea", variant: "destructive" });
    }
  };

  const handleAddComment = async () => {
    if (!displayTask || !newComment.trim()) return;
    try {
      await addComment(displayTask.id, newComment);
      setNewComment('');
      refreshTask();
    } catch (error) {
      toast({ title: "Error", description: "No se pudo añadir el comentario" });
    }
  };

  const handleAddChecklist = async () => {
    if (!displayTask || !newChecklist.trim()) return;
    try {
      await addChecklistItem(displayTask.id, newChecklist);
      setNewChecklist("");
      refreshTask();
    } catch (error) {
      toast({ title: "Error", description: "No se pudo añadir el item" });
    }
  };

  const handleToggleAssignee = (userId: number) => {
    if (!displayTask) return;
    const currentIds = displayTask.assignees?.map(a => a.id) || [];
    let newIds: number[];
    if (currentIds.includes(userId)) {
      newIds = currentIds.filter(id => id !== userId);
    } else {
      newIds = [...currentIds, userId];
    }
    handleSave({ assignee_ids: newIds } as any);
  };

  const handleTagToggle = async (tagName: string) => {
    if (!displayTask) return;
    const currentTags = displayTask.tags?.map(t => t.name) || [];
    let newTags: string[];
    if (currentTags.includes(tagName)) {
      newTags = currentTags.filter(t => t !== tagName);
    } else {
      newTags = [...currentTags, tagName];
    }
    handleSave({ tags: newTags } as any);
  };

  if (!displayTask) return null;

  const getStatusColor = (status?: string) => {
    const s = (status || '').toLowerCase();
    if (s.includes('abierto') || s.includes('todo') || s.includes('almp')) return 'bg-slate-400/30 text-slate-100 border-slate-400/50';
    if (s.includes('proceso') || s.includes('curso') || s.includes('468')) return 'bg-blue-500/40 text-blue-50 border-blue-500/60';
    if (s.includes('presentar') || s.includes('inscripcion')) return 'bg-purple-500/40 text-purple-50 border-purple-500/60';
    if (s.includes('retiro') || s.includes('not personal')) return 'bg-red-500/40 text-red-50 border-red-500/60';
    if (s.includes('completado') || s.includes('finalizado') || s.includes('cerrado')) return 'bg-green-500/40 text-green-50 border-green-500/60';
    return 'bg-amber-500/40 text-amber-50 border-amber-500/60';
  };

  const statusOptions = useMemo(() => {
    const base = ['ALMP', 'INSCRIPCION MEDIDAS', 'NOT PERSONAL', 'NOT AVISO', 'EMPLAZAMIENTO', '468', 'LIQUIDACION', 'AVALUO', 'REMATE', 'COMPLETO'];
    const combined = Array.from(new Set([...base, ...allStatuses])).filter(Boolean);
    return combined;
  }, [allStatuses]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[1250px] p-0 bg-[#252833] border-white/20 text-slate-100 overflow-hidden flex flex-col shadow-2xl">
        <div className="flex flex-1 overflow-hidden h-full">
          {/* LEFT PANE: DETAILS */}
          <div className="flex-[2] flex flex-col border-r border-white/10 overflow-hidden bg-[#1e2128]">
             <ScrollArea className="flex-1">
                <div className="p-10 space-y-10">
                   {/* HEADER: ID & CONTROLS */}
                   <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                         <Badge variant="outline" className="bg-primary/30 text-primary border-primary/50 font-black text-[11px] uppercase tracking-widest px-4 py-2 shadow-md">
                           ID: {displayTask.clickup_id || displayTask.id}
                         </Badge>
                         <div className="flex items-center gap-2 text-[10px] text-slate-300 bg-white/10 px-4 py-2 rounded-full border border-white/20 shadow-inner font-bold">
                           <Activity className="h-4 w-4 text-primary animate-pulse" />
                           <span>MODO EXPERTO ACTIVADO</span>
                         </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white hover:bg-white/10"><Smile className="h-5 w-5"/></Button>
                        <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white hover:bg-white/10"><MoreHorizontal className="h-5 w-5"/></Button>
                        <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="rounded-full hover:bg-white/20 ml-2 h-10 w-10">
                          <X className="h-6 w-6" />
                        </Button>
                      </div>
                   </div>

                   {/* TITLE & STATUS */}
                   <div className="space-y-8">
                      <div className="flex items-center gap-4 flex-wrap">
                        <Select value={displayTask.status || 'ABIERTO'} onValueChange={(v) => handleSave({ status: v })}>
                          <SelectTrigger className={`w-auto min-w-[160px] h-11 px-5 rounded-2xl border-2 font-black text-[11px] uppercase tracking-[0.15em] transition-all shadow-xl ${getStatusColor(displayTask.status)} hover:scale-105 active:scale-95`}>
                            <div className="flex items-center gap-3">
                               <div className={`h-3 w-3 rounded-full border border-white/30 ${getStatusColor(displayTask.status).split(' ')[1].replace('text-', 'bg-')}`} />
                               <SelectValue />
                            </div>
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-white/20 text-white max-h-[500px] shadow-2xl">
                            {statusOptions.map(s => (
                              <SelectItem key={s} value={s} className="uppercase text-[11px] font-black tracking-widest py-3 border-b border-white/5 last:border-0 hover:bg-white/5">{s}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        <Popover>
                          <PopoverTrigger asChild>
                            <div className="flex items-center gap-3 px-5 py-2.5 bg-white/10 rounded-2xl border border-white/20 cursor-pointer hover:bg-white/20 transition-all shadow-lg group">
                               <UserIcon className="h-5 w-5 text-primary group-hover:rotate-12 transition-transform" />
                               <div className="flex -space-x-2.5 overflow-hidden">
                                  {displayTask.assignees?.map((a, i) => (
                                    <Avatar key={i} className="h-7 w-7 border-2 border-[#1e2128] shadow-xl">
                                      <AvatarFallback className="text-[10px] bg-primary text-primary-foreground font-black">{(a.nombre || a.username)[0]}</AvatarFallback>
                                    </Avatar>
                                  ))}
                                  {(!displayTask.assignees || displayTask.assignees.length === 0) && (
                                    <span className="text-[11px] font-black text-slate-100 uppercase tracking-widest ml-1 drop-shadow-sm">
                                      {displayTask.assignee_name || 'Sin Asignar'}
                                    </span>
                                  )}
                               </div>
                               <ChevronDown className="h-4 w-4 text-slate-500 group-hover:text-white" />
                            </div>
                          </PopoverTrigger>
                          <PopoverContent className="w-72 p-3 bg-slate-800 border-white/20 text-white rounded-3xl shadow-2xl backdrop-blur-xl">
                             <ScrollArea className="h-[300px]">
                                <div className="space-y-1.5">
                                   {users.map(u => (
                                     <div key={u.id} className="flex items-center gap-3 p-3 hover:bg-white/10 rounded-2xl cursor-pointer transition-all border border-transparent hover:border-white/10" onClick={() => handleToggleAssignee(u.id)}>
                                        <Checkbox checked={displayTask.assignees?.some(a => a.id === u.id)} className="h-5 w-5 border-white/30 data-[state=checked]:bg-primary" />
                                        <Avatar className="h-8 w-8">
                                           <AvatarFallback className="text-xs font-black bg-primary/20 text-primary">{(u.nombre || u.username)[0]}</AvatarFallback>
                                        </Avatar>
                                        <span className="text-sm font-bold">{(u.nombre || u.username)}</span>
                                     </div>
                                   ))}
                                </div>
                             </ScrollArea>
                          </PopoverContent>
                        </Popover>

                        <Select value={displayTask.priority || 'normal'} onValueChange={(v) => handleSave({ priority: v })}>
                          <SelectTrigger className={`w-auto h-11 px-5 rounded-2xl bg-white/10 border border-white/20 font-black text-[11px] uppercase tracking-[0.15em] transition-all shadow-lg ${displayTask.priority === 'urgent' ? 'text-red-400 border-red-500/50' : 'text-slate-300'}`}>
                            <div className="flex items-center gap-3">
                              <Flag className={`h-4 w-4 ${displayTask.priority === 'urgent' ? 'fill-red-500' : 'fill-slate-500'}`} />
                              <SelectValue />
                            </div>
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-white/20 text-white rounded-2xl shadow-2xl">
                            <SelectItem value="urgent" className="text-red-400 font-black">URGENTE</SelectItem>
                            <SelectItem value="high">ALTA</SelectItem>
                            <SelectItem value="normal">NORMAL</SelectItem>
                            <SelectItem value="low">BAJA</SelectItem>
                          </SelectContent>
                        </Select>

                        <div className="flex-1 min-w-[250px]">
                           <div className="flex flex-wrap gap-2.5 items-center bg-white/5 p-2 rounded-2xl border border-white/10 shadow-inner">
                              {displayTask.tags?.map(tag => (
                                <Badge 
                                  key={tag.id}
                                  style={{ backgroundColor: tag.color || '#3b82f6', color: 'white' }}
                                  className="text-[10px] py-2 px-4 border-none shadow-xl font-black uppercase tracking-widest rounded-xl flex items-center gap-2 group cursor-pointer hover:brightness-125 transform hover:-translate-y-0.5 transition-all"
                                  onClick={() => handleTagToggle(tag.name)}
                                >
                                  {tag.name}
                                  <X className="h-3.5 w-3.5 opacity-50 group-hover:opacity-100 transition-opacity" />
                                </Badge>
                              ))}
                              <Popover>
                                <PopoverTrigger asChild>
                                  <Button variant="ghost" size="sm" className="h-9 px-5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 text-[10px] font-black text-slate-100 uppercase tracking-widest shadow-md flex items-center gap-2">
                                    <Tag className="h-4 w-4 text-primary" /> ETIQUETAS
                                  </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-72 p-3 bg-slate-800 border-white/20 text-white rounded-3xl shadow-2xl backdrop-blur-xl">
                                   <ScrollArea className="h-[300px]">
                                      <div className="space-y-1.5">
                                         {allTags.map(t => (
                                           <div key={t.id} className="flex items-center gap-3 p-3 hover:bg-white/10 rounded-2xl cursor-pointer text-sm font-bold transition-all border border-transparent hover:border-white/10" onClick={() => handleTagToggle(t.name)}>
                                              <div className="h-4 w-4 rounded-full shadow-lg border border-white/20" style={{ backgroundColor: t.color }} />
                                              <span className="flex-1">{t.name}</span>
                                              {displayTask.tags?.some(gt => gt.name === t.name) && <CheckCircle2 className="h-4 w-4 text-primary" />}
                                           </div>
                                         ))}
                                         {allTags.length === 0 && <p className="p-6 text-center text-xs text-slate-400 italic font-medium">Cargando etiquetas...</p>}
                                      </div>
                                   </ScrollArea>
                                </PopoverContent>
                              </Popover>
                           </div>
                        </div>
                      </div>

                      <input 
                        className="w-full bg-transparent text-5xl font-black tracking-tighter border-none focus:ring-0 p-0 text-white placeholder:text-slate-700 shadow-none selection:bg-primary/30"
                        value={editedTitle}
                        onChange={(e) => setEditedTitle(e.target.value)}
                        onBlur={() => handleSave({ title: editedTitle })}
                        placeholder="Sin título de gestión..."
                      />
                   </div>

                   {/* CUSTOM FIELDS / CASE LINK */}
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-10 bg-white/5 p-10 rounded-[2.5rem] border border-white/20 shadow-2xl relative overflow-hidden group">
                      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                      
                      <div className="space-y-8">
                         <div className="text-[11px] font-black uppercase text-slate-400 tracking-[0.2em] flex items-center gap-3">
                           <Layout className="h-4 w-4 text-primary" /> INFORMACIÓN DE CARPETA
                         </div>
                         <div className="space-y-5">
                            {(() => {
                               try {
                                 const fields = JSON.parse(displayTask.custom_fields || '[]');
                                 if (Array.isArray(fields) && fields.length > 0) {
                                   return fields.map((f: any, idx: number) => (
                                     <div key={idx} className="flex justify-between items-center py-3.5 border-b border-white/10 group/item">
                                        <span className="text-[11px] text-slate-400 font-black uppercase tracking-tight group-hover/item:text-primary transition-colors">{f.name}</span>
                                        <span className="text-[13px] text-white font-black bg-white/10 px-3 py-1 rounded-xl shadow-sm border border-white/5">{f.value || f.text_value || '-'}</span>
                                     </div>
                                   ));
                                 }
                               } catch (e) {}
                               return (
                                 <div className="p-8 text-center text-[11px] text-slate-500 uppercase font-black italic tracking-widest bg-black/20 rounded-3xl border border-dashed border-white/10">No hay campos personalizados</div>
                               );
                            })()}
                         </div>
                      </div>
                      <div className="space-y-8">
                        <div className="text-[11px] font-black uppercase text-slate-400 tracking-[0.2em] flex items-center gap-3">
                           <Zap className="h-4 w-4 text-yellow-500" /> EXPEDIENTE VINCULADO
                         </div>
                         <div className="p-7 bg-black/40 rounded-3xl border border-white/20 hover:border-primary/50 transition-all cursor-pointer group shadow-2xl relative">
                            <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-3xl" />
                            <div className="text-lg font-black text-primary truncate mb-3 relative z-10">{displayTask.case_radicado || '11001400305420250052800'}</div>
                            <div className="flex items-center gap-3 text-[11px] text-slate-300 uppercase tracking-widest font-black relative z-10">
                               <div className="h-8 w-8 rounded-xl bg-primary/20 flex items-center justify-center text-primary border border-primary/20">
                                  <UserCheck className="h-4 w-4" />
                               </div>
                               <span>Ver Detalles del Proceso</span>
                               <ChevronRight className="h-4 w-4 ml-auto text-primary group-hover:translate-x-1 transition-transform" />
                            </div>
                         </div>
                      </div>
                   </div>

                   {/* DESCRIPTION */}
                   <div className="space-y-6">
                      <div className="flex items-center gap-3 text-[11px] font-black uppercase tracking-[0.25em] text-slate-400">
                        <Edit3 className="h-5 w-5 text-primary" /> NOTAS TÉCNICAS DE GESTIÓN
                      </div>
                      <Textarea 
                        className="min-h-[220px] bg-white/5 border-2 border-white/10 focus:border-primary/50 rounded-[2rem] p-10 text-[15px] font-medium leading-relaxed text-slate-100 resize-none transition-all placeholder:text-slate-700 shadow-xl focus:bg-white/[0.07] selection:bg-primary/30"
                        placeholder="Ingresa la actualización jurídica o detalles relevantes..."
                        value={editedDesc}
                        onChange={(e) => setEditedDesc(e.target.value)}
                        onBlur={() => handleSave({ description: editedDesc })}
                      />
                   </div>

                   {/* SUBTASKS / CHECKLISTS */}
                   <div className="space-y-10">
                      <div className="space-y-8">
                         <div className="flex items-center justify-between bg-white/5 p-6 rounded-3xl border border-white/10">
                            <div className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-300 flex items-center gap-3">
                               <CalendarPlus className="h-6 w-6 text-primary" /> SUBTAREAS Y CRONOGRAMA
                            </div>
                            <Button size="sm" onClick={() => setShowSubtaskForm(true)} className="rounded-2xl bg-primary text-primary-foreground font-black uppercase text-[11px] tracking-widest px-8 h-10 shadow-lg shadow-primary/30 hover:scale-105 transition-transform">
                               <Plus className="h-5 w-5 mr-2" /> NUEVA SUBTAREA
                            </Button>
                         </div>
                         
                         <div className="space-y-5">
                            {/* Subtask Creation Form */}
                            <AnimatePresence>
                              {showSubtaskForm && (
                                <motion.div 
                                  initial={{ opacity: 0, scale: 0.95 }} 
                                  animate={{ opacity: 1, scale: 1 }} 
                                  exit={{ opacity: 0, scale: 0.95 }}
                                  className="p-10 bg-primary/10 border-2 border-primary/30 rounded-[2.5rem] space-y-8 shadow-2xl relative overflow-hidden"
                                >
                                   <div className="flex items-center justify-between mb-2">
                                      <h3 className="text-sm font-black uppercase tracking-widest text-primary">Configurar Nueva Subtarea</h3>
                                      <Button variant="ghost" size="icon" onClick={() => setShowSubtaskForm(false)} className="rounded-full h-8 w-8 text-primary hover:bg-primary/20">
                                         <X className="h-4 w-4" />
                                      </Button>
                                   </div>
                                   <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                      <div className="space-y-3">
                                         <label className="text-[10px] font-black text-primary/70 uppercase ml-2">Título de la Gestión</label>
                                         <Input 
                                           placeholder="Ej: Radicar memorial de subsanación..." 
                                           value={newSubtaskTitle} 
                                           onChange={(e) => setNewSubtaskTitle(e.target.value)}
                                           className="bg-black/30 border-white/20 h-12 rounded-2xl focus:border-primary text-sm font-bold shadow-inner"
                                         />
                                      </div>
                                      <div className="space-y-3">
                                         <label className="text-[10px] font-black text-primary/70 uppercase ml-2">Fecha Límite (Opcional)</label>
                                         <div className="relative">
                                            <Input 
                                              type="date"
                                              value={newSubtaskDate}
                                              onChange={(e) => setNewSubtaskDate(e.target.value)}
                                              className="bg-black/30 border-white/20 h-12 rounded-2xl pl-12 focus:border-primary text-sm font-bold shadow-inner"
                                            />
                                            <CalendarDays className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-primary" />
                                         </div>
                                      </div>
                                   </div>
                                   <div className="flex justify-end gap-4 pt-2">
                                      <Button variant="ghost" size="lg" onClick={() => setShowSubtaskForm(false)} className="rounded-2xl text-xs font-black uppercase tracking-widest text-slate-400 hover:text-white">Cancelar</Button>
                                      <Button size="lg" onClick={handleCreateSubtask} className="rounded-2xl bg-primary text-primary-foreground font-black uppercase text-xs tracking-widest px-10 shadow-xl shadow-primary/30">CREAR GESTIÓN</Button>
                                   </div>
                                </motion.div>
                              )}
                            </AnimatePresence>

                            {/* Checklist items */}
                            {displayTask.checklists?.map(item => (
                              <div key={item.id} className="flex items-center gap-6 p-6 bg-white/5 border-2 border-white/10 rounded-3xl group hover:bg-white/[0.08] transition-all shadow-xl hover:border-primary/20">
                                 <Checkbox 
                                   checked={item.is_completed} 
                                   onCheckedChange={(v) => updateChecklistItem(item.id, { is_completed: !!v }).then(refreshTask)} 
                                   className="h-6 w-6 border-2 border-white/30 data-[state=checked]:bg-green-500 data-[state=checked]:border-green-500 shadow-sm"
                                 />
                                 <span className={`text-[15px] flex-1 font-bold tracking-tight ${item.is_completed ? 'line-through text-slate-500' : 'text-slate-100'}`}>{item.content}</span>
                                 <Button variant="ghost" size="icon" onClick={() => deleteChecklistItem(item.id).then(refreshTask)} className="h-10 w-10 text-slate-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-red-500/10 rounded-2xl">
                                    <Trash2 className="h-5 w-5" />
                                 </Button>
                              </div>
                            ))}

                            <div className="flex items-center gap-5 bg-white/[0.03] border-2 border-dashed border-white/20 rounded-3xl p-3 pl-8 hover:border-primary/50 transition-all group shadow-inner">
                               <Plus className="h-6 w-6 text-slate-600 group-hover:text-primary transition-colors" />
                               <Input 
                                 placeholder="Añadir paso rápido a la lista de gestión..." 
                                 value={newChecklist} 
                                 onChange={(e) => setNewChecklist(e.target.value)}
                                 onKeyDown={(e) => e.key === 'Enter' && handleAddChecklist()}
                                 className="bg-transparent border-none focus:ring-0 text-[15px] font-bold p-0 h-14 placeholder:text-slate-700 selection:bg-primary/20"
                               />
                               <Button size="lg" onClick={handleAddChecklist} className="rounded-2xl h-12 px-8 bg-primary/20 text-primary hover:bg-primary/30 border-2 border-primary/20 font-black uppercase text-[11px] tracking-widest shadow-md">AÑADIR PASO</Button>
                            </div>
                         </div>
                      </div>
                   </div>
                </div>
             </ScrollArea>
          </div>

          {/* RIGHT PANE: ACTIVITY / COMMENTS */}
          <div className="flex-1 flex flex-col bg-[#1a1c23] overflow-hidden border-l border-white/10 shadow-2xl">
             <div className="h-20 flex items-center px-10 border-b-2 border-white/10 gap-10 bg-white/5 backdrop-blur-md">
                <button 
                  onClick={() => setActiveRightTab('activity')}
                  className={`text-[11px] font-black uppercase tracking-[0.25em] transition-all h-full flex items-center border-b-4 ${activeRightTab === 'activity' ? 'text-primary border-primary' : 'text-slate-500 border-transparent hover:text-slate-300'}`}
                >
                  ACTIVIDAD
                </button>
                <button 
                  onClick={() => setActiveRightTab('comments')}
                  className={`text-[11px] font-black uppercase tracking-[0.25em] transition-all h-full flex items-center border-b-4 ${activeRightTab === 'comments' ? 'text-primary border-primary' : 'text-slate-500 border-transparent hover:text-slate-300'}`}
                >
                  MENSAJES
                </button>
             </div>

             <ScrollArea className="flex-1 bg-black/10">
                <div className="p-10 space-y-12">
                   {displayTask.comments?.map(comment => (
                     <div key={comment.id} className="flex gap-5 group">
                        <Avatar className="h-12 w-12 flex-shrink-0 shadow-2xl ring-4 ring-white/5 transition-transform group-hover:scale-110">
                           <AvatarFallback className="text-sm font-black bg-primary text-primary-foreground uppercase">{(comment.user_name || 'U')[0]}</AvatarFallback>
                        </Avatar>
                        <div className="space-y-3 flex-1">
                           <div className="flex items-center justify-between">
                              <span className="text-xs font-black text-slate-200 uppercase tracking-widest">{comment.user_name}</span>
                              <span className="text-[10px] text-slate-500 font-bold bg-white/5 px-2 py-0.5 rounded-lg border border-white/5">{format(new Date(comment.created_at), "d MMM, h:mm a", { locale: es })}</span>
                           </div>
                           <div className="p-6 bg-white/[0.07] border-2 border-white/10 rounded-[2rem] rounded-tl-none text-[14px] font-medium text-slate-100 leading-relaxed shadow-xl group-hover:bg-white/[0.1] transition-all group-hover:border-primary/20">
                              {comment.content}
                           </div>
                        </div>
                     </div>
                   ))}

                   {(!displayTask.comments || displayTask.comments.length === 0) && (
                     <div className="h-[400px] flex flex-col items-center justify-center text-slate-700 opacity-20">
                        <div className="relative mb-8">
                           <MessageSquare className="h-24 w-24 stroke-1" />
                           <Activity className="absolute bottom-0 right-0 h-8 w-8 text-primary animate-pulse" />
                        </div>
                        <p className="text-[13px] font-black uppercase tracking-[0.3em]">CANAL DE GESTIÓN VACÍO</p>
                        <p className="text-[11px] font-bold mt-3 tracking-widest opacity-60">Sincroniza el primer mensaje para este caso</p>
                     </div>
                   )}
                </div>
             </ScrollArea>

             <div className="p-10 border-t-2 border-white/10 bg-[#252833]/80 backdrop-blur-2xl">
                <div className="relative group/input">
                   <div className="absolute inset-0 bg-primary/5 rounded-[2.5rem] blur-2xl opacity-0 group-hover/input:opacity-100 transition-opacity" />
                   <Textarea 
                     value={newComment}
                     onChange={(e) => setNewComment(e.target.value)}
                     placeholder="Escribe un mensaje técnico o actualización..."
                     className="bg-black/40 border-2 border-white/20 focus:border-primary/60 rounded-[2.5rem] pr-20 min-h-[140px] resize-none text-[15px] font-bold p-8 shadow-2xl relative z-10 transition-all placeholder:text-slate-600 focus:bg-black/60"
                   />
                   <Button 
                     size="icon" 
                     onClick={handleAddComment}
                     disabled={!newComment.trim()}
                     className="absolute bottom-6 right-6 h-12 w-12 rounded-[1.5rem] bg-primary hover:bg-primary/90 text-primary-foreground shadow-[0_10px_30px_rgba(var(--primary),0.4)] transform hover:scale-110 active:scale-95 transition-all z-20"
                   >
                     <Send className="h-6 w-6" />
                   </Button>
                </div>
             </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
