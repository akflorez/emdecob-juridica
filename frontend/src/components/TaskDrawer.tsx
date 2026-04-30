import { useState, useEffect, useMemo } from "react";
import { 
  X, Calendar as CalendarIcon, User as UserIcon, CheckCircle2, 
  Clock, Tag, Paperclip, MessageSquare, Plus, ChevronRight, 
  Send, Trash2, ListChecks, Zap, Flag, AlertCircle, Edit3,
  UserCheck, Search, Activity, CornerDownRight, Smile, MoreHorizontal,
  ChevronDown, CalendarDays, Layout
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
  updateTask, addComment, deleteComment,
  addChecklistItem, updateChecklistItem, deleteChecklistItem,
  getUsers, getTags, getTaskDetail, createTask,
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
  
  const [showSubtaskForm, setShowSubtaskForm] = useState(false);
  const [newSubtaskTitle, setNewSubtaskTitle] = useState("");
  const [newSubtaskDate, setNewSubtaskDate] = useState("");

  const displayTask = fullTask || task;

  useEffect(() => {
    if (task && open) {
      setEditedTitle(task.title || '');
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
    const currentIds = displayTask.assignees?.map(a => a.id) || [];
    let newIds: number[];
    if (currentIds.includes(userId)) {
      newIds = currentIds.filter(id => id !== userId);
    } else {
      newIds = [...currentIds, userId];
    }
    handleSave({ assignee_ids: newIds } as any);
  };

  const toggleTag = (tagName: string) => {
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
      setShowSubtaskForm(false);
      refreshTask();
      toast({ title: "Subtarea creada" });
    } catch (error) {
      toast({ title: "Error al crear", variant: "destructive" });
    }
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

  const handleAddChecklist = async () => {
    if (!displayTask || !newChecklist.trim()) return;
    try {
      await addChecklistItem(displayTask.id, newChecklist);
      setNewChecklist("");
      refreshTask();
    } catch (error) {
      toast({ title: "Error al añadir item" });
    }
  };

  if (!displayTask) return null;

  const statusOptions = Array.from(new Set([
    'ABIERTO', 'TO DO', 'IN PROGRESS', 'PENDIENTE', 'ALMP', '468', 'COMPLETO', 'CLOSED',
    ...(allStatuses || [])
  ])).filter(Boolean);

  const currentStatus = (displayTask.status || 'ABIERTO').toUpperCase();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[1200px] p-0 bg-[#252833] border-white/20 text-slate-100 flex flex-col shadow-2xl">
        <SheetHeader className="sr-only">
          <SheetTitle>Detalle de Tarea</SheetTitle>
        </SheetHeader>
        
        <div className="flex flex-1 overflow-hidden h-full">
          <div className="flex-[2] flex flex-col border-r border-white/10 overflow-hidden bg-[#1e2128]">
             <ScrollArea className="flex-1">
                <div className="p-8 space-y-8">
                   <div className="flex items-center justify-between">
                      <Badge className="bg-primary/30 text-primary border-primary/50 font-black px-4 py-2 uppercase tracking-widest text-[11px]">
                        ID: {displayTask.clickup_id || displayTask.id}
                      </Badge>
                      <div className="flex items-center gap-2 text-[10px] text-slate-300 bg-white/10 px-4 py-2 rounded-full border border-white/20 font-bold">
                        <Activity className="h-4 w-4 text-primary" />
                        <span>CONSOLA DE MANDO</span>
                      </div>
                      <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="rounded-full hover:bg-white/20 h-10 w-10">
                        <X className="h-6 w-6" />
                      </Button>
                   </div>

                   <div className="space-y-6">
                      <div className="flex items-center gap-4 flex-wrap">
                        <Select value={statusOptions.includes(currentStatus) ? currentStatus : undefined} onValueChange={(v) => handleSave({ status: v })}>
                          <SelectTrigger className="w-auto min-w-[160px] h-10 px-5 rounded-2xl border-2 font-black text-[10px] uppercase tracking-widest bg-white/5 border-white/20 shadow-xl">
                            <SelectValue placeholder={currentStatus} />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-white/20 text-white shadow-2xl">
                            {statusOptions.map(s => (
                              <SelectItem key={s} value={s} className="uppercase text-[10px] font-black tracking-widest py-3">{s}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        <Popover>
                          <PopoverTrigger asChild>
                            <div className="flex items-center gap-3 px-5 py-2.5 bg-white/10 rounded-2xl border border-white/20 cursor-pointer hover:bg-white/20 transition-all font-black text-[11px] uppercase tracking-widest shadow-lg">
                               <UserIcon className="h-4 w-4 text-primary" />
                               <span className="max-w-[300px] truncate">
                                 {displayTask.assignees && displayTask.assignees.length > 0 
                                   ? displayTask.assignees.map(a => a.nombre || a.username).join(', ') 
                                   : displayTask.assignee_name || 'Asignar Abogados'}
                               </span>
                               <ChevronDown className="h-4 w-4 text-slate-500" />
                            </div>
                          </PopoverTrigger>
                          <PopoverContent className="w-80 p-3 bg-slate-800 border-white/20 text-white rounded-3xl shadow-2xl">
                             <div className="px-3 pb-3 border-b border-white/10 mb-2">
                                <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Listado de Abogados</span>
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
                                </div>
                             </ScrollArea>
                          </PopoverContent>
                        </Popover>
                        
                        <div className="flex-1 min-w-[200px]">
                           <div className="flex flex-wrap gap-2.5 items-center bg-white/5 p-2 rounded-2xl border border-white/10">
                              {displayTask.tags?.map(tag => (
                                <Badge key={tag.id} style={{ backgroundColor: tag.color || '#3b82f6', color: 'white' }} className="text-[10px] py-2 px-4 border-none font-black uppercase tracking-widest rounded-xl shadow-md group cursor-pointer hover:brightness-110" onClick={() => toggleTag(tag.name)}>
                                  {tag.name}
                                  <X className="h-3 w-3 ml-2 opacity-50 group-hover:opacity-100" />
                                </Badge>
                              ))}
                              <Popover>
                                <PopoverTrigger asChild>
                                  <Button variant="ghost" size="sm" className="h-9 px-4 rounded-xl bg-white/10 hover:bg-white/20 text-[10px] font-black text-slate-100 uppercase tracking-widest shadow-md">
                                    <Tag className="h-4 w-4 mr-2 text-primary" /> + ETIQUETAS
                                  </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-72 p-3 bg-slate-800 border-white/20 text-white rounded-3xl shadow-2xl">
                                   <ScrollArea className="h-[300px]">
                                      <div className="space-y-1">
                                         {allTags.map(t => (
                                           <div key={t.id} className="flex items-center gap-3 p-3 hover:bg-white/10 rounded-2xl cursor-pointer text-sm font-bold transition-all" onClick={() => toggleTag(t.name)}>
                                              <div className="h-4 w-4 rounded-full" style={{ backgroundColor: t.color }} />
                                              <span className="flex-1">{t.name}</span>
                                              {displayTask.tags?.some(gt => gt.name === t.name) && <CheckCircle2 className="h-4 w-4 text-primary" />}
                                           </div>
                                         ))}
                                         {allTags.length === 0 && <p className="p-6 text-center text-[10px] text-slate-500 font-black uppercase italic">Cargando etiquetas...</p>}
                                      </div>
                                   </ScrollArea>
                                </PopoverContent>
                              </Popover>
                           </div>
                        </div>
                      </div>

                      <input 
                        className="w-full bg-transparent text-4xl font-black tracking-tighter border-none focus:ring-0 p-0 text-white placeholder:text-slate-700 shadow-none selection:bg-primary/30"
                        value={editedTitle}
                        onChange={(e) => setEditedTitle(e.target.value)}
                        onBlur={() => handleSave({ title: editedTitle })}
                        placeholder="Sin título..."
                      />
                   </div>

                   <div className="grid grid-cols-1 md:grid-cols-2 gap-10 bg-white/5 p-10 rounded-[2.5rem] border border-white/20 shadow-2xl relative overflow-hidden group">
                      <div className="space-y-6">
                         <div className="text-[11px] font-black uppercase text-slate-400 tracking-[0.2em] flex items-center gap-3">
                           <Layout className="h-4 w-4 text-primary" /> INFORMACIÓN DE CARPETA
                         </div>
                         <div className="space-y-5">
                            {(() => {
                               try {
                                 const fields = JSON.parse(displayTask.custom_fields || '[]');
                                 if (Array.isArray(fields) && fields.length > 0) {
                                   return fields.map((f: any, idx: number) => (
                                     <div key={idx} className="flex justify-between items-center py-3.5 border-b border-white/10">
                                        <span className="text-[11px] text-slate-400 font-black uppercase tracking-tight">{f.name}</span>
                                        <span className="text-[13px] text-white font-black bg-white/10 px-3 py-1 rounded-xl shadow-sm border border-white/5">{f.value || f.text_value || '-'}</span>
                                     </div>
                                   ));
                                 }
                               } catch (e) {}
                               return <div className="p-8 text-center text-[11px] text-slate-500 uppercase font-black italic tracking-widest bg-black/20 rounded-3xl border border-dashed border-white/10">Sin campos personalizados</div>;
                            })()}
                         </div>
                      </div>
                      <div className="space-y-6">
                        <div className="text-[11px] font-black uppercase text-slate-400 tracking-[0.2em] flex items-center gap-3">
                           <Zap className="h-4 w-4 text-yellow-500" /> EXPEDIENTE VINCULADO
                         </div>
                         <div className="p-7 bg-black/40 rounded-3xl border border-white/20 hover:border-primary/50 transition-all cursor-pointer group shadow-2xl relative">
                            <div className="text-lg font-black text-primary truncate mb-3">{displayTask.case_radicado || '11001400305420250052800'}</div>
                            <div className="flex items-center gap-3 text-[11px] text-slate-300 uppercase tracking-widest font-black">
                               <div className="h-8 w-8 rounded-xl bg-primary/20 flex items-center justify-center text-primary border border-primary/20">
                                  <UserCheck className="h-4 w-4" />
                               </div>
                               <span>Detalles del Proceso</span>
                               <ChevronRight className="h-4 w-4 ml-auto text-primary" />
                            </div>
                         </div>
                      </div>
                   </div>

                   <div className="space-y-6">
                      <div className="flex items-center gap-3 text-[11px] font-black uppercase tracking-[0.2em] text-slate-400">
                        <Edit3 className="h-5 w-5 text-primary" /> NOTAS DE GESTIÓN
                      </div>
                      <Textarea 
                        className="min-h-[220px] bg-white/5 border-2 border-white/10 focus:border-primary/50 rounded-[2.5rem] p-8 text-[15px] font-medium leading-relaxed text-slate-100 shadow-xl placeholder:text-slate-700 selection:bg-primary/30"
                        placeholder="Ingresa la actualización jurídica o detalles relevantes..."
                        value={editedDesc}
                        onChange={(e) => setEditedDesc(e.target.value)}
                        onBlur={() => handleSave({ description: editedDesc })}
                      />
                   </div>

                   <div className="space-y-10">
                      <div className="flex items-center justify-between bg-white/5 p-6 rounded-3xl border border-white/10">
                         <div className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-300 flex items-center gap-3">
                            <Activity className="h-6 w-6 text-primary" /> SUBTAREAS Y CRONOGRAMA
                         </div>
                         <Button size="sm" onClick={() => setShowSubtaskForm(true)} className="rounded-2xl bg-primary text-primary-foreground font-black uppercase text-[11px] tracking-widest px-8 h-10 shadow-lg shadow-primary/30 hover:scale-105 transition-transform">
                            <Plus className="h-5 w-5 mr-2" /> NUEVA SUBTAREA
                         </Button>
                      </div>
                      <div className="space-y-5">
                         {showSubtaskForm && (
                           <div className="p-10 bg-primary/10 border-2 border-primary/30 rounded-[2.5rem] space-y-8 shadow-2xl">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                 <div className="space-y-2">
                                    <label className="text-[10px] font-black text-primary/70 uppercase ml-2">Título de la Gestión</label>
                                    <Input placeholder="Título de la subtarea..." value={newSubtaskTitle} onChange={(e) => setNewSubtaskTitle(e.target.value)} className="bg-black/30 border-white/20 h-12 rounded-2xl text-sm font-bold" />
                                 </div>
                                 <div className="space-y-2">
                                    <label className="text-[10px] font-black text-primary/70 uppercase ml-2">Fecha Límite</label>
                                    <Input type="date" value={newSubtaskDate} onChange={(e) => setNewSubtaskDate(e.target.value)} className="bg-black/30 border-white/20 h-12 rounded-2xl pl-4 text-sm font-bold" />
                                 </div>
                              </div>
                              <div className="flex justify-end gap-4">
                                 <Button variant="ghost" onClick={() => setShowSubtaskForm(false)} className="rounded-2xl text-xs font-black uppercase tracking-widest text-slate-400 hover:text-white">Cancelar</Button>
                                 <Button onClick={handleCreateSubtask} className="rounded-2xl bg-primary text-primary-foreground font-black uppercase text-xs tracking-widest px-10">CREAR GESTIÓN</Button>
                              </div>
                           </div>
                         )}
                         {displayTask.checklists?.map(item => (
                           <div key={item.id} className="flex items-center gap-6 p-6 bg-white/5 border-2 border-white/10 rounded-3xl group hover:bg-white/[0.08] transition-all shadow-xl">
                              <Checkbox checked={item.is_completed} onCheckedChange={(v) => updateChecklistItem(item.id, { is_completed: !!v }).then(refreshTask)} className="h-6 w-6 border-2 border-white/30 data-[state=checked]:bg-green-500 data-[state=checked]:border-green-500 shadow-sm" />
                              <span className={`text-[15px] flex-1 font-bold tracking-tight ${item.is_completed ? 'line-through text-slate-500' : 'text-slate-100'}`}>{item.content}</span>
                              <Button variant="ghost" size="icon" onClick={() => deleteChecklistItem(item.id).then(refreshTask)} className="h-10 w-10 text-slate-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all rounded-2xl">
                                 <Trash2 className="h-5 w-5" />
                              </Button>
                           </div>
                         ))}
                         <div className="flex items-center gap-5 bg-white/[0.03] border-2 border-dashed border-white/20 rounded-3xl p-3 pl-8 hover:border-primary/50 transition-all group shadow-inner">
                            <Plus className="h-6 w-6 text-slate-600" />
                            <Input placeholder="Añadir paso rápido a la lista de gestión..." value={newChecklist} onChange={(e) => setNewChecklist(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleAddChecklist()} className="bg-transparent border-none focus:ring-0 text-[15px] font-bold p-0 h-14" />
                            <Button size="lg" onClick={handleAddChecklist} className="rounded-2xl h-12 px-8 bg-primary/20 text-primary hover:bg-primary/30 border-2 border-primary/20 font-black uppercase text-[11px] tracking-widest shadow-md">AÑADIR PASO</Button>
                         </div>
                      </div>
                   </div>
                </div>
             </ScrollArea>
          </div>

          <div className="flex-1 flex flex-col bg-[#1a1c23] border-l border-white/10 shadow-2xl overflow-hidden">
             <div className="h-20 flex items-center px-10 border-b-2 border-white/10 font-black text-[11px] uppercase tracking-[0.25em] gap-10 bg-white/5">
                <span className="text-primary border-b-4 border-primary h-full flex items-center">ACTIVIDAD</span>
             </div>
             <ScrollArea className="flex-1 bg-black/10">
                <div className="p-10 space-y-10">
                   {displayTask.comments?.map(comment => (
                     <div key={comment.id} className="flex gap-5">
                        <div className="h-10 w-10 flex-shrink-0 shadow-2xl rounded-full bg-primary flex items-center justify-center text-white font-black uppercase text-xs">
                           {(comment.user_name || 'U')[0]}
                        </div>
                        <div className="flex-1 space-y-3">
                           <div className="flex justify-between items-center">
                              <span className="text-xs font-black text-slate-200 uppercase tracking-widest">{comment.user_name}</span>
                              <span className="text-[10px] text-slate-600 font-bold bg-white/5 px-2 py-0.5 rounded-lg border border-white/5">
                                 {isValid(new Date(comment.created_at)) ? format(new Date(comment.created_at), "d MMM", { locale: es }) : ''}
                              </span>
                           </div>
                           <div className="p-6 bg-white/[0.07] border-2 border-white/10 rounded-[2rem] rounded-tl-none text-[14px] font-medium text-slate-100 leading-relaxed shadow-xl">
                              {comment.content}
                           </div>
                        </div>
                     </div>
                   ))}
                </div>
             </ScrollArea>
             <div className="p-10 border-t-2 border-white/10 bg-[#252833]/80 backdrop-blur-2xl">
                <div className="relative group/input">
                   <Textarea 
                     value={newComment}
                     onChange={(e) => setNewComment(e.target.value)}
                     placeholder="Escribe un mensaje técnico..."
                     className="bg-black/40 border-2 border-white/20 focus:border-primary/60 rounded-[2.5rem] pr-20 min-h-[140px] resize-none text-[15px] font-bold p-8 shadow-2xl relative z-10 transition-all placeholder:text-slate-600 focus:bg-black/60"
                   />
                   <Button size="icon" onClick={handleAddComment} disabled={!newComment.trim()} className="absolute bottom-6 right-6 h-12 w-12 rounded-[1.5rem] bg-primary hover:bg-primary/90 text-primary-foreground shadow-2xl transform hover:scale-110 active:scale-95 transition-all z-20">
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
