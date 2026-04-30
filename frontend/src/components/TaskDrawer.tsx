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
      
      // Fetching master data
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
      <SheetContent className="sm:max-w-[1200px] p-0 bg-[#111111] border-none text-[#d1d1d1] flex flex-col shadow-2xl font-sans">
        <SheetHeader className="sr-only"><SheetTitle>Consola Jurídica Sync</SheetTitle></SheetHeader>
        
        <div className="flex flex-1 overflow-hidden h-full">
          {/* LEFT: MAIN TASK */}
          <div className="flex-[2.2] flex flex-col overflow-hidden bg-[#111111]">
             <ScrollArea className="flex-1 px-10 pt-8 pb-20">
                <div className="space-y-8 max-w-[900px] mx-auto">
                   
                   {/* Breadcrumb Row */}
                   <div className="flex items-center justify-between text-[11px]">
                      <div className="flex items-center gap-2">
                         <div className="flex items-center gap-1.5 px-2 py-0.5 bg-[#1a1a1a] rounded hover:bg-[#252525] transition-colors cursor-pointer border border-white/5">
                            <div className="h-3.5 w-3.5 bg-[#2da44e] rounded-sm flex items-center justify-center"><Check className="h-2.5 w-2.5 text-white" /></div>
                            <span className="text-gray-400 font-bold uppercase tracking-widest text-[9px]">Tarea</span>
                            <ChevronDown className="h-3 w-3 text-gray-600" />
                         </div>
                         <span className="text-gray-700">/</span>
                         <span className="text-gray-400 font-bold tracking-wider">{displayTask.clickup_id || displayTask.id}</span>
                      </div>
                      <div className="flex items-center gap-3">
                         <Button variant="ghost" size="icon" onClick={refreshTask} disabled={isLoading} className="h-8 w-8 text-gray-500 hover:text-white">
                            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
                         </Button>
                         <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="h-8 w-8 text-gray-500 hover:text-white">
                           <X className="h-5 w-5" />
                         </Button>
                      </div>
                   </div>

                   {/* Title */}
                   <div className="space-y-0.5">
                      <input 
                        className="w-full bg-transparent text-3xl font-bold tracking-tight border-none focus:ring-0 p-0 text-white placeholder:text-gray-800"
                        value={editedTitle}
                        onChange={(e) => setEditedTitle(e.target.value)}
                        onBlur={() => handleSave({ title: editedTitle })}
                      />
                   </div>

                   {/* Metadata Bar */}
                   <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 text-[13px] py-4 border-b border-white/5">
                      {/* Status */}
                      <div className="flex items-center gap-3">
                         <div className="w-20 text-gray-600 font-medium flex items-center gap-2"><Activity className="h-3.5 w-3.5" /> Estado</div>
                         <Select value={statusOptions.includes(currentStatus) ? currentStatus : undefined} onValueChange={(v) => handleSave({ status: v })}>
                            <SelectTrigger className="h-7 w-auto min-w-[130px] bg-[#2da44e] hover:bg-[#34bc5a] text-white text-[10px] font-black uppercase rounded-md border-none px-3 transition-all flex items-center gap-2 shadow-lg">
                               <SelectValue placeholder={currentStatus} />
                               <ChevronDown className="h-3 w-3 opacity-70" />
                            </SelectTrigger>
                            <SelectContent className="bg-[#1e1e1e] border-white/10 text-white shadow-2xl">
                               {statusOptions.map(s => (
                                 <SelectItem key={s} value={s} className="uppercase text-[10px] font-black py-2.5 tracking-widest">{s}</SelectItem>
                               ))}
                            </SelectContent>
                         </Select>
                      </div>

                      {/* Assignees (Abogados) */}
                      <div className="flex items-center gap-3">
                         <div className="w-20 text-gray-600 font-medium flex items-center gap-2"><UserIcon className="h-3.5 w-3.5" /> Abogado</div>
                         <Popover>
                            <PopoverTrigger asChild>
                               <Button variant="ghost" className="h-8 p-0 flex items-center gap-2 hover:bg-transparent text-gray-300 font-bold group">
                                  <div className="flex -space-x-1.5">
                                     {displayTask.assignees?.map(a => (
                                       <div key={a.id} className="h-6 w-6 rounded-full bg-[#ff7b72] border-2 border-[#111] flex items-center justify-center text-[10px] font-black text-white">{a.nombre?.[0] || a.username[0]}</div>
                                     )) || <div className="h-6 w-6 rounded-full border-2 border-dashed border-gray-700 bg-gray-800" />}
                                  </div>
                                  <span className="text-[11px] truncate max-w-[100px] group-hover:text-primary transition-colors">
                                     {displayTask.assignees?.length ? displayTask.assignees.map(a => a.nombre || a.username).join(', ') : 'Asignar'}
                                  </span>
                               </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-72 p-2 bg-[#1e1e1e] border-white/10 text-white rounded-xl shadow-2xl">
                               <ScrollArea className="h-[300px]">
                                  {users.map(u => (
                                    <div key={u.id} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-lg cursor-pointer transition-all" onClick={() => toggleAssignee(u.id)}>
                                       <div className="flex flex-col">
                                          <span className="text-xs font-bold text-gray-200">{u.nombre || u.username}</span>
                                          <span className="text-[9px] text-gray-500 font-black uppercase">Personal Jurídico</span>
                                       </div>
                                       {displayTask.assignees?.some(a => a.id === u.id) && <Check className="h-4 w-4 text-[#2da44e]" />}
                                    </div>
                                  ))}
                               </ScrollArea>
                            </PopoverContent>
                         </Popover>
                      </div>

                      {/* Due Date */}
                      <div className="flex items-center gap-3">
                         <div className="w-20 text-gray-600 font-medium flex items-center gap-2"><CalendarIcon className="h-3.5 w-3.5" /> Límite</div>
                         <div className="flex items-center gap-2 bg-[#1a1a1a] px-3 py-1 rounded border border-white/5 hover:border-white/10 transition-all">
                            <input 
                              type="date" 
                              className="bg-transparent border-none focus:ring-0 text-[11px] font-black uppercase text-gray-300 p-0 w-[100px] cursor-pointer"
                              value={editedDueDate}
                              onChange={(e) => {
                                setEditedDueDate(e.target.value);
                                handleSave({ due_date: e.target.value } as any);
                              }}
                            />
                         </div>
                      </div>

                      {/* Tags */}
                      <div className="flex items-center gap-3">
                         <div className="w-20 text-gray-600 font-medium flex items-center gap-2"><Tag className="h-3.5 w-3.5" /> Etiquetas</div>
                         <Popover>
                            <PopoverTrigger asChild>
                               <div className="flex flex-wrap gap-1.5 cursor-pointer max-w-[150px]">
                                  {displayTask.tags?.map(t => (
                                    <Badge key={t.id} style={{ backgroundColor: t.color || '#3b82f6', color: '#fff' }} className="h-5 text-[9px] font-black px-2 rounded-md border-none shadow-sm">
                                       {t.name}
                                    </Badge>
                                  )) || <div className="text-gray-700 hover:text-gray-400 text-[11px] font-bold">+ Tag</div>}
                               </div>
                            </PopoverTrigger>
                            <PopoverContent className="w-64 p-2 bg-[#1e1e1e] border-white/10 text-white rounded-xl shadow-2xl">
                               <ScrollArea className="h-[200px]">
                                  {allTags.map(t => (
                                    <div key={t.id} className="flex items-center justify-between p-2.5 hover:bg-white/5 rounded-lg cursor-pointer" onClick={() => toggleTag(t.name)}>
                                       <div className="flex items-center gap-2">
                                          <div className="h-3 w-3 rounded-full" style={{ backgroundColor: t.color || '#3b82f6' }} />
                                          <span className="text-xs font-bold">{t.name}</span>
                                       </div>
                                       {displayTask.tags?.some(gt => gt.name === t.name) && <Check className="h-3 w-3 text-[#2da44e]" />}
                                    </div>
                                  ))}
                                  {allTags.length === 0 && <div className="p-4 text-[10px] text-gray-600 uppercase italic text-center">Cargando etiquetas...</div>}
                               </ScrollArea>
                            </PopoverContent>
                         </Popover>
                      </div>
                   </div>

                   {/* Description */}
                   <div className="space-y-4 pt-2">
                      <div className="flex items-center gap-2 text-gray-700 italic text-[11px]">
                         <Activity className="h-3.5 w-3.5 opacity-50" />
                         <span>Resumen detallado del proceso judicial...</span>
                      </div>
                      <Textarea 
                        className="min-h-[180px] bg-transparent border-none p-0 text-[14px] leading-relaxed text-gray-300 focus:ring-0 placeholder:text-gray-700"
                        placeholder="Ingresa los avances o memorandos aquí..."
                        value={editedDesc}
                        onChange={(e) => setEditedDesc(e.target.value)}
                        onBlur={() => handleSave({ description: editedDesc })}
                      />
                   </div>

                   {/* Subtasks (Table Style) */}
                   <div className="space-y-6 pt-8 border-t border-white/5">
                      <div className="flex items-center justify-between">
                         <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2 text-gray-400 font-bold text-[13px]">
                               <ChevronDown className="h-4 w-4" /> Subtareas
                            </div>
                            <div className="flex items-center gap-2 text-[11px] text-gray-600">
                               <span>{completedSubtasks} completada</span>
                               <Progress value={totalSubtasks > 0 ? (completedSubtasks / totalSubtasks) * 100 : 0} className="w-20 h-1 bg-gray-800" />
                            </div>
                         </div>
                         <div className="flex items-center gap-4 text-gray-500">
                            <Search className="h-4 w-4 hover:text-white cursor-pointer" />
                            <Plus className="h-4 w-4 hover:text-white cursor-pointer" onClick={() => setShowSubtaskForm(true)} />
                         </div>
                      </div>

                      <div className="w-full">
                         <div className="grid grid-cols-[1fr_120px_100px_100px] gap-4 px-4 py-2 border-b border-white/5 text-[10px] font-black uppercase text-gray-600 tracking-widest">
                            <div>Nombre</div>
                            <div className="text-center">Asignado</div>
                            <div className="text-center">Prioridad</div>
                            <div className="text-right">Vencimiento</div>
                         </div>
                         <div className="space-y-0.5 mt-2">
                            {displayTask.subtasks?.map(st => (
                              <div key={st.id} className="grid grid-cols-[1fr_120px_100px_100px] gap-4 px-4 py-2.5 hover:bg-white/5 rounded-lg transition-all cursor-pointer group text-[13px]">
                                 <div className="flex items-center gap-3 text-gray-200">
                                    <div className={`h-4 w-4 rounded-full border-2 border-gray-600 flex items-center justify-center ${st.status?.toLowerCase().includes('completado') && 'bg-[#2da44e] border-[#2da44e]'}`}>
                                       {st.status?.toLowerCase().includes('completado') && <Check className="h-2.5 w-2.5 text-white" />}
                                    </div>
                                    <span className={cn("truncate", st.status?.toLowerCase().includes('completado') && "line-through text-gray-600")}>{st.title}</span>
                                 </div>
                                 <div className="flex justify-center items-center">
                                    <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center text-[10px] font-black text-primary border border-primary/20">{st.assignee_name?.[0] || 'U'}</div>
                                 </div>
                                 <div className="flex justify-center items-center">
                                    <Flag className={`h-4 w-4 ${st.priority === 'high' ? 'text-red-500' : 'text-gray-700'}`} />
                                 </div>
                                 <div className="text-right text-[11px] font-bold text-[#2da44e] flex items-center justify-end">
                                    {st.due_date ? format(new Date(st.due_date), 'd MMM') : '-'}
                                 </div>
                              </div>
                            ))}
                            <div className="px-4 py-3 text-gray-600 hover:text-primary transition-all text-[13px] font-bold flex items-center gap-3 cursor-pointer group" onClick={() => setShowSubtaskForm(true)}>
                               <Plus className="h-4 w-4 group-hover:scale-110 transition-all" />
                               <span>Agregar Tarea</span>
                            </div>
                         </div>
                      </div>
                   </div>

                   {/* Custom Fields Section */}
                   <div className="space-y-4 pt-8 border-t border-white/5">
                      <div className="text-gray-400 font-bold text-[13px] flex items-center gap-2">
                         <ChevronDown className="h-4 w-4" /> Campos Técnicos
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-1">
                         {(() => {
                            try {
                              const fields = JSON.parse(displayTask.custom_fields || '[]');
                              if (Array.isArray(fields)) {
                                return fields.map((f: any, idx: number) => (
                                  <div key={idx} className="flex justify-between items-center py-2 px-3 hover:bg-white/5 rounded-lg group transition-all text-[12px]">
                                     <span className="text-gray-600 font-bold uppercase tracking-tight group-hover:text-gray-400">{f.name}</span>
                                     <span className="text-gray-200 font-black px-3 py-1 bg-white/5 rounded-md border border-white/10">{f.value || f.text_value || '-'}</span>
                                  </div>
                                ));
                              }
                            } catch (e) {}
                            return null;
                         })()}
                      </div>
                   </div>

                   {/* Checklists */}
                   <div className="space-y-6 pt-8 border-t border-white/5">
                      <div className="flex items-center justify-between">
                         <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2 text-gray-400 font-bold text-[13px]">
                               <ChevronDown className="h-4 w-4" /> Listas de control
                            </div>
                            <div className="flex items-center gap-2 text-[11px] text-gray-600">
                               <span>{completedChecklist}/{totalChecklist} abiertas</span>
                               <Progress value={checklistProgress} className="w-24 h-1 bg-gray-800" />
                            </div>
                         </div>
                      </div>
                      <div className="px-6 space-y-2">
                         {displayTask.checklists?.map(item => (
                           <div key={item.id} className="flex items-center gap-4 py-2 group hover:bg-white/[0.03] px-3 rounded-xl transition-all">
                              <Checkbox 
                                checked={item.is_completed} 
                                onCheckedChange={(v) => updateChecklistItem(item.id, { is_completed: !!v }).then(refreshTask)} 
                                className="h-5 w-5 border-gray-600 data-[state=checked]:bg-[#3b82f6] data-[state=checked]:border-[#3b82f6]" 
                              />
                              <span className={cn("text-[13px] flex-1 font-medium", item.is_completed ? "line-through text-gray-600" : "text-gray-200")}>
                                {item.content}
                              </span>
                              <div className="opacity-0 group-hover:opacity-100 transition-all">
                                 <Trash2 className="h-4 w-4 text-gray-700 hover:text-red-400 cursor-pointer" onClick={() => deleteChecklistItem(item.id).then(refreshTask)} />
                              </div>
                           </div>
                         ))}
                         <div className="flex items-center gap-4 py-3 px-3">
                            <Plus className="h-4 w-4 text-gray-700" />
                            <Input 
                               placeholder="Agregar elemento..." 
                               value={newChecklist} 
                               onChange={(e) => setNewChecklist(e.target.value)} 
                               onKeyDown={(e) => e.key === 'Enter' && handleAddChecklist()} 
                               className="bg-transparent border-none p-0 text-[13px] focus:ring-0 text-gray-300"
                            />
                         </div>
                      </div>
                   </div>
                </div>
             </ScrollArea>
          </div>

          {/* RIGHT: ACTIVITY */}
          <div className="flex-1 flex flex-col bg-[#111111] border-l border-white/5 shadow-2xl">
             <div className="h-14 flex items-center justify-between px-8 border-b border-white/5 bg-white/[0.02]">
                <span className="text-[13px] font-black uppercase tracking-[0.2em] text-gray-500">Activity</span>
                <div className="flex items-center gap-4 text-gray-600">
                   <Search className="h-4 w-4 hover:text-white cursor-pointer" />
                   <Settings className="h-4 w-4 hover:text-white cursor-pointer" />
                </div>
             </div>

             <ScrollArea className="flex-1 px-8 py-8">
                <div className="space-y-10">
                   {displayTask.comments?.map(comment => (
                     <div key={comment.id} className="group relative">
                        <div className="flex items-center gap-3 text-[11px] mb-3">
                           <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center text-[10px] font-black text-primary ring-2 ring-[#111]">
                              {comment.user_name?.[0] || 'U'}
                           </div>
                           <span className="text-gray-300 font-bold">{(comment.user_name || 'System')}</span>
                           <span className="text-gray-600 text-[10px] font-medium">{isValid(new Date(comment.created_at)) ? format(new Date(comment.created_at), "d MMM 'a la(s)' p", { locale: es }) : ''}</span>
                        </div>
                        
                        <div className="p-5 bg-white/[0.04] border border-white/5 rounded-2xl text-[13px] text-gray-300 leading-relaxed shadow-lg group-hover:bg-white/[0.06] transition-all">
                           {editingCommentId === comment.id ? (
                             <div className="space-y-3">
                                <Textarea value={editingCommentText} onChange={(e) => setEditingCommentText(e.target.value)} className="bg-black/60 border-primary/30 text-xs min-h-[80px]" />
                                <div className="flex justify-end gap-2">
                                   <Button size="sm" variant="ghost" onClick={() => setEditingCommentId(null)} className="h-7 text-[10px] font-bold">Cancelar</Button>
                                   <Button size="sm" onClick={() => handleUpdateComment(comment.id)} className="h-7 text-[10px] font-black bg-primary">GUARDAR</Button>
                               </div>
                             </div>
                           ) : (
                             <>
                               {comment.content}
                               <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-all flex gap-2">
                                  <button onClick={() => { setEditingCommentId(comment.id); setEditingCommentText(comment.content); }} className="h-7 w-7 rounded-lg bg-black/60 flex items-center justify-center hover:text-primary border border-white/5 transition-all"><Edit3 className="h-3.5 w-3.5" /></button>
                                  <button onClick={() => handleDeleteComment(comment.id)} className="h-7 w-7 rounded-lg bg-black/60 flex items-center justify-center hover:text-red-500 border border-white/5 transition-all"><Trash2 className="h-3.5 w-3.5" /></button>
                               </div>
                             </>
                           )}
                        </div>
                     </div>
                   ))}
                </div>
             </ScrollArea>

             <div className="p-6 bg-[#111111] border-t border-white/5">
                <div className="bg-[#1e1e1e] border border-white/10 rounded-2xl p-4 space-y-4 shadow-inner focus-within:border-primary/30 transition-all">
                   <Textarea 
                     value={newComment}
                     onChange={(e) => setNewComment(e.target.value)}
                     placeholder="Escribe un comentario técnico..."
                     className="bg-transparent border-none focus:ring-0 p-0 text-[13px] min-h-[60px] resize-none text-gray-300 font-medium"
                   />
                   <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 text-gray-600">
                         <AttachmentIcon className="h-4.5 w-4.5 hover:text-white cursor-pointer transition-colors" />
                         <Zap className="h-4.5 w-4.5 text-purple-400 hover:text-purple-300 cursor-pointer transition-colors" />
                         <Smile className="h-4.5 w-4.5 hover:text-white cursor-pointer transition-colors" />
                      </div>
                      <Button size="icon" onClick={handleAddComment} disabled={!newComment.trim()} className={cn("h-9 w-9 rounded-xl transition-all shadow-lg", newComment.trim() ? "bg-primary text-white" : "bg-gray-800 text-gray-500")}>
                        <Send className="h-4.5 w-4.5" />
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
