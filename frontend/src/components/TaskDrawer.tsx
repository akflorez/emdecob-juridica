import { useState, useEffect, useMemo, useCallback } from "react";
import { 
  X, Calendar as CalendarIcon, User as UserIcon, CheckCircle2, 
  Clock, Tag, Paperclip, MessageSquare, Plus, ChevronRight, 
  Send, Trash2, ListChecks, Zap, Flag, AlertCircle, Edit3,
  UserCheck, Search
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
  updateTask, getTaskComments, addTaskComment, 
  getTaskChecklists, addTaskChecklist, updateTaskChecklist, 
  deleteTaskChecklist, deleteTaskComment, getCaseByRadicado,
  getTags,
  type Task as TaskType, type User, type Tag as TagType
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

interface TaskDrawerProps {
  task: TaskType | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskUpdate: (updatedTask: TaskType) => void;
  clickupToken?: string;
  allAssignees?: string[];
  allStatuses?: string[];
}

type CaseRow = { id: number, radicado: string, demandante: string, demandado: string };

export function TaskDrawer({ task, open, onOpenChange, onTaskUpdate, clickupToken, allAssignees = [], allStatuses = [] }: TaskDrawerProps) {
  const { toast } = useToast();
  const [editedTitle, setEditedTitle] = useState('');
  const [editedDesc, setEditedDesc] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [fullTask, setFullTask] = useState<TaskType | null>(null);
  const [caseSearch, setCaseSearch] = useState('');
  const [caseResults, setCaseResults] = useState<CaseRow[]>([]);
  const [linkedCase, setLinkedCase] = useState<CaseRow | null>(null);
  const [newComment, setNewComment] = useState('');
  const [newChecklist, setNewChecklist] = useState("");
  const [allTags, setAllTags] = useState<TagType[]>([]);

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
    try {
      // En una app real, aquí cargaríamos el detalle completo
      // setFullTask(await getTaskDetail(task.id));
    } catch (error) {
      console.error("Error refreshing task", error);
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
    if (s.includes('abierto') || s.includes('todo')) return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    if (s.includes('proceso') || s.includes('curso')) return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    if (s.includes('presentar')) return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
    if (s.includes('retiro')) return 'bg-red-500/20 text-red-400 border-red-500/30';
    if (s.includes('completado') || s.includes('finalizado')) return 'bg-green-500/20 text-green-400 border-green-500/30';
    return 'bg-primary/20 text-primary border-primary/30';
  };

  const getPriorityColor = (p?: string) => {
    const pr = (p || '').toLowerCase();
    if (pr === 'urgent') return 'text-red-500';
    if (pr === 'high') return 'text-orange-500';
    if (pr === 'normal') return 'text-blue-500';
    return 'text-slate-400';
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[700px] p-0 bg-[#0d0e12] border-white/5 text-slate-200 overflow-hidden flex flex-col">
        <AnimatePresence>
          {open && (
            <motion.div 
              initial={{ x: 300, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 300, opacity: 0 }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="flex flex-col h-full"
            >
              <div className="flex-1 overflow-y-auto custom-scrollbar p-8 pt-12">
                
                {/* HEADER SECTION */}
                <div className="space-y-6 mb-10">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 font-mono text-[10px] uppercase tracking-widest px-3 py-1">
                        ID: {displayTask.clickup_id || displayTask.id}
                      </Badge>
                      <div className="flex items-center gap-2 text-[10px] text-muted-foreground bg-white/5 px-3 py-1 rounded-full border border-white/5">
                        <Zap className="h-3 w-3 text-yellow-500 animate-pulse" />
                        <span>Sincronización Activa</span>
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)} className="rounded-full hover:bg-white/10">
                      <X className="h-5 w-5" />
                    </Button>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                       <Select value={displayTask.status || 'ABIERTO'} onValueChange={(v) => handleSave({ status: v })}>
                         <SelectTrigger className={`w-auto h-8 px-4 rounded-full border font-black text-[10px] uppercase tracking-[0.1em] transition-all ${getStatusColor(displayTask.status)} hover:brightness-125`}>
                           <SelectValue />
                         </SelectTrigger>
                         <SelectContent className="bg-slate-900 border-white/10 text-white">
                           {(allStatuses.length > 0 ? allStatuses : ['ABIERTO', 'PENDIENTE', 'COMPLETADO']).map(s => (
                             <SelectItem key={s} value={s}>{s.toUpperCase()}</SelectItem>
                           ))}
                         </SelectContent>
                       </Select>

                       <Select value={displayTask.priority || 'normal'} onValueChange={(v) => handleSave({ priority: v })}>
                         <SelectTrigger className={`w-auto h-8 px-4 rounded-full bg-white/5 border border-white/10 font-black text-[10px] uppercase tracking-[0.1em] transition-all ${getPriorityColor(displayTask.priority)}`}>
                           <div className="flex items-center gap-2">
                             <Flag className="h-3 w-3 fill-current" />
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
                    </div>

                    <input 
                      className="w-full bg-transparent text-3xl font-black tracking-tight border-none focus:ring-0 p-0 text-white placeholder:text-slate-700"
                      value={editedTitle}
                      onChange={(e) => setEditedTitle(e.target.value)}
                      onBlur={() => handleSave({ title: editedTitle })}
                      placeholder="Sin título..."
                    />
                  </div>
                </div>

                {/* PROPERTIES GRID */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-8 bg-white/[0.02] p-8 rounded-3xl border border-white/5 mb-10 relative overflow-hidden group">
                   <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl -mr-16 -mt-16 group-hover:scale-150 transition-transform duration-1000" />
                   
                   <div className="space-y-8">
                      <div className="space-y-3">
                        <label className="text-[10px] uppercase font-black text-slate-500 flex items-center gap-2 tracking-[0.2em]"><UserIcon className="h-3.5 w-3.5 text-primary"/> Responsables</label>
                        
                        <Popover>
                          <PopoverTrigger asChild>
                            <div className="flex items-center gap-2 p-3 bg-black/40 border border-white/5 rounded-2xl cursor-pointer hover:bg-white/5 transition-all min-h-[44px]">
                               <div className="flex -space-x-2 overflow-hidden">
                                  {displayTask.assignees?.map((a, i) => (
                                    <div key={i} className="h-6 w-6 rounded-full ring-2 ring-[#1a1c23] bg-primary/20 flex items-center justify-center text-[8px] font-black text-primary border border-primary/20">
                                      {(a.nombre || a.username)[0]}
                                    </div>
                                  )) || (
                                    <div className="h-6 w-6 rounded-full bg-slate-800 flex items-center justify-center">
                                      <Plus className="h-3 w-3 text-slate-500" />
                                    </div>
                                  )}
                               </div>
                               <span className="text-xs font-bold text-slate-400">
                                 {displayTask.assignees?.length ? `${displayTask.assignees.length} asignados` : 'Sin asignar'}
                               </span>
                            </div>
                          </PopoverTrigger>
                          <PopoverContent className="w-64 p-2 bg-slate-900 border-white/10 text-white rounded-2xl shadow-2xl">
                             <div className="space-y-1">
                                {users.map(u => (
                                  <div key={u.id} className="flex items-center gap-2 p-2 hover:bg-white/5 rounded-xl cursor-pointer transition-all" onClick={() => handleToggleAssignee(u.id)}>
                                     <Checkbox checked={displayTask.assignees?.some(a => a.id === u.id)} className="border-white/20 data-[state=checked]:bg-primary" />
                                     <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center text-[10px] font-black text-primary">{(u.nombre || u.username)[0]}</div>
                                     <span className="text-xs font-bold">{(u.nombre || u.username)}</span>
                                  </div>
                                ))}
                             </div>
                          </PopoverContent>
                        </Popover>
                      </div>

                      <div className="space-y-3">
                        <label className="text-[10px] uppercase font-black text-slate-500 flex items-center gap-2 tracking-[0.2em]"><CalendarIcon className="h-3.5 w-3.5 text-blue-500"/> Vencimiento</label>
                        <div className="relative group">
                          <Input 
                            type="date"
                            className="h-11 bg-black/40 border-white/5 hover:border-primary/40 rounded-2xl font-bold text-slate-300 transition-all focus:ring-primary/20"
                            value={displayTask.due_date ? displayTask.due_date.split('T')[0] : ''}
                            onChange={(e) => handleSave({ due_date: e.target.value })}
                          />
                          <CalendarIcon className="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-600 pointer-events-none group-hover:text-primary transition-colors" />
                        </div>
                      </div>
                   </div>

                   <div className="space-y-8">
                      <div className="space-y-3">
                        <label className="text-[10px] uppercase font-black text-slate-500 flex items-center gap-2 tracking-[0.2em]"><Tag className="h-3.5 w-3.5 text-purple-500"/> Etiquetas</label>
                        <div className="flex flex-wrap gap-2 min-h-[44px] bg-black/40 p-3 rounded-2xl border border-white/5">
                          {displayTask.tags?.map(tag => (
                            <motion.div initial={{ scale: 0.8 }} animate={{ scale: 1 }} key={tag.id}>
                              <Badge 
                                style={{ backgroundColor: tag.color || '#3b82f6', color: 'white' }}
                                className="text-[9px] py-0.5 px-3 cursor-pointer hover:brightness-110 flex items-center gap-1.5 border-none shadow-lg font-black uppercase tracking-wider"
                                onClick={() => handleTagToggle(tag.name)}
                              >
                                {tag.name}
                                <X className="h-2.5 w-2.5 opacity-50" />
                              </Badge>
                            </motion.div>
                          ))}
                          <Popover>
                            <PopoverTrigger asChild>
                              <Button variant="ghost" size="sm" className="h-6 w-6 p-0 rounded-full bg-white/5 hover:bg-white/10">
                                <Plus className="h-3 w-3 text-slate-500" />
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-56 p-2 bg-slate-900 border-white/10 text-white rounded-xl">
                               <div className="space-y-1">
                                  {allTags.map(t => (
                                    <div key={t.id} className="flex items-center gap-2 p-2 hover:bg-white/5 rounded-lg cursor-pointer text-xs font-bold" onClick={() => handleTagToggle(t.name)}>
                                       <div className="h-2 w-2 rounded-full" style={{ backgroundColor: t.color }} />
                                       {t.name}
                                    </div>
                                  ))}
                               </div>
                            </PopoverContent>
                          </Popover>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <label className="text-[10px] uppercase font-black text-slate-500 flex items-center gap-2 tracking-[0.2em]"><Zap className="h-3.5 w-3.5 text-yellow-500"/> Proceso Vinculado</label>
                        <div className="flex items-center gap-2 p-3 bg-black/40 border border-white/5 rounded-2xl hover:bg-white/5 transition-all">
                           <Zap className="h-4 w-4 text-primary" />
                           <span className="text-xs font-bold text-primary truncate">11001400306820260022700</span>
                        </div>
                      </div>
                   </div>
                </div>

                {/* DESCRIPTION */}
                <div className="mb-10 space-y-4">
                  <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
                    <Edit3 className="h-3.5 w-3.5" /> Descripción
                  </div>
                  <Textarea 
                    className="min-h-[120px] bg-white/[0.02] border-white/5 focus:border-primary/40 rounded-3xl p-6 text-sm leading-relaxed text-slate-300 resize-none transition-all placeholder:text-slate-700"
                    placeholder="Describe los detalles de este caso jurídico..."
                    value={editedDesc}
                    onChange={(e) => setEditedDesc(e.target.value)}
                    onBlur={() => handleSave({ description: editedDesc })}
                  />
                </div>
                
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </SheetContent>
    </Sheet>
  );
}
