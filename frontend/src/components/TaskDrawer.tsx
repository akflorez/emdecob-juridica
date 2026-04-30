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
    'ABIERTO', 'TO DO', 'IN PROGRESS', 'PENDIENTE', 'ALMP', '468', 'NOT PERSONAL', 'LIQUIDACION', 'REMATE', 'COMPLETO', 'CLOSED',
    ...(allSystemStatuses || []),
    ...(propStatuses || [])
  ])).filter(Boolean);

  const currentStatus = (displayTask.status || 'ABIERTO').toUpperCase();
  
  const completedChecklist = displayTask.checklists?.filter(c => c.is_completed).length || 0;
  const totalChecklist = displayTask.checklists?.length || 0;
  const checklistProgress = totalChecklist > 0 ? (completedChecklist / totalChecklist) * 100 : 0;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[1200px] p-0 bg-[#111111] border-none text-[#d1d1d1] flex flex-col shadow-2xl font-sans">
        <SheetHeader className="sr-only">
          <SheetTitle>ClickUp Interface Sync</SheetTitle>
        </SheetHeader>
        
        <div className="flex flex-1 overflow-hidden h-full">
          {/* LEFT COLUMN: TASK DETAILS */}
          <div className="flex-[2.2] flex flex-col overflow-hidden bg-[#111111]">
             <ScrollArea className="flex-1 px-10 pt-8 pb-20">
                <div className="space-y-10 max-w-[900px] mx-auto">
                   
                   {/* Top Breadcrumb & Actions */}
                   <div className="flex items-center justify-between text-[11px] text-gray-500 font-medium">
                      <div className="flex items-center gap-2">
                         <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[#1a1a1a] rounded hover:bg-[#252525] cursor-pointer transition-colors border border-transparent hover:border-white/10">
                            <Badge className="h-4 w-4 bg-[#2da44e] rounded-sm p-0 flex items-center justify-center text-[10px] text-white">
                               <Check className="h-3 w-3" />
                            </Badge>
                            <span className="text-gray-300">Tarea</span>
                            <ChevronDown className="h-3 w-3" />
                         </div>
                         <span className="opacity-30">/</span>
                         <span className="text-gray-400 font-bold">{displayTask.clickup_id || displayTask.id}</span>
                      </div>
                      <div className="flex items-center gap-4">
                         <RefreshCw className={cn("h-4 w-4 cursor-pointer hover:text-white transition-all", isLoading && "animate-spin")} onClick={refreshTask} />
                         <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="h-8 w-8 text-gray-500 hover:text-white">
                           <X className="h-5 w-5" />
                         </Button>
                      </div>
                   </div>

                   {/* Task Title (Radicado) */}
                   <div className="space-y-1">
                      <input 
                        className="w-full bg-transparent text-3xl font-bold tracking-tight border-none focus:ring-0 p-0 text-white placeholder:text-gray-800"
                        value={editedTitle}
                        onChange={(e) => setEditedTitle(e.target.value)}
                        onBlur={() => handleSave({ title: editedTitle })}
                      />
                   </div>

                   {/* Meta-info Grid (ClickUp Style) */}
                   <div className="grid grid-cols-2 lg:grid-cols-4 gap-y-6 gap-x-4 text-[13px]">
                      {/* Estado */}
                      <div className="flex items-center gap-4 group">
                         <div className="w-24 text-gray-500 flex items-center gap-2">
                            <Activity className="h-3.5 w-3.5" /> Estado
                         </div>
                         <Select value={statusOptions.includes(currentStatus) ? currentStatus : undefined} onValueChange={(v) => handleSave({ status: v })}>
                            <SelectTrigger className="h-7 w-auto min-w-[120px] bg-[#2da44e] hover:bg-[#34bc5a] text-white text-[11px] font-bold uppercase rounded-md border-none px-3 transition-colors flex items-center gap-1">
                               <SelectValue placeholder={currentStatus} />
                               <ChevronDown className="h-3 w-3" />
                            </SelectTrigger>
                            <SelectContent className="bg-[#1e1e1e] border-white/10 text-white">
                               {statusOptions.map(s => (
                                 <SelectItem key={s} value={s} className="uppercase text-[11px] font-bold py-2 tracking-widest">{s}</SelectItem>
                               ))}
                            </SelectContent>
                         </Select>
                      </div>

                      {/* Personas Asignadas */}
                      <div className="flex items-center gap-4 group">
                         <div className="w-24 text-gray-500 flex items-center gap-2">
                            <UserIcon className="h-3.5 w-3.5" /> Personas
                         </div>
                         <Popover>
                            <PopoverTrigger asChild>
                               <div className="flex items-center gap-1.5 cursor-pointer hover:bg-white/5 p-1 rounded pr-2 transition-colors">
                                  <div className="flex -space-x-1.5">
                                     {displayTask.assignees && displayTask.assignees.length > 0 ? (
                                        displayTask.assignees.map(a => (
                                          <div key={a.id} className="h-6 w-6 rounded-full bg-[#ff7b72] flex items-center justify-center text-[10px] font-black text-white ring-2 ring-[#111]">{(a.nombre || a.username)[0]}</div>
                                        ))
                                     ) : (
                                        <div className="h-6 w-6 rounded-full bg-gray-800 border-2 border-dashed border-gray-600 flex items-center justify-center"><UserIcon className="h-3 w-3 text-gray-500" /></div>
                                     )}
                                  </div>
                                  <span className="text-[11px] text-gray-300 font-medium truncate max-w-[100px]">
                                     {displayTask.assignees && displayTask.assignees.length > 0 
                                       ? displayTask.assignees.map(a => a.nombre || a.username).join(', ') 
                                       : 'Sin asignar'}
                                  </span>
                               </div>
                            </PopoverTrigger>
                            <PopoverContent className="w-64 p-2 bg-[#1e1e1e] border-white/10 text-white rounded-lg shadow-2xl">
                               <ScrollArea className="h-[250px]">
                                  {users.map(u => (
                                    <div key={u.id} className="flex items-center justify-between p-2 hover:bg-white/5 rounded cursor-pointer transition-colors" onClick={() => toggleAssignee(u.id)}>
                                       <div className="flex items-center gap-2">
                                          <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center text-[10px]">{u.nombre?.[0]}</div>
                                          <span className="text-xs">{u.nombre || u.username}</span>
                                       </div>
                                       {displayTask.assignees?.some(a => a.id === u.id) && <Check className="h-3 w-3 text-[#2da44e]" />}
                                    </div>
                                  ))}
                               </ScrollArea>
                            </PopoverContent>
                         </Popover>
                      </div>

                      {/* Fechas */}
                      <div className="flex items-center gap-4">
                         <div className="w-24 text-gray-500 flex items-center gap-2">
                            <CalendarIcon className="h-3.5 w-3.5" /> Fechas
                         </div>
                         <div className="flex items-center gap-2 bg-[#1a1a1a] p-1.5 rounded-md border border-white/5 hover:border-white/20 transition-all">
                            <input 
                              type="date" 
                              className="bg-transparent border-none focus:ring-0 text-[11px] font-bold text-gray-300 p-0 w-[100px]"
                              value={editedDueDate}
                              onChange={(e) => {
                                setEditedDueDate(e.target.value);
                                handleSave({ due_date: e.target.value } as any);
                              }}
                            />
                         </div>
                      </div>

                      {/* Etiquetas */}
                      <div className="flex items-center gap-4">
                         <div className="w-24 text-gray-500 flex items-center gap-2">
                            <Tag className="h-3.5 w-3.5" /> Etiquetas
                         </div>
                         <Popover>
                            <PopoverTrigger asChild>
                               <div className="flex flex-wrap gap-1.5 cursor-pointer">
                                  {displayTask.tags && displayTask.tags.length > 0 ? (
                                     displayTask.tags.map(t => (
                                       <Badge key={t.id} style={{ backgroundColor: t.color || '#3b82f6', color: '#fff' }} className="h-6 text-[10px] font-bold px-2.5 rounded-full border-none">
                                          {t.name}
                                       </Badge>
                                     ))
                                  ) : (
                                     <div className="text-gray-600 hover:text-gray-400 flex items-center gap-1 transition-colors"><Plus className="h-3 w-3" /> Añadir</div>
                                  )}
                               </div>
                            </PopoverTrigger>
                            <PopoverContent className="w-64 p-2 bg-[#1e1e1e] border-white/10 text-white rounded-lg">
                               <ScrollArea className="h-[200px]">
                                  {allTags.map(t => (
                                    <div key={t.id} className="flex items-center justify-between p-2 hover:bg-white/5 rounded cursor-pointer transition-colors" onClick={() => toggleTag(t.name)}>
                                       <div className="flex items-center gap-2">
                                          <div className="h-3 w-3 rounded-full" style={{ backgroundColor: t.color || '#3b82f6' }} />
                                          <span className="text-xs">{t.name}</span>
                                       </div>
                                       {displayTask.tags?.some(gt => gt.name === t.name) && <Check className="h-3 w-3 text-[#2da44e]" />}
                                    </div>
                                  ))}
                               </ScrollArea>
                            </PopoverContent>
                         </Popover>
                      </div>
                   </div>

                   {/* Description (Rich text feel) */}
                   <div className="space-y-4 pt-4 border-t border-white/5">
                      <div className="flex items-center gap-2 text-gray-500 group cursor-pointer hover:text-gray-300 transition-colors">
                         <MoreHorizontal className="h-4 w-4" />
                         <span className="text-xs font-medium italic opacity-50">Resumen inteligente de Brain...</span>
                      </div>
                      <Textarea 
                        className="min-h-[160px] bg-transparent border-none p-0 text-[14px] leading-relaxed text-gray-300 focus:ring-0 placeholder:text-gray-700 font-sans"
                        placeholder="Escribe una descripción o pulsa '/' para comandos..."
                        value={editedDesc}
                        onChange={(e) => setEditedDesc(e.target.value)}
                        onBlur={() => handleSave({ description: editedDesc })}
                      />
                   </div>

                   {/* Campos Section */}
                   <div className="space-y-4 pt-6 border-t border-white/5">
                      <div className="flex items-center justify-between group">
                         <div className="flex items-center gap-2 text-gray-400 font-bold text-[13px]">
                            <ChevronDown className="h-4 w-4" /> Campos
                         </div>
                         <div className="flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-all">
                            <Search className="h-3.5 w-3.5 text-gray-500" />
                            <Plus className="h-3.5 w-3.5 text-gray-500" />
                         </div>
                      </div>
                      <div className="space-y-0.5">
                         {(() => {
                            try {
                              const fields = JSON.parse(displayTask.custom_fields || '[]');
                              if (Array.isArray(fields) && fields.length > 0) {
                                return fields.map((f: any, idx: number) => (
                                  <div key={idx} className="grid grid-cols-[160px_1fr] group hover:bg-white/5 p-2 rounded transition-colors text-[13px]">
                                     <div className="flex items-center gap-3 text-gray-500">
                                        <Hash className="h-3.5 w-3.5 opacity-40" />
                                        <span className="truncate">{f.name}</span>
                                     </div>
                                     <div className="text-gray-200 font-medium px-4">{f.value || f.text_value || '-'}</div>
                                  </div>
                                ));
                              }
                            } catch (e) {}
                            return <div className="text-[12px] text-gray-600 italic px-8">Sin campos personalizados</div>;
                         })()}
                      </div>
                   </div>

                   {/* Subtareas Section */}
                   <div className="space-y-4 pt-6 border-t border-white/5">
                      <div className="flex items-center justify-between">
                         <div className="flex items-center gap-3">
                            <div className="flex items-center gap-2 text-gray-400 font-bold text-[13px]">
                               <ChevronDown className="h-4 w-4" /> Subtareas
                            </div>
                            <span className="text-[11px] text-gray-600 font-medium">0 completada —</span>
                            <div className="w-20 h-1 bg-gray-800 rounded-full overflow-hidden">
                               <div className="h-full bg-[#2da44e]" style={{ width: '0%' }} />
                            </div>
                         </div>
                         <div className="flex items-center gap-4 text-gray-500">
                            <div className="flex items-center gap-1 text-[11px] hover:text-white cursor-pointer"><Settings className="h-3.5 w-3.5" /> Ordenar</div>
                            <div className="flex items-center gap-1 text-[11px] hover:text-white cursor-pointer"><Zap className="h-3.5 w-3.5 text-purple-400" /> Sugerir</div>
                            <Plus className="h-4 w-4 hover:text-white cursor-pointer" onClick={() => setShowSubtaskForm(true)} />
                         </div>
                      </div>

                      <div className="w-full">
                         {/* Subtasks Header */}
                         <div className="grid grid-cols-[1fr_100px_80px_100px] gap-4 px-4 py-2 border-b border-white/5 text-[10px] font-black uppercase text-gray-600 tracking-wider">
                            <div>Nombre</div>
                            <div className="text-center">Persona asig.</div>
                            <div className="text-center">Prioridad</div>
                            <div className="text-right">Fecha límite</div>
                         </div>
                         
                         {/* Subtasks List */}
                         <div className="space-y-1 mt-2">
                            {displayTask.subtasks?.map(st => (
                              <div key={st.id} className="grid grid-cols-[1fr_100px_80px_100px] gap-4 px-4 py-2.5 hover:bg-white/5 transition-all rounded cursor-pointer group text-[13px]">
                                 <div className="flex items-center gap-3 text-gray-300">
                                    <CheckCircle2 className="h-4 w-4 text-[#2da44e]" />
                                    <span className="truncate">{st.title}</span>
                                 </div>
                                 <div className="flex justify-center">
                                    <div className="h-6 w-6 rounded-full bg-gray-800 flex items-center justify-center text-[10px] text-gray-500 font-bold border border-gray-700">JS</div>
                                 </div>
                                 <div className="flex justify-center">
                                    <Flag className="h-4 w-4 text-gray-600 group-hover:text-gray-400" />
                                 </div>
                                 <div className="text-right text-[11px] font-bold text-[#2da44e]">
                                    {st.due_date ? format(new Date(st.due_date), 'd/M/yy') : '-'}
                                 </div>
                              </div>
                            ))}
                            <div className="px-4 py-3 text-gray-600 hover:text-gray-400 text-[13px] flex items-center gap-3 cursor-pointer group" onClick={() => setShowSubtaskForm(true)}>
                               <Plus className="h-4 w-4 group-hover:scale-110 transition-transform" />
                               <span>Add Tarea</span>
                            </div>
                         </div>
                      </div>
                   </div>

                   {/* Listas de control (Checklists) */}
                   <div className="space-y-4 pt-6 border-t border-white/5">
                      <div className="flex items-center justify-between">
                         <div className="flex items-center gap-3">
                            <div className="flex items-center gap-2 text-gray-400 font-bold text-[13px]">
                               <ChevronDown className="h-4 w-4" /> Listas de control
                            </div>
                            <span className="text-[11px] text-gray-600 font-medium">{completedChecklist} abierta —</span>
                            <div className="w-24 h-1 bg-gray-800 rounded-full overflow-hidden">
                               <div className="h-full bg-[#3b82f6] transition-all duration-500" style={{ width: `${checklistProgress}%` }} />
                            </div>
                         </div>
                         <div className="flex items-center gap-4 text-gray-500">
                            <Layout className="h-4 w-4 hover:text-white cursor-pointer" />
                            <Plus className="h-4 w-4 hover:text-white cursor-pointer" />
                         </div>
                      </div>

                      <div className="px-6 space-y-1">
                         <div className="text-[11px] font-black text-gray-600 uppercase tracking-widest mb-3">Checklist</div>
                         {displayTask.checklists?.map(item => (
                           <div key={item.id} className="flex items-center gap-4 py-2 group hover:bg-white/[0.02] rounded px-2 transition-colors">
                              <Checkbox 
                                checked={item.is_completed} 
                                onCheckedChange={(v) => updateChecklistItem(item.id, { is_completed: !!v }).then(refreshTask)} 
                                className="h-4 w-4 border-gray-600 data-[state=checked]:bg-[#3b82f6] data-[state=checked]:border-[#3b82f6]" 
                              />
                              <span className={cn("text-[13px] flex-1 font-medium text-gray-300", item.is_completed && "line-through text-gray-600")}>
                                {item.content}
                              </span>
                              <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-all">
                                 <UserIcon className="h-3.5 w-3.5 text-gray-600 hover:text-gray-400 cursor-pointer" />
                                 <Trash2 className="h-3.5 w-3.5 text-gray-600 hover:text-red-400 cursor-pointer" onClick={() => deleteChecklistItem(item.id).then(refreshTask)} />
                              </div>
                           </div>
                         ))}
                         <div className="py-2 text-gray-600 hover:text-gray-400 text-[13px] flex items-center gap-3 cursor-pointer group px-2">
                            <Plus className="h-3.5 w-3.5" />
                            <span>Agregar elemento</span>
                         </div>
                      </div>
                   </div>

                   {/* Footer Actions */}
                   <div className="pt-10 border-t border-white/5 flex items-center gap-6">
                      <div className="flex items-center gap-2 text-gray-500 hover:text-gray-300 cursor-pointer transition-colors text-[13px] font-medium">
                         <AttachmentIcon className="h-4 w-4" /> Adjuntar archivo
                      </div>
                      <div className="flex items-center gap-2 text-gray-500 hover:text-gray-300 cursor-pointer transition-colors text-[13px] font-medium">
                         <Plus className="h-4 w-4" /> Relacionar elementos o agregar dependencias
                      </div>
                   </div>
                </div>
             </ScrollArea>
          </div>

          {/* RIGHT COLUMN: ACTIVITY */}
          <div className="flex-1 flex flex-col bg-[#111111] border-l border-white/5">
             {/* Activity Header */}
             <div className="h-14 flex items-center justify-between px-6 border-b border-white/5">
                <span className="text-[13px] font-bold text-gray-300">Activity</span>
                <div className="flex items-center gap-3 text-gray-500">
                   <Search className="h-4 w-4 hover:text-white cursor-pointer" />
                   <RefreshCw className="h-4 w-4 hover:text-white cursor-pointer" />
                   <Settings className="h-4 w-4 hover:text-white cursor-pointer" />
                </div>
             </div>

             <ScrollArea className="flex-1 px-6 py-6">
                <div className="space-y-6">
                   {displayTask.comments?.map(comment => (
                     <div key={comment.id} className="group relative">
                        <div className="flex items-center gap-2 text-[11px] mb-2">
                           <div className="h-5 w-5 rounded-full bg-gray-800 flex items-center justify-center text-[10px] font-black text-gray-400">
                              {comment.user_name?.[0]}
                           </div>
                           <span className="text-gray-300 font-bold">{comment.user_name}</span>
                           <span className="text-gray-500 text-[10px]">{isValid(new Date(comment.created_at)) ? format(new Date(comment.created_at), "d MMM 'a la(s)' p", { locale: es }) : ''}</span>
                        </div>
                        
                        <div className="p-4 bg-[#1e1e1e] border border-white/5 rounded-lg text-[13px] text-gray-300 leading-relaxed relative group-hover:border-white/10 transition-all">
                           {editingCommentId === comment.id ? (
                             <div className="space-y-2">
                                <Textarea value={editingCommentText} onChange={(e) => setEditingCommentText(e.target.value)} className="bg-black/40 text-xs border-none focus:ring-1 focus:ring-primary/40" />
                                <div className="flex justify-end gap-2">
                                   <Button size="sm" variant="ghost" onClick={() => setEditingCommentId(null)} className="h-6 text-[10px]">Cancelar</Button>
                                   <Button size="sm" onClick={() => handleUpdateComment(comment.id)} className="h-6 text-[10px] bg-primary">OK</Button>
                               </div>
                             </div>
                           ) : (
                             <>
                               {comment.content}
                               <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-all flex gap-1">
                                  <button onClick={() => { setEditingCommentId(comment.id); setEditingCommentText(comment.content); }} className="p-1 hover:text-white text-gray-500"><Edit3 className="h-3 w-3" /></button>
                                  <button onClick={() => handleDeleteComment(comment.id)} className="p-1 hover:text-red-500 text-gray-500"><Trash2 className="h-3 w-3" /></button>
                               </div>
                               <div className="mt-3 pt-3 border-t border-white/5 flex items-center gap-4 text-gray-500 text-[11px]">
                                  <div className="flex items-center gap-1 hover:text-white cursor-pointer"><Smile className="h-3.5 w-3.5" /></div>
                                  <div className="hover:text-white cursor-pointer font-medium">Respuesta</div>
                               </div>
                             </>
                           )}
                        </div>
                     </div>
                   ))}
                </div>
             </ScrollArea>

             {/* Comment Input Footer */}
             <div className="p-4 bg-[#111111] border-t border-white/5">
                <div className="bg-[#1e1e1e] border border-white/5 rounded-lg p-3 space-y-3 shadow-inner focus-within:border-white/20 transition-all">
                   <Textarea 
                     value={newComment}
                     onChange={(e) => setNewComment(e.target.value)}
                     placeholder="Escribe un comentario..."
                     className="bg-transparent border-none focus:ring-0 p-0 text-[13px] min-h-[40px] resize-none text-gray-300"
                   />
                   <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 text-gray-500">
                         <Plus className="h-4 w-4 hover:text-white cursor-pointer" />
                         <div className="flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-white/5 cursor-pointer text-[11px] font-bold">
                            <MessageCircle className="h-3.5 w-3.5" /> Comentario <ChevronDown className="h-3 w-3" />
                         </div>
                         <Zap className="h-4 w-4 text-purple-400 hover:text-purple-300 cursor-pointer" />
                         <AttachmentIcon className="h-4 w-4 hover:text-white cursor-pointer" />
                      </div>
                      <Button size="icon" onClick={handleAddComment} disabled={!newComment.trim()} className={cn("h-7 w-7 rounded bg-transparent text-gray-600 hover:bg-primary hover:text-white transition-all", newComment.trim() && "text-primary hover:bg-primary/20")}>
                        <Send className="h-4 w-4" />
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
