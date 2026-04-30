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
      
      getUsers().then(res => {
        if (Array.isArray(res)) {
          setUsers(res.filter(u => u && u.nombre && u.nombre.trim() !== ''));
        }
      }).catch(console.error);
      
      getTags().then(res => {
        if (res && Array.isArray(res) && res.length > 0) {
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
    const currentIds = (displayTask.assignees || []).map(a => a.id);
    let newIds = currentIds.includes(userId) 
      ? currentIds.filter(id => id !== userId) 
      : [...currentIds, userId];
    handleSave({ assignee_ids: newIds } as any);
  };

  const toggleTag = (tagName: string) => {
    if (!displayTask) return;
    const currentTags = (displayTask.tags || []).map(t => t.name);
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
      toast({ title: "Creado" });
    } catch (error) {
      toast({ title: "Error", variant: "destructive" });
    }
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

  if (!displayTask) return null;

  const statusOptions = Array.from(new Set([
    'ABIERTO', 'TO DO', 'IN PROGRESS', 'PENDIENTE', 'ALMP', '468', 'COMPLETO', 'CLOSED',
    ...(allStatuses || [])
  ])).filter(Boolean);

  const currentStatus = (displayTask.status || 'ABIERTO').toUpperCase();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[1100px] p-0 bg-[#0f1115] border-white/10 text-slate-100 flex flex-col">
        <SheetHeader className="sr-only">
          <SheetTitle>Gestión Experta</SheetTitle>
        </SheetHeader>
        
        <div className="flex flex-1 overflow-hidden h-full">
          <div className="flex-[1.8] flex flex-col border-r border-white/5 overflow-hidden bg-[#0f1115]">
             <ScrollArea className="flex-1">
                <div className="p-8 space-y-10">
                   <div className="flex items-center justify-between">
                      <Badge className="bg-primary/20 text-primary border-primary/30 font-black px-4 py-1.5 uppercase tracking-widest text-[9px]">
                        ID: {displayTask.clickup_id || displayTask.id}
                      </Badge>
                      <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="rounded-full hover:bg-white/5 h-10 w-10">
                        <X className="h-6 w-6" />
                      </Button>
                   </div>

                   <div className="space-y-6">
                      <div className="flex items-center gap-3 flex-wrap">
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
                                   ? displayTask.assignees.map(a => a.nombre).join(', ') 
                                   : displayTask.assignee_name || 'Abogados'}
                               </span>
                            </button>
                          </PopoverTrigger>
                          <PopoverContent className="w-64 p-2 bg-[#1c1f26] border-white/10 text-white rounded-2xl shadow-2xl">
                             <ScrollArea className="h-[250px]">
                                {users.map(u => (
                                  <div key={u.id} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl cursor-pointer" onClick={() => toggleAssignee(u.id)}>
                                     <span className="text-xs font-bold text-slate-200">{(u.nombre || u.username)}</span>
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
                             <ScrollArea className="h-[200px]">
                                {allTags.map(t => (
                                  <div key={t.id} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl cursor-pointer" onClick={() => toggleTag(t.name)}>
                                     <span className="text-xs font-bold">{t.name}</span>
                                     {displayTask.tags?.some(gt => gt.name === t.name) && <CheckCircle2 className="h-4 w-4 text-primary" />}
                                  </div>
                                ))}
                             </ScrollArea>
                          </PopoverContent>
                        </Popover>
                      </div>

                      <div className="space-y-1">
                        <input 
                          className="w-full bg-transparent text-2xl font-black tracking-tight border-none focus:ring-0 p-0 text-white placeholder:text-slate-800"
                          value={editedTitle}
                          onChange={(e) => setEditedTitle(e.target.value)}
                          onBlur={() => handleSave({ title: editedTitle })}
                        />
                        <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Radicado Judicial</div>
                      </div>
                   </div>

                   <div className="flex flex-wrap gap-2">
                      {displayTask.tags?.map(tag => (
                        <Badge key={tag.id} style={{ backgroundColor: `${tag.color || '#3b82f6'}33`, color: tag.color || '#3b82f6', borderColor: `${tag.color || '#3b82f6'}55` }} className="text-[8px] py-1 px-3 font-black uppercase rounded-lg border">
                          {tag.name}
                        </Badge>
                      ))}
                   </div>

                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="p-6 bg-white/[0.02] border border-white/5 rounded-2xl space-y-4">
                         <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">Información</div>
                         <div className="space-y-3">
                            {(() => {
                               try {
                                 const fields = JSON.parse(displayTask.custom_fields || '[]');
                                 if (Array.isArray(fields)) {
                                   return fields.slice(0, 4).map((f: any, idx: number) => (
                                     <div key={idx} className="flex justify-between text-[11px] font-bold">
                                        <span className="text-slate-500 uppercase text-[9px]">{f.name}</span>
                                        <span className="text-slate-200">{f.value || f.text_value || '-'}</span>
                                     </div>
                                   ));
                                 }
                               } catch (e) {}
                               return null;
                            })()}
                         </div>
                      </div>
                      <div className="p-6 bg-white/[0.02] border border-white/5 rounded-2xl flex flex-col justify-between">
                         <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Expediente</div>
                         <div className="text-xs font-black text-primary truncate mt-2">{displayTask.case_radicado || '11001400305420250052800'}</div>
                      </div>
                   </div>

                   <div className="space-y-3">
                      <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Notas</div>
                      <Textarea 
                        className="min-h-[140px] bg-white/[0.02] border-white/10 rounded-xl p-4 text-sm text-slate-200 focus:border-primary/50"
                        value={editedDesc}
                        onChange={(e) => setEditedDesc(e.target.value)}
                        onBlur={() => handleSave({ description: editedDesc })}
                      />
                   </div>

                   <div className="space-y-6">
                      <div className="flex items-center justify-between">
                         <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Gestión</div>
                         <Button size="sm" onClick={() => setShowSubtaskForm(true)} className="h-7 text-[8px] font-black uppercase bg-primary/10 text-primary">+ Nueva</Button>
                      </div>
                      <div className="space-y-3">
                         {showSubtaskForm && (
                           <div className="p-6 bg-primary/5 border border-primary/20 rounded-xl space-y-4">
                              <Input placeholder="Título..." value={newSubtaskTitle} onChange={(e) => setNewSubtaskTitle(e.target.value)} className="bg-black/40 h-9" />
                              <div className="flex justify-end gap-2">
                                 <Button variant="ghost" size="sm" onClick={() => setShowSubtaskForm(false)}>Cancelar</Button>
                                 <Button size="sm" onClick={handleCreateSubtask}>Crear</Button>
                              </div>
                           </div>
                         )}
                         {displayTask.checklists?.map(item => (
                           <div key={item.id} className="flex items-center gap-4 p-4 bg-white/5 border border-white/10 rounded-xl">
                              <Checkbox checked={item.is_completed} onCheckedChange={(v) => updateChecklistItem(item.id, { is_completed: !!v }).then(refreshTask)} />
                              <span className={`text-xs font-bold ${item.is_completed ? 'line-through text-slate-600' : 'text-slate-200'}`}>{item.content}</span>
                           </div>
                         ))}
                      </div>
                   </div>
                </div>
             </ScrollArea>
          </div>

          <div className="flex-1 flex flex-col bg-[#0b0d10] overflow-hidden">
             <div className="h-16 flex items-center px-6 border-b border-white/5 font-black text-[9px] uppercase tracking-widest text-slate-600">Historial</div>
             <ScrollArea className="flex-1">
                <div className="p-6 space-y-8">
                   {displayTask.comments?.map(comment => (
                     <div key={comment.id} className="space-y-2">
                        <div className="flex justify-between text-[8px] font-black uppercase text-slate-500">
                           <span>{comment.user_name}</span>
                           <span>{isValid(new Date(comment.created_at)) ? format(new Date(comment.created_at), "d MMM", { locale: es }) : ''}</span>
                        </div>
                        <div className="p-4 bg-white/5 border border-white/10 rounded-xl rounded-tl-none text-xs text-slate-300">
                           {comment.content}
                        </div>
                     </div>
                   ))}
                </div>
             </ScrollArea>
             <div className="p-6 border-t border-white/5">
                <div className="relative">
                   <Textarea 
                     value={newComment}
                     onChange={(e) => setNewComment(e.target.value)}
                     placeholder="Mensaje..."
                     className="bg-black/40 border-white/10 rounded-xl pr-12 min-h-[80px] text-xs font-bold"
                   />
                   <Button size="icon" onClick={handleAddComment} disabled={!newComment.trim()} className="absolute bottom-3 right-3 h-8 w-8 rounded-lg bg-primary">
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
