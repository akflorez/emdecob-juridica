import { useState, useEffect, useMemo } from "react";
import { 
  X, Calendar as CalendarIcon, User as UserIcon, CheckCircle2, 
  Clock, Tag, Paperclip, MessageSquare, Plus, ChevronRight, 
  Send, Trash2, ListChecks, Zap, Flag, AlertCircle, Edit3,
  UserCheck, Search, Activity, CornerDownRight, Smile, MoreHorizontal,
  ChevronDown, CalendarDays
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
      <SheetContent className="sm:max-w-[1200px] p-0 bg-[#252833] border-white/20 text-slate-100 flex flex-col">
        <SheetHeader className="sr-only">
          <SheetTitle>Detalle de Tarea</SheetTitle>
        </SheetHeader>
        
        <div className="flex flex-1 overflow-hidden h-full">
          <div className="flex-[2] flex flex-col border-r border-white/10 overflow-hidden bg-[#1e2128]">
             <ScrollArea className="flex-1">
                <div className="p-8 space-y-8">
                   <div className="flex items-center justify-between">
                      <Badge className="bg-primary/30 text-primary border-primary/50 font-black">
                        ID: {displayTask.clickup_id || displayTask.id}
                      </Badge>
                      <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="rounded-full hover:bg-white/20 h-10 w-10">
                        <X className="h-6 w-6" />
                      </Button>
                   </div>

                   <div className="space-y-6">
                      <div className="flex items-center gap-4 flex-wrap">
                        <Select value={statusOptions.includes(currentStatus) ? currentStatus : undefined} onValueChange={(v) => handleSave({ status: v })}>
                          <SelectTrigger className="w-auto min-w-[160px] h-10 px-4 rounded-xl border-2 font-black text-[10px] uppercase tracking-widest bg-white/5 border-white/20">
                            <SelectValue placeholder={currentStatus} />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-white/20 text-white">
                            {statusOptions.map(s => (
                              <SelectItem key={s} value={s} className="uppercase text-[10px] font-bold">{s}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        <Popover>
                          <PopoverTrigger asChild>
                            <div className="flex items-center gap-3 px-4 py-2 bg-white/10 rounded-xl border border-white/20 cursor-pointer hover:bg-white/20 transition-all font-bold text-xs">
                               <UserIcon className="h-4 w-4 text-primary" />
                               {displayTask.assignees?.map(a => a.nombre || a.username).join(', ') || displayTask.assignee_name || 'Sin Asignar'}
                            </div>
                          </PopoverTrigger>
                          <PopoverContent className="w-64 p-2 bg-slate-800 border-white/20 text-white rounded-2xl">
                             <ScrollArea className="h-[250px]">
                                <div className="space-y-1">
                                   {users.map(u => (
                                     <div key={u.id} className="flex items-center gap-3 p-2 hover:bg-white/5 rounded-xl cursor-pointer" onClick={() => (displayTask) && handleSave({ assignee_ids: [u.id] } as any)}>
                                        <Checkbox checked={displayTask.assignees?.some(a => a.id === u.id)} className="h-4 w-4 border-white/30" />
                                        <span className="text-sm font-medium">{(u.nombre || u.username)}</span>
                                     </div>
                                   ))}
                                </div>
                             </ScrollArea>
                          </PopoverContent>
                        </Popover>
                        
                        <div className="flex flex-wrap gap-2">
                           {displayTask.tags?.map(tag => (
                             <Badge key={tag.id} style={{ backgroundColor: tag.color || '#3b82f6', color: 'white' }} className="text-[9px] py-1 px-3 border-none font-black uppercase">
                               {tag.name}
                             </Badge>
                           ))}
                        </div>
                      </div>

                      <input 
                        className="w-full bg-transparent text-4xl font-black tracking-tighter border-none focus:ring-0 p-0 text-white placeholder:text-slate-700"
                        value={editedTitle}
                        onChange={(e) => setEditedTitle(e.target.value)}
                        onBlur={() => handleSave({ title: editedTitle })}
                      />
                   </div>

                   <div className="grid grid-cols-1 md:grid-cols-2 gap-8 bg-white/5 p-8 rounded-[2rem] border border-white/10">
                      <div className="space-y-4 text-xs">
                         <div className="text-[10px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-2">Información</div>
                         <div className="space-y-2">
                            <div className="flex justify-between border-b border-white/5 py-2">
                               <span className="text-slate-500">Obligación</span>
                               <span className="font-mono text-white">{displayTask.custom_fields || '-'}</span>
                            </div>
                         </div>
                      </div>
                      <div className="space-y-4">
                         <div className="text-[10px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-2">Vínculo</div>
                         <div className="p-4 bg-black/40 rounded-2xl border border-white/10 text-primary font-black text-sm truncate">
                            {displayTask.case_radicado || 'Radicado Vinculado'}
                         </div>
                      </div>
                   </div>

                   <div className="space-y-4">
                      <div className="text-[10px] font-black uppercase tracking-widest text-slate-500">Notas</div>
                      <Textarea 
                        className="min-h-[180px] bg-white/5 border-2 border-white/10 rounded-2xl p-6 text-sm text-slate-100"
                        value={editedDesc}
                        onChange={(e) => setEditedDesc(e.target.value)}
                        onBlur={() => handleSave({ description: editedDesc })}
                      />
                   </div>

                   <div className="space-y-6">
                      <div className="flex items-center justify-between">
                         <div className="text-[10px] font-black uppercase tracking-widest text-slate-500">Pasos de Gestión</div>
                         <Button size="sm" onClick={() => setShowSubtaskForm(true)} className="rounded-xl h-8 text-[10px] font-black">NUEVA SUBTAREA</Button>
                      </div>
                      <div className="space-y-3">
                         {showSubtaskForm && (
                           <div className="p-6 bg-primary/10 border border-primary/30 rounded-2xl space-y-4">
                              <Input placeholder="Título..." value={newSubtaskTitle} onChange={(e) => setNewSubtaskTitle(e.target.value)} className="bg-black/20" />
                              <div className="flex justify-end gap-2">
                                 <Button variant="ghost" size="sm" onClick={() => setShowSubtaskForm(false)}>Cancelar</Button>
                                 <Button size="sm" onClick={handleCreateSubtask}>Crear</Button>
                              </div>
                           </div>
                         )}
                         {displayTask.checklists?.map(item => (
                           <div key={item.id} className="flex items-center gap-4 p-4 bg-white/5 border border-white/10 rounded-xl">
                              <Checkbox checked={item.is_completed} onCheckedChange={(v) => updateChecklistItem(item.id, { is_completed: !!v }).then(refreshTask)} />
                              <span className={`text-sm flex-1 ${item.is_completed ? 'line-through text-slate-500' : 'text-slate-200'}`}>{item.content}</span>
                           </div>
                         ))}
                      </div>
                   </div>
                </div>
             </ScrollArea>
          </div>

          <div className="flex-1 flex flex-col bg-[#1a1c23]">
             <div className="h-16 flex items-center px-6 border-b border-white/10 font-black text-[10px] uppercase tracking-widest gap-4 text-slate-500">
                <span className="text-primary border-b-2 border-primary h-full flex items-center">Actividad</span>
             </div>
             <ScrollArea className="flex-1 p-6">
                <div className="space-y-6">
                   {displayTask.comments?.map(comment => (
                     <div key={comment.id} className="flex gap-3">
                        <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-xs font-black">{comment.user_name?.[0] || 'U'}</div>
                        <div className="flex-1 space-y-1">
                           <div className="flex justify-between text-[10px] font-bold">
                              <span className="text-slate-300">{comment.user_name}</span>
                              <span className="text-slate-600">{isValid(new Date(comment.created_at)) ? format(new Date(comment.created_at), "d MMM", { locale: es }) : ''}</span>
                           </div>
                           <div className="p-4 bg-white/5 border border-white/10 rounded-2xl rounded-tl-none text-xs text-slate-300 leading-relaxed">
                              {comment.content}
                           </div>
                        </div>
                     </div>
                   ))}
                </div>
             </ScrollArea>
             <div className="p-6 border-t border-white/10">
                <div className="relative">
                   <Textarea 
                     value={newComment}
                     onChange={(e) => setNewComment(e.target.value)}
                     placeholder="Mensaje..."
                     className="bg-black/30 border-white/10 rounded-2xl pr-12 min-h-[100px] text-sm"
                   />
                   <Button size="icon" onClick={handleAddComment} className="absolute bottom-3 right-3 h-8 w-8 rounded-xl bg-primary">
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
