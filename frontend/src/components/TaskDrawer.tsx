import { useState, useEffect, useMemo, useCallback } from "react";
import { 
  X, Calendar as CalendarIcon, User as UserIcon, CheckCircle2, 
  Clock, Tag, Paperclip, MessageSquare, Plus, ChevronRight, 
  Send, Trash2, ListChecks, Zap, Flag, AlertCircle, Edit3,
  UserCheck, Search, Activity, CornerDownRight, Smile, MoreHorizontal,
  ChevronDown, Layout
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
  getUsers, getTags, getTaskDetail,
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
    if (s.includes('abierto') || s.includes('todo') || s.includes('almp')) return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    if (s.includes('proceso') || s.includes('curso') || s.includes('468')) return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    if (s.includes('presentar') || s.includes('inscripcion')) return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
    if (s.includes('retiro') || s.includes('not personal')) return 'bg-red-500/20 text-red-400 border-red-500/30';
    if (s.includes('completado') || s.includes('finalizado') || s.includes('cerrado')) return 'bg-green-500/20 text-green-400 border-green-500/30';
    return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[1200px] p-0 bg-[#0d0e12] border-white/5 text-slate-200 overflow-hidden flex flex-col">
        <div className="flex flex-1 overflow-hidden h-full">
          {/* LEFT PANE: DETAILS */}
          <div className="flex-[2] flex flex-col border-r border-white/5 overflow-hidden">
             <ScrollArea className="flex-1">
                <div className="p-10 space-y-10">
                   {/* HEADER: ID & CONTROLS */}
                   <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                         <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 font-mono text-[10px] uppercase tracking-widest px-3 py-1">
                           ID: {displayTask.clickup_id || displayTask.id}
                         </Badge>
                         <div className="flex items-center gap-2 text-[10px] text-muted-foreground bg-white/5 px-3 py-1 rounded-full border border-white/5">
                           <Activity className="h-3 w-3 text-primary" />
                           <span>Actividad en Vivo</span>
                         </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white"><Smile className="h-4 w-4"/></Button>
                        <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white"><MoreHorizontal className="h-4 w-4"/></Button>
                        <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="rounded-full hover:bg-white/10 ml-2">
                          <X className="h-5 w-5" />
                        </Button>
                      </div>
                   </div>

                   {/* TITLE & STATUS */}
                   <div className="space-y-6">
                      <div className="flex items-center gap-4 flex-wrap">
                        <Select value={displayTask.status || 'ABIERTO'} onValueChange={(v) => handleSave({ status: v })}>
                          <SelectTrigger className={`w-auto min-w-[120px] h-9 px-4 rounded-xl border font-black text-[10px] uppercase tracking-[0.1em] transition-all ${getStatusColor(displayTask.status)} hover:brightness-125`}>
                            <div className="flex items-center gap-2">
                               <div className={`h-2 w-2 rounded-full ${getStatusColor(displayTask.status).split(' ')[1].replace('text-', 'bg-')}`} />
                               <SelectValue />
                            </div>
                          </SelectTrigger>
                          <SelectContent className="bg-slate-900 border-white/10 text-white max-h-[300px]">
                            {(allStatuses.length > 0 ? allStatuses : ['ALMP', 'INSCRIPCION MEDIDAS', 'NOT PERSONAL', 'NOT AVISO', 'EMPLAZAMIENTO', '468', 'LIQUIDACION', 'AVALUO', 'REMATE', 'COMPLETO']).map(s => (
                              <SelectItem key={s} value={s} className="uppercase text-[10px] font-bold tracking-widest">{s}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        <Popover>
                          <PopoverTrigger asChild>
                            <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-xl border border-white/5 cursor-pointer hover:bg-white/10 transition-all">
                               <UserIcon className="h-3.5 w-3.5 text-primary" />
                               <div className="flex -space-x-1.5 overflow-hidden">
                                  {displayTask.assignees?.map((a, i) => (
                                    <Avatar key={i} className="h-5 w-5 border-2 border-[#0d0e12]">
                                      <AvatarFallback className="text-[8px] bg-primary/20 text-primary font-black">{(a.nombre || a.username)[0]}</AvatarFallback>
                                    </Avatar>
                                  ))}
                                  {(!displayTask.assignees || displayTask.assignees.length === 0) && <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Asignar</span>}
                               </div>
                            </div>
                          </PopoverTrigger>
                          <PopoverContent className="w-64 p-2 bg-slate-900 border-white/10 text-white rounded-2xl shadow-2xl">
                             <ScrollArea className="h-[250px]">
                                <div className="space-y-1">
                                   {users.map(u => (
                                     <div key={u.id} className="flex items-center gap-2 p-2 hover:bg-white/5 rounded-xl cursor-pointer transition-all" onClick={() => handleToggleAssignee(u.id)}>
                                        <Checkbox checked={displayTask.assignees?.some(a => a.id === u.id)} className="border-white/20 data-[state=checked]:bg-primary" />
                                        <Avatar className="h-6 w-6">
                                           <AvatarFallback className="text-[10px] font-black bg-primary/20 text-primary">{(u.nombre || u.username)[0]}</AvatarFallback>
                                        </Avatar>
                                        <span className="text-xs font-bold">{(u.nombre || u.username)}</span>
                                     </div>
                                   ))}
                                </div>
                             </ScrollArea>
                          </PopoverContent>
                        </Popover>

                        <Select value={displayTask.priority || 'normal'} onValueChange={(v) => handleSave({ priority: v })}>
                          <SelectTrigger className={`w-auto h-9 px-4 rounded-xl bg-white/5 border border-white/10 font-black text-[10px] uppercase tracking-[0.1em] transition-all ${displayTask.priority === 'urgent' ? 'text-red-500' : 'text-slate-400'}`}>
                            <div className="flex items-center gap-2">
                              <Flag className="h-3.5 w-3.5 fill-current" />
                              <SelectValue />
                            </div>
                          </SelectTrigger>
                          <SelectContent className="bg-slate-900 border-white/10 text-white">
                            <SelectItem value="urgent">Urgente</SelectItem>
                            <SelectItem value="high">Alta</SelectItem>
                            <SelectItem value="normal">Normal</SelectItem>
                            <SelectItem value="low">Baja</SelectItem>
                          </SelectContent>
                        </Select>

                        <div className="flex-1 min-w-[200px]">
                           <div className="flex flex-wrap gap-2 items-center">
                              {displayTask.tags?.map(tag => (
                                <Badge 
                                  key={tag.id}
                                  style={{ backgroundColor: tag.color || '#3b82f6', color: 'white' }}
                                  className="text-[9px] py-1 px-3 border-none shadow-lg font-black uppercase tracking-wider rounded-lg flex items-center gap-1.5 group cursor-pointer"
                                  onClick={() => handleTagToggle(tag.name)}
                                >
                                  {tag.name}
                                  <X className="h-2.5 w-2.5 opacity-50 group-hover:opacity-100" />
                                </Badge>
                              ))}
                              <Popover>
                                <PopoverTrigger asChild>
                                  <Button variant="ghost" size="sm" className="h-7 px-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                                    <Tag className="h-3 w-3 mr-2 text-primary" /> Etiquetas
                                  </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-56 p-2 bg-slate-900 border-white/10 text-white rounded-xl shadow-2xl">
                                   <ScrollArea className="h-[200px]">
                                      <div className="space-y-1">
                                         {allTags.map(t => (
                                           <div key={t.id} className="flex items-center gap-2 p-2 hover:bg-white/5 rounded-lg cursor-pointer text-xs font-bold" onClick={() => handleTagToggle(t.name)}>
                                              <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: t.color }} />
                                              <span className="flex-1">{t.name}</span>
                                              {displayTask.tags?.some(gt => gt.name === t.name) && <CheckCircle2 className="h-3 w-3 text-primary" />}
                                           </div>
                                         ))}
                                      </div>
                                   </ScrollArea>
                                </PopoverContent>
                              </Popover>
                           </div>
                        </div>
                      </div>

                      <input 
                        className="w-full bg-transparent text-4xl font-black tracking-tighter border-none focus:ring-0 p-0 text-white placeholder:text-slate-800"
                        value={editedTitle}
                        onChange={(e) => setEditedTitle(e.target.value)}
                        onBlur={() => handleSave({ title: editedTitle })}
                        placeholder="Radicado o Título..."
                      />
                   </div>

                   {/* CUSTOM FIELDS / CASE LINK */}
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-8 bg-white/[0.01] p-6 rounded-3xl border border-white/5">
                      <div className="space-y-4">
                         <div className="text-[10px] font-black uppercase text-slate-600 tracking-widest flex items-center gap-2">
                           <Layout className="h-3 w-3 text-primary" /> Campos Personalizados
                         </div>
                         <div className="space-y-3">
                            {(() => {
                               try {
                                 const fields = JSON.parse(displayTask.custom_fields || '[]');
                                 if (Array.isArray(fields) && fields.length > 0) {
                                   return fields.map((f: any, idx: number) => (
                                     <div key={idx} className="flex justify-between items-center py-2 border-b border-white/[0.03]">
                                        <span className="text-[10px] text-slate-500 font-bold uppercase">{f.name}</span>
                                        <span className="text-xs text-white font-mono">{f.value || f.text_value || '-'}</span>
                                     </div>
                                   ));
                                 }
                               } catch (e) {}
                               return (
                                 <>
                                   <div className="flex justify-between items-center py-2 border-b border-white/[0.03]">
                                      <span className="text-[10px] text-slate-500 font-bold uppercase">Obligación</span>
                                      <span className="text-xs text-white font-mono">{displayTask.custom_fields || '91183935'}</span>
                                   </div>
                                   <div className="flex justify-between items-center py-2 border-b border-white/[0.03]">
                                      <span className="text-[10px] text-slate-500 font-bold uppercase">Tipo Proceso</span>
                                      <span className="text-xs text-white">Ejecutivo Hipotecario</span>
                                   </div>
                                 </>
                               );
                            })()}
                         </div>
                      </div>
                      <div className="space-y-4">
                        <div className="text-[10px] font-black uppercase text-slate-600 tracking-widest flex items-center gap-2">
                           <Zap className="h-3 w-3 text-yellow-500" /> Proceso Judicial
                         </div>
                         <div className="p-3 bg-black/40 rounded-2xl border border-white/5 hover:border-primary/30 transition-all cursor-pointer">
                            <div className="text-[11px] font-black text-primary truncate mb-1">11001400305620240063200</div>
                            <div className="text-[9px] text-slate-500 uppercase tracking-widest font-bold">FNA vs CARLOS ENRIQUE ACEVEDO</div>
                         </div>
                      </div>
                   </div>

                   {/* DESCRIPTION */}
                   <div className="space-y-4">
                      <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-600">
                        <Edit3 className="h-3.5 w-3.5" /> Descripción de Gestión
                      </div>
                      <Textarea 
                        className="min-h-[150px] bg-white/[0.02] border-white/5 focus:border-primary/40 rounded-3xl p-6 text-sm leading-relaxed text-slate-300 resize-none transition-all placeholder:text-slate-800"
                        placeholder="Describe los detalles de la actuación jurídica..."
                        value={editedDesc}
                        onChange={(e) => setEditedDesc(e.target.value)}
                        onBlur={() => handleSave({ description: editedDesc })}
                      />
                   </div>

                   {/* SUBTASKS / CHECKLISTS */}
                   <div className="space-y-8">
                      <div className="space-y-4">
                         <div className="flex items-center justify-between">
                            <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-600 flex items-center gap-2">
                               <CornerDownRight className="h-4 w-4" /> Subtareas / Pasos
                            </div>
                            <Badge variant="outline" className="text-[9px]">{displayTask.checklists?.length || 0} items</Badge>
                         </div>
                         
                         <div className="space-y-3">
                            {displayTask.checklists?.map(item => (
                              <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} key={item.id} className="flex items-center gap-4 p-4 bg-white/[0.02] border border-white/5 rounded-2xl group hover:bg-white/[0.04] transition-all">
                                 <Checkbox 
                                   checked={item.is_completed} 
                                   onCheckedChange={(v) => updateChecklistItem(item.id, { is_completed: !!v }).then(refreshTask)} 
                                   className="border-white/20 data-[state=checked]:bg-green-500 data-[state=checked]:border-green-500"
                                 />
                                 <span className={`text-sm flex-1 ${item.is_completed ? 'line-through text-slate-600' : 'text-slate-300'}`}>{item.content}</span>
                                 <Button variant="ghost" size="icon" onClick={() => deleteChecklistItem(item.id).then(refreshTask)} className="h-8 w-8 text-slate-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <Trash2 className="h-4 w-4" />
                                 </Button>
                              </motion.div>
                            ))}
                            <div className="flex items-center gap-3 bg-white/[0.01] border border-dashed border-white/10 rounded-2xl p-2 pl-4">
                               <Input 
                                 placeholder="Añadir nuevo paso de gestión..." 
                                 value={newChecklist} 
                                 onChange={(e) => setNewChecklist(e.target.value)}
                                 onKeyDown={(e) => e.key === 'Enter' && handleAddChecklist()}
                                 className="bg-transparent border-none focus:ring-0 text-sm p-0 h-10"
                               />
                               <Button size="sm" onClick={handleAddChecklist} className="rounded-xl h-9 bg-primary/10 text-primary hover:bg-primary/20"><Plus className="h-4 w-4"/></Button>
                            </div>
                         </div>
                      </div>
                   </div>
                </div>
             </ScrollArea>
          </div>

          {/* RIGHT PANE: ACTIVITY / COMMENTS */}
          <div className="flex-1 flex flex-col bg-[#090a0d] overflow-hidden">
             <div className="h-16 flex items-center px-6 border-b border-white/5 gap-6">
                <button 
                  onClick={() => setActiveRightTab('activity')}
                  className={`text-[10px] font-black uppercase tracking-widest transition-colors ${activeRightTab === 'activity' ? 'text-primary border-b-2 border-primary h-full' : 'text-slate-500'}`}
                >
                  Actividad
                </button>
                <button 
                  onClick={() => setActiveRightTab('comments')}
                  className={`text-[10px] font-black uppercase tracking-widest transition-colors ${activeRightTab === 'comments' ? 'text-primary border-b-2 border-primary h-full' : 'text-slate-500'}`}
                >
                  Comentarios
                </button>
             </div>

             <ScrollArea className="flex-1">
                <div className="p-6 space-y-8">
                   {displayTask.comments?.map(comment => (
                     <div key={comment.id} className="flex gap-4">
                        <Avatar className="h-8 w-8 flex-shrink-0">
                           <AvatarFallback className="text-[10px] font-black bg-primary/10 text-primary">{(comment.user_name || 'U')[0]}</AvatarFallback>
                        </Avatar>
                        <div className="space-y-1 flex-1">
                           <div className="flex items-center justify-between">
                              <span className="text-xs font-black text-slate-300 uppercase tracking-tight">{comment.user_name}</span>
                              <span className="text-[10px] text-slate-600 font-bold">{format(new Date(comment.created_at), "d MMM, h:mm a", { locale: es })}</span>
                           </div>
                           <div className="p-4 bg-white/[0.03] border border-white/5 rounded-2xl rounded-tl-none text-sm text-slate-400 leading-relaxed shadow-sm">
                              {comment.content}
                           </div>
                        </div>
                     </div>
                   ))}

                   {(!displayTask.comments || displayTask.comments.length === 0) && (
                     <div className="h-[200px] flex flex-col items-center justify-center text-slate-700 opacity-20">
                        <MessageSquare className="h-12 w-12 mb-4" />
                        <p className="text-xs font-black uppercase tracking-widest">Sin comentarios aún</p>
                     </div>
                   )}
                </div>
             </ScrollArea>

             <div className="p-6 border-t border-white/5 bg-[#0d0e12]/50">
                <div className="relative">
                   <Textarea 
                     value={newComment}
                     onChange={(e) => setNewComment(e.target.value)}
                     placeholder="Escribe un mensaje o actualización..."
                     className="bg-white/[0.02] border-white/5 focus:border-primary/40 rounded-2xl pr-12 min-h-[100px] resize-none text-sm"
                   />
                   <Button 
                     size="icon" 
                     onClick={handleAddComment}
                     disabled={!newComment.trim()}
                     className="absolute bottom-3 right-3 h-8 w-8 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/20"
                   >
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
