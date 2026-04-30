import { useState, useEffect, useMemo } from "react";
import { 
  X, Calendar as CalendarIcon, User as UserIcon, CheckCircle2, 
  Clock, Tag, Paperclip, MessageSquare, Plus, ChevronRight, 
  Send, Trash2, ListChecks, Zap, Flag, AlertCircle, Edit3,
  UserCheck, Search, Activity, CornerDownRight, Smile, MoreHorizontal,
  ChevronDown, CalendarDays, Layout, Check, Trash
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
      
      // Cargar datos maestros para selectores
      getUsers().then(res => setUsers(Array.isArray(res) ? res : [])).catch(console.error);
      getTags().then(res => setAllTags(Array.isArray(res) ? res : [])).catch(console.error);
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
    'ABIERTO', 'TO DO', 'IN PROGRESS', 'PENDIENTE', 'ALMP', '468', 'COMPLETO', 'CLOSED',
    ...(allSystemStatuses || []),
    ...(propStatuses || [])
  ])).filter(Boolean);

  const currentStatus = (displayTask.status || 'ABIERTO').toUpperCase();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[1100px] p-0 bg-[#0f1115] border-white/10 text-slate-100 flex flex-col shadow-2xl">
        <SheetHeader className="sr-only">
          <SheetTitle>Gestión Judicial</SheetTitle>
        </SheetHeader>
        
        <div className="flex flex-1 overflow-hidden h-full">
          <div className="flex-[1.8] flex flex-col border-r border-white/5 overflow-hidden bg-[#0f1115]">
             <ScrollArea className="flex-1">
                <div className="p-8 space-y-10">
                   {/* Top Info */}
                   <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                         <Badge className="bg-primary/20 text-primary border-primary/30 font-black px-4 py-1.5 uppercase text-[9px] rounded-lg">
                           ID: {displayTask.clickup_id || displayTask.id}
                         </Badge>
                         <div className="flex items-center gap-2 px-4 py-1 bg-white/5 rounded-lg border border-white/10">
                            <CalendarIcon className="h-3.5 w-3.5 text-primary" />
                            <input 
                              type="date" 
                              className="bg-transparent border-none focus:ring-0 text-[10px] font-black uppercase text-slate-300 p-0"
                              value={editedDueDate}
                              onChange={(e) => {
                                setEditedDueDate(e.target.value);
                                handleSave({ due_date: e.target.value } as any);
                              }}
                            />
                         </div>
                      </div>
                      <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="rounded-full hover:bg-white/5">
                        <X className="h-6 w-6" />
                      </Button>
                   </div>

                   {/* Main Actions */}
                   <div className="space-y-6">
                      <div className="flex items-center gap-4 flex-wrap">
                        <Select value={statusOptions.includes(currentStatus) ? currentStatus : undefined} onValueChange={(v) => handleSave({ status: v })}>
                          <SelectTrigger className="w-auto min-w-[140px] h-9 px-4 rounded-xl border-none font-black text-[9px] uppercase tracking-widest bg-white/5 text-primary">
                            <SelectValue placeholder={currentStatus} />
                          </SelectTrigger>
                          <SelectContent className="bg-[#1c1f26] border-white/10 text-white">
                            {statusOptions.map(s => (
                              <SelectItem key={s} value={s} className="uppercase text-[9px] font-black py-2.5">{s}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        <Popover>
                          <PopoverTrigger asChild>
                            <button className="flex items-center gap-3 px-4 py-2 bg-white/5 rounded-xl hover:bg-white/10 transition-all text-[10px] font-bold uppercase text-slate-300 border border-white/5">
                               <UserIcon className="h-4 w-4 text-primary" />
                               <span className="max-w-[200px] truncate">
                                 {displayTask.assignees && displayTask.assignees.length > 0 
                                   ? displayTask.assignees.map(a => a.nombre || a.username).join(', ') 
                                   : displayTask.assignee_name || 'Sin Asignar'}
                               </span>
                            </button>
                          </PopoverTrigger>
                          <PopoverContent className="w-72 p-2 bg-[#1c1f26] border-white/10 text-white rounded-2xl shadow-2xl">
                             <ScrollArea className="h-[300px]">
                                {users.map(u => (
                                  <div key={u.id} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl cursor-pointer" onClick={() => toggleAssignee(u.id)}>
                                     <div className="flex flex-col">
                                        <span className="text-xs font-bold text-slate-200">{u.nombre || u.username}</span>
                                        <span className="text-[9px] text-slate-500 font-black uppercase">Abogado</span>
                                     </div>
                                     {displayTask.assignees?.some(a => a.id === u.id) && <CheckCircle2 className="h-4 w-4 text-primary" />}
                                  </div>
                                ))}
                             </ScrollArea>
                          </PopoverContent>
                        </Popover>

                        <Popover>
                          <PopoverTrigger asChild>
                            <button className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-xl hover:bg-white/10 transition-all text-[9px] font-black uppercase text-slate-400 border border-white/5">
                               <Tag className="h-3 w-3" /> ETIQUETAS
                            </button>
                          </PopoverTrigger>
                          <PopoverContent className="w-64 p-2 bg-[#1c1f26] border-white/10 text-white rounded-2xl">
                             <ScrollArea className="h-[250px]">
                                {allTags.map(t => (
                                  <div key={t.id} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl cursor-pointer" onClick={() => toggleTag(t.name)}>
                                     <div className="flex items-center gap-2">
                                        <div className="h-3 w-3 rounded-full" style={{ backgroundColor: t.color }} />
                                        <span className="text-xs font-bold">{t.name}</span>
                                     </div>
                                     {displayTask.tags?.some(gt => gt.name === t.name) && <CheckCircle2 className="h-4 w-4 text-primary" />}
                                  </div>
                                ))}
                             </ScrollArea>
                          </PopoverContent>
                        </Popover>
                      </div>

                      <div className="space-y-1">
                        <input 
                          className="w-full bg-transparent text-2xl font-black tracking-tight border-none focus:ring-0 p-0 text-white"
                          value={editedTitle}
                          onChange={(e) => setEditedTitle(e.target.value)}
                          onBlur={() => handleSave({ title: editedTitle })}
                        />
                        <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
                           <Activity className="h-3 w-3" /> Radicado Judicial
                        </div>
                      </div>
                   </div>

                   {/* Details Grid */}
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="p-6 bg-white/[0.02] border border-white/5 rounded-2xl space-y-4">
                         <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">Campos Técnicos</div>
                         <div className="space-y-3">
                            {(() => {
                               try {
                                 const fields = JSON.parse(displayTask.custom_fields || '[]');
                                 if (Array.isArray(fields) && fields.length > 0) {
                                   return fields.map((f: any, idx: number) => (
                                     <div key={idx} className="flex justify-between text-[11px] font-bold py-1 border-b border-white/5">
                                        <span className="text-slate-500 uppercase text-[9px]">{f.name}</span>
                                        <span className="text-slate-200">{f.value || f.text_value || '-'}</span>
                                     </div>
                                   ));
                                 }
                               } catch (e) {}
                               return <div className="text-[10px] italic text-slate-600">Sin datos ClickUp</div>;
                            })()}
                         </div>
                      </div>
                      <div className="p-6 bg-white/[0.02] border border-white/5 rounded-2xl space-y-4">
                         <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Expediente Asociado</div>
                         <div className="p-4 bg-black/30 rounded-xl border border-white/10 text-xs font-black text-primary truncate">
                            {displayTask.case_radicado || 'Vincular Expediente'}
                         </div>
                         <Button variant="link" className="p-0 h-auto text-[9px] font-black uppercase text-slate-500">Ver Procesos Rama Judicial</Button>
                      </div>
                   </div>

                   {/* Description */}
                   <div className="space-y-3">
                      <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
                        <Edit3 className="h-4 w-4" /> Actualización Jurídica
                      </div>
                      <Textarea 
                        className="min-h-[160px] bg-white/[0.02] border-white/10 rounded-2xl p-6 text-sm text-slate-200 focus:border-primary/50"
                        placeholder="Ingresa los avances del proceso..."
                        value={editedDesc}
                        onChange={(e) => setEditedDesc(e.target.value)}
                        onBlur={() => handleSave({ description: editedDesc })}
                      />
                   </div>

                   {/* Subtasks */}
                   <div className="space-y-6">
                      <div className="flex items-center justify-between">
                         <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Listado de Gestión</div>
                         <Button size="sm" onClick={() => setShowSubtaskForm(true)} className="h-7 text-[8px] font-black uppercase bg-primary/10 text-primary">+ Nueva Gestión</Button>
                      </div>
                      <div className="space-y-3">
                         {showSubtaskForm && (
                           <div className="p-6 bg-primary/5 border border-primary/20 rounded-xl space-y-4 shadow-xl">
                              <div className="grid grid-cols-2 gap-4">
                                 <Input placeholder="Título..." value={newSubtaskTitle} onChange={(e) => setNewSubtaskTitle(e.target.value)} className="bg-black/40 h-9" />
                                 <Input type="date" value={newSubtaskDate} onChange={(e) => setNewSubtaskDate(e.target.value)} className="bg-black/40 h-9" />
                              </div>
                              <div className="flex justify-end gap-2">
                                 <Button variant="ghost" size="sm" onClick={() => setShowSubtaskForm(false)}>Cancelar</Button>
                                 <Button size="sm" onClick={handleCreateSubtask}>Guardar</Button>
                              </div>
                           </div>
                         )}
                         {displayTask.checklists?.map(item => (
                           <div key={item.id} className="flex items-center gap-4 p-4 bg-white/5 border border-white/10 rounded-xl group">
                              <Checkbox checked={item.is_completed} onCheckedChange={(v) => updateChecklistItem(item.id, { is_completed: !!v }).then(refreshTask)} />
                              <span className={`text-xs font-bold flex-1 ${item.is_completed ? 'line-through text-slate-600' : 'text-slate-200'}`}>{item.content}</span>
                              <Button variant="ghost" size="icon" onClick={() => deleteChecklistItem(item.id).then(refreshTask)} className="h-8 w-8 text-slate-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all">
                                 <Trash2 className="h-4 w-4" />
                              </Button>
                           </div>
                         ))}
                      </div>
                   </div>
                </div>
             </ScrollArea>
          </div>

          {/* Activity / Comments */}
          <div className="flex-1 flex flex-col bg-[#0b0d10] overflow-hidden">
             <div className="h-16 flex items-center px-8 border-b border-white/5 font-black text-[10px] uppercase tracking-widest text-slate-500">Historial de Mensajes</div>
             <ScrollArea className="flex-1">
                <div className="p-8 space-y-10">
                   {displayTask.comments?.map(comment => (
                     <div key={comment.id} className="group relative">
                        <div className="flex justify-between text-[8px] font-black uppercase text-slate-600 mb-2">
                           <div className="flex items-center gap-2">
                              <div className="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center text-primary">{comment.user_name?.[0]}</div>
                              <span>{comment.user_name}</span>
                           </div>
                           <span>{isValid(new Date(comment.created_at)) ? format(new Date(comment.created_at), "d MMM, h:mm a", { locale: es }) : ''}</span>
                        </div>
                        {editingCommentId === comment.id ? (
                           <div className="space-y-2">
                              <Textarea value={editingCommentText} onChange={(e) => setEditingCommentText(e.target.value)} className="bg-black/50 text-xs min-h-[60px]" />
                              <div className="flex justify-end gap-2">
                                 <Button size="sm" variant="ghost" onClick={() => setEditingCommentId(null)}>Can.</Button>
                                 <Button size="sm" onClick={() => handleUpdateComment(comment.id)}>OK</Button>
                              </div>
                           </div>
                        ) : (
                           <div className="p-5 bg-white/5 border border-white/10 rounded-2xl rounded-tl-none text-xs text-slate-300 leading-relaxed relative">
                              {comment.content}
                              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-all flex gap-1">
                                 <button onClick={() => { setEditingCommentId(comment.id); setEditingCommentText(comment.content); }} className="p-1 hover:text-primary"><Edit3 className="h-3 w-3" /></button>
                                 <button onClick={() => handleDeleteComment(comment.id)} className="p-1 hover:text-red-500"><Trash className="h-3 w-3" /></button>
                              </div>
                           </div>
                        )}
                     </div>
                   ))}
                </div>
             </ScrollArea>
             <div className="p-8 border-t border-white/5">
                <div className="relative">
                   <Textarea 
                     value={newComment}
                     onChange={(e) => setNewComment(e.target.value)}
                     placeholder="Escribe una actualización..."
                     className="bg-black/40 border-white/10 rounded-xl pr-14 min-h-[100px] text-xs font-bold p-5"
                   />
                   <Button size="icon" onClick={handleAddComment} disabled={!newComment.trim()} className="absolute bottom-4 right-4 h-9 w-9 rounded-xl bg-primary">
                     <Send className="h-5 w-5" />
                   </Button>
                </div>
             </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
