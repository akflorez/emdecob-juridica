import { useState, useEffect, useMemo } from "react";
import { 
  X, Calendar as CalendarIcon, User as UserIcon, CheckCircle2, 
  Clock, Tag, Paperclip, MessageSquare, Plus, ChevronRight, 
  Send, Trash2, ListChecks, Zap, Flag, AlertCircle, Edit3,
  UserCheck, Search, Activity, CornerDownRight, Smile, MoreHorizontal,
  ChevronDown, CalendarDays, Layout, Check
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
import { cn } from "@/lib/utils";

interface TaskDrawerProps {
  task: TaskType | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskUpdate: (updatedTask: TaskType) => void;
  clickupToken?: string;
  allAssignees?: string[];
  allStatuses?: string[];
}

export function TaskDrawer({ task, open, onOpenChange, onTaskUpdate, clickupToken, allStatuses = [] }: TaskDrawerProps) {
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
      // Prioridad: Traer todos los usuarios que tengan 'nombre' (Abogados)
      getUsers().then(res => {
        setUsers(res.filter(u => u.nombre && u.nombre.trim() !== ''));
      }).catch(console.error);
      
      // Asegurar que las etiquetas se carguen de múltiples fuentes
      getTags().then(res => {
        if (res && res.length > 0) {
          setAllTags(res);
        } else if (task.tags) {
          setAllTags(task.tags);
        }
      }).catch(() => {
        if (task.tags) setAllTags(task.tags);
      });
    }
  }, [task, open]);

  const refreshTask = async () => {
    if (!task) return;
    setIsLoading(true);
    try {
      const detail = await getTaskDetail(task.id, clickupToken);
      if (detail) {
        setFullTask(detail);
        if (detail.tags && detail.tags.length > 0) {
           setAllTags(prev => {
             const existingNames = new Set(prev.map(t => t.name));
             const newOnes = detail.tags!.filter(t => !existingNames.has(t.name));
             return [...prev, ...newOnes];
           });
        }
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
    let newIds = currentIds.includes(userId) 
      ? currentIds.filter(id => id !== userId) 
      : [...currentIds, userId];
    handleSave({ assignee_ids: newIds } as any);
  };

  const toggleTag = (tagName: string) => {
    if (!displayTask) return;
    const currentTags = displayTask.tags?.map(t => t.name) || [];
    let newTags = currentTags.includes(tagName) 
      ? currentTags.filter(t => t !== tagName) 
      : [...currentTags, tagName];
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
      setNewSubtaskDate("");
      setShowSubtaskForm(false);
      refreshTask();
      toast({ title: "Géstion creada" });
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

  if (!displayTask) return null;

  const statusOptions = Array.from(new Set([
    'ABIERTO', 'TO DO', 'IN PROGRESS', 'PENDIENTE', 'ALMP', '468', 'COMPLETO', 'CLOSED',
    ...(allStatuses || [])
  ])).filter(Boolean);

  const currentStatus = (displayTask.status || 'ABIERTO').toUpperCase();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[1100px] p-0 bg-[#16181d] border-white/10 text-slate-100 flex flex-col shadow-[0_0_50px_rgba(0,0,0,0.5)]">
        <SheetHeader className="sr-only">
          <SheetTitle>Gestión Judicial Experta</SheetTitle>
        </SheetHeader>
        
        <div className="flex flex-1 overflow-hidden h-full">
          {/* MAIN CONTENT */}
          <div className="flex-[1.8] flex flex-col border-r border-white/5 overflow-hidden bg-[#0f1115]">
             <ScrollArea className="flex-1">
                <div className="p-10 space-y-12">
                   {/* TOP BAR */}
                   <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                         <Badge className="bg-primary/20 text-primary border-primary/30 font-black px-4 py-1.5 uppercase tracking-[0.2em] text-[10px] rounded-lg">
                           ID: {displayTask.clickup_id || displayTask.id}
                         </Badge>
                         <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" title="Sincronizado" />
                      </div>
                      <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="rounded-full hover:bg-white/5 text-slate-500 hover:text-white transition-colors">
                        <X className="h-6 w-6" />
                      </Button>
                   </div>

                   {/* SELECTORS ROW */}
                   <div className="space-y-8">
                      <div className="flex items-center gap-3 flex-wrap">
                        {/* STATUS SELECT */}
                        <Select value={statusOptions.includes(currentStatus) ? currentStatus : undefined} onValueChange={(v) => handleSave({ status: v })}>
                          <SelectTrigger className="w-auto min-w-[140px] h-9 px-4 rounded-xl border-none font-black text-[10px] uppercase tracking-widest bg-white/5 hover:bg-white/10 transition-all text-primary">
                            <SelectValue placeholder={currentStatus} />
                          </SelectTrigger>
                          <SelectContent className="bg-[#1c1f26] border-white/10 text-white">
                            {statusOptions.map(s => (
                              <SelectItem key={s} value={s} className="uppercase text-[10px] font-black tracking-widest py-2.5 focus:bg-primary/20 focus:text-primary">{s}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        {/* ABOGADOS MULTI-SELECT */}
                        <Popover>
                          <PopoverTrigger asChild>
                            <button className="flex items-center gap-3 px-4 py-2 bg-white/5 rounded-xl hover:bg-white/10 transition-all text-[11px] font-bold uppercase tracking-tight text-slate-300 border border-white/5">
                               <UserIcon className="h-4 w-4 text-primary" />
                               <span className="max-w-[240px] truncate">
                                 {displayTask.assignees && displayTask.assignees.length > 0 
                                   ? displayTask.assignees.map(a => a.nombre).join(', ') 
                                   : displayTask.assignee_name || 'Asignar Abogados'}
                               </span>
                               <ChevronDown className="h-4 w-4 opacity-50" />
                            </button>
                          </PopoverTrigger>
                          <PopoverContent className="w-72 p-2 bg-[#1c1f26] border-white/10 text-white rounded-2xl shadow-2xl">
                             <div className="px-3 py-2 text-[10px] font-black uppercase text-slate-500 tracking-[0.2em] border-b border-white/5 mb-1">Cuerpo de Abogados</div>
                             <ScrollArea className="h-[300px]">
                                {users.map(u => (
                                  <div key={u.id} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl cursor-pointer transition-all group" onClick={() => toggleAssignee(u.id)}>
                                     <div className="flex items-center gap-3">
                                        <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-black text-xs">{u.nombre?.[0]}</div>
                                        <span className="text-xs font-bold text-slate-200 group-hover:text-white">{u.nombre}</span>
                                     </div>
                                     {displayTask.assignees?.some(a => a.id === u.id) && <Check className="h-4 w-4 text-primary" />}
                                  </div>
                                ))}
                             </ScrollArea>
                          </PopoverContent>
                        </Popover>

                        {/* TAGS SELECT */}
                        <Popover>
                          <PopoverTrigger asChild>
                            <button className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-xl hover:bg-white/10 transition-all text-[10px] font-black uppercase tracking-widest text-slate-400 border border-white/5">
                               <Tag className="h-3.5 w-3.5" /> ETIQUETAS
                            </button>
                          </PopoverTrigger>
                          <PopoverContent className="w-64 p-2 bg-[#1c1f26] border-white/10 text-white rounded-2xl shadow-2xl">
                             <ScrollArea className="h-[250px]">
                                {allTags.map(t => (
                                  <div key={t.id} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl cursor-pointer" onClick={() => toggleTag(t.name)}>
                                     <div className="flex items-center gap-2">
                                        <div className="h-3 w-3 rounded-full" style={{ backgroundColor: t.color }} />
                                        <span className="text-xs font-bold">{t.name}</span>
                                     </div>
                                     {displayTask.tags?.some(gt => gt.name === t.name) && <Check className="h-4 w-4 text-primary" />}
                                  </div>
                                ))}
                                {allTags.length === 0 && <div className="p-6 text-center text-[10px] font-black text-slate-600 uppercase tracking-widest italic">Sincronizando etiquetas...</div>}
                             </ScrollArea>
                          </PopoverContent>
                        </Popover>
                      </div>

                      {/* RADICADO TITLE (MODERNIZED) */}
                      <div className="space-y-1">
                        <input 
                          className="w-full bg-transparent text-2xl font-black tracking-tight border-none focus:ring-0 p-0 text-white placeholder:text-slate-800"
                          value={editedTitle}
                          onChange={(e) => setEditedTitle(e.target.value)}
                          onBlur={() => handleSave({ title: editedTitle })}
                          placeholder="Sin título..."
                        />
                        <div className="flex items-center gap-2 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                           <Activity className="h-3 w-3" /> RADICADO DEL PROCESO
                        </div>
                      </div>
                   </div>

                   {/* TAGS CLOUD */}
                   <div className="flex flex-wrap gap-2">
                      {displayTask.tags?.map(tag => (
                        <Badge key={tag.id} style={{ backgroundColor: `${tag.color}33`, color: tag.color, borderColor: `${tag.color}55` }} className="text-[9px] py-1.5 px-3 font-black uppercase tracking-widest rounded-lg border flex items-center gap-2 group cursor-pointer hover:bg-white/5" onClick={() => toggleTag(tag.name)}>
                          {tag.name}
                          <X className="h-3 w-3 opacity-30 group-hover:opacity-100" />
                        </Badge>
                      ))}
                   </div>

                   {/* INFO CARDS (MINIMALIST) */}
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="p-8 bg-white/[0.02] border border-white/5 rounded-3xl space-y-6">
                         <div className="flex items-center gap-3 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">
                           <Layout className="h-4 w-4" /> CARPETA DIGITAL
                         </div>
                         <div className="space-y-4">
                            {(() => {
                               try {
                                 const fields = JSON.parse(displayTask.custom_fields || '[]');
                                 if (Array.isArray(fields) && fields.length > 0) {
                                   return fields.map((f: any, idx: number) => (
                                     <div key={idx} className="flex justify-between items-baseline group">
                                        <span className="text-[10px] text-slate-500 font-bold uppercase">{f.name}</span>
                                        <span className="text-[12px] text-slate-200 font-bold border-b border-transparent group-hover:border-primary/30 transition-all">{f.value || f.text_value || '-'}</span>
                                     </div>
                                   ));
                                 }
                               } catch (e) {}
                               return <div className="text-[10px] font-bold text-slate-600 uppercase italic">Sin datos adicionales</div>;
                            })()}
                         </div>
                      </div>
                      <div className="p-8 bg-white/[0.02] border border-white/5 rounded-3xl space-y-6 flex flex-col justify-between">
                         <div className="flex items-center gap-3 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">
                           <Zap className="h-4 w-4 text-yellow-500" /> EXPEDIENTE
                         </div>
                         <div className="space-y-4">
                            <div className="text-sm font-black text-primary font-mono tracking-wider">{displayTask.case_radicado || '11001400305420250052800'}</div>
                            <Button variant="link" className="p-0 h-auto text-[10px] font-black uppercase text-slate-400 hover:text-primary transition-colors flex items-center gap-2">
                               VER HISTORIAL COMPLETO <ChevronRight className="h-3 w-3" />
                            </Button>
                         </div>
                      </div>
                   </div>

                   {/* DESCRIPTION / NOTES */}
                   <div className="space-y-4">
                      <div className="flex items-center gap-2 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                        <Edit3 className="h-4 w-4" /> NOTAS TÉCNICAS
                      </div>
                      <div className="relative group">
                         <div className="absolute -inset-1 bg-gradient-to-r from-primary/10 to-transparent rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity blur-md" />
                         <Textarea 
                           className="min-h-[160px] bg-white/[0.03] border-white/10 rounded-2xl p-6 text-[14px] font-medium leading-relaxed text-slate-200 focus:border-primary/50 transition-all shadow-inner placeholder:text-slate-800"
                           value={editedDesc}
                           onChange={(e) => setEditedDesc(e.target.value)}
                           onBlur={() => handleSave({ description: editedDesc })}
                           placeholder="Ingresa los detalles de la gestión..."
                         />
                      </div>
                   </div>

                   {/* SUBTASKS SECTION */}
                   <div className="space-y-8">
                      <div className="flex items-center justify-between">
                         <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
                            <Activity className="h-4 w-4" /> CRONOGRAMA DE GESTIÓN
                         </div>
                         <Button size="sm" onClick={() => setShowSubtaskForm(true)} className="h-8 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20 font-black text-[9px] uppercase tracking-widest px-4">
                            + NUEVA GESTIÓN
                         </Button>
                      </div>
                      
                      <div className="space-y-4">
                         {showSubtaskForm && (
                           <div className="p-8 bg-primary/[0.02] border border-primary/10 rounded-2xl space-y-6">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                 <div className="space-y-2">
                                    <label className="text-[9px] font-black text-slate-500 uppercase ml-1">Título</label>
                                    <Input placeholder="Ej: Radicar memorial..." value={newSubtaskTitle} onChange={(e) => setNewSubtaskTitle(e.target.value)} className="bg-black/40 border-white/10 h-10 rounded-xl" />
                                 </div>
                                 <div className="space-y-2">
                                    <label className="text-[9px] font-black text-slate-500 uppercase ml-1">Fecha</label>
                                    <Input type="date" value={newSubtaskDate} onChange={(e) => setNewSubtaskDate(e.target.value)} className="bg-black/40 border-white/10 h-10 rounded-xl" />
                                 </div>
                              </div>
                              <div className="flex justify-end gap-3">
                                 <Button variant="ghost" size="sm" onClick={() => setShowSubtaskForm(false)} className="text-[10px] font-bold">Cancelar</Button>
                                 <Button size="sm" onClick={handleCreateSubtask} className="h-9 px-6 bg-primary font-black text-[10px] uppercase tracking-widest rounded-xl shadow-lg shadow-primary/20">CREAR</Button>
                              </div>
                           </div>
                         )}

                         {displayTask.checklists?.map(item => (
                           <div key={item.id} className="flex items-center gap-5 p-5 bg-white/[0.02] border border-white/5 rounded-2xl group hover:bg-white/[0.04] transition-all">
                              <Checkbox 
                                checked={item.is_completed} 
                                onCheckedChange={(v) => updateChecklistItem(item.id, { is_completed: !!v }).then(refreshTask)} 
                                className="h-5 w-5 border-white/20 data-[state=checked]:bg-green-500" 
                              />
                              <span className={cn("text-[13px] flex-1 font-bold tracking-tight transition-all", item.is_completed ? "line-through text-slate-600" : "text-slate-200")}>
                                {item.content}
                              </span>
                              <Button variant="ghost" size="icon" onClick={() => deleteChecklistItem(item.id).then(refreshTask)} className="h-8 w-8 text-slate-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all">
                                 <Trash2 className="h-4 w-4" />
                              </Button>
                           </div>
                         ))}

                         <div className="flex items-center gap-4 bg-white/[0.01] border border-dashed border-white/10 rounded-2xl p-2 pl-6 group">
                            <Plus className="h-4 w-4 text-slate-700 group-hover:text-primary transition-colors" />
                            <Input 
                              placeholder="Añadir paso rápido..." 
                              value={newChecklist} 
                              onChange={(e) => setNewChecklist(e.target.value)} 
                              onKeyDown={(e) => e.key === 'Enter' && handleAddChecklist()} 
                              className="bg-transparent border-none focus:ring-0 text-xs font-bold" 
                            />
                            <Button size="sm" onClick={handleAddChecklist} className="h-8 rounded-lg bg-white/5 hover:bg-white/10 text-[9px] font-black uppercase px-4">AÑADIR</Button>
                         </div>
                      </div>
                   </div>
                </div>
             </ScrollArea>
          </div>

          {/* ACTIVITY SIDEBAR (MODERNIZED) */}
          <div className="flex-1 flex flex-col bg-[#0b0d10] border-l border-white/5 shadow-2xl overflow-hidden">
             <div className="h-16 flex items-center px-8 border-b border-white/5 font-black text-[10px] uppercase tracking-[0.3em] gap-8 bg-white/[0.01]">
                <button 
                  onClick={() => setActiveRightTab('activity')}
                  className={cn("h-full flex items-center border-b-2 transition-all", activeRightTab === 'activity' ? "text-primary border-primary" : "text-slate-600 border-transparent")}
                >
                  HISTORIAL
                </button>
             </div>

             <ScrollArea className="flex-1 bg-gradient-to-b from-black/20 to-transparent">
                <div className="p-8 space-y-10">
                   {displayTask.comments?.map(comment => (
                     <div key={comment.id} className="flex gap-4">
                        <div className="h-9 w-9 flex-shrink-0 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-black uppercase text-[10px]">
                           {comment.user_name?.[0] || 'U'}
                        </div>
                        <div className="flex-1 space-y-2">
                           <div className="flex justify-between items-center text-[9px] font-black uppercase tracking-widest text-slate-500">
                              <span>{comment.user_name}</span>
                              <span className="opacity-50">{isValid(new Date(comment.created_at)) ? format(new Date(comment.created_at), "d MMM, h:mm", { locale: es }) : ''}</span>
                           </div>
                           <div className="p-5 bg-white/[0.03] border border-white/5 rounded-2xl rounded-tl-none text-[13px] font-medium text-slate-300 leading-relaxed">
                              {comment.content}
                           </div>
                        </div>
                     </div>
                   ))}
                </div>
             </ScrollArea>

             <div className="p-8 border-t border-white/5 bg-[#16181d]/80 backdrop-blur-md">
                <div className="relative">
                   <Textarea 
                     value={newComment}
                     onChange={(e) => setNewComment(e.target.value)}
                     placeholder="Actualización técnica..."
                     className="bg-black/40 border-white/10 rounded-2xl pr-14 min-h-[90px] text-[13px] font-bold p-5 focus:border-primary/40 transition-all placeholder:text-slate-800"
                   />
                   <Button size="icon" onClick={handleAddComment} disabled={!newComment.trim()} className="absolute bottom-4 right-4 h-9 w-9 rounded-xl bg-primary shadow-lg shadow-primary/20 hover:scale-105 active:scale-95 transition-all">
                     <Send className="h-4 w-4" />
                   </Button>
                </div>
             </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
