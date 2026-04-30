import React, { useState, useEffect } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Calendar as CalendarIcon, CheckCircle2, Clock, Tag, User as UserIcon, 
  CheckSquare, Plus, LayoutGrid, MessageSquare, Trash2, Edit2, Trash, 
  CheckCircle, Paperclip, Share2, History, Eye, Link2, ExternalLink,
  ChevronDown, AlertTriangle, Flag, Zap, MoreHorizontal, FileText, Search
} from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Task as TaskType, updateTask, createTask, getUsers, User, getTaskDetail, getCases, addComment, addChecklistItem, deleteComment, updateChecklistItem, deleteChecklistItem, getTags, type CaseRow, type Tag } from '@/services/api';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";

interface TaskDrawerProps {
  task: TaskType | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskUpdate: (updatedTask: TaskType) => void;
  clickupToken?: string;
  allAssignees?: string[];
}

export function TaskDrawer({ task, open, onOpenChange, onTaskUpdate, clickupToken, allAssignees = [] }: TaskDrawerProps) {
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
  const [newSubtaskTitle, setNewSubtaskTitle] = useState("");
  const [allTags, setAllTags] = useState<Tag[]>([]);

  const displayTask = fullTask || task;

  useEffect(() => {
    if (task && open) {
      setIsLoading(true);
      getTaskDetail(task.id, clickupToken)
        .then(res => setFullTask(res))
        .catch(err => {
          console.error("Error fetching task details", err);
          setFullTask(task);
        })
        .finally(() => setIsLoading(false));
    } else {
      setFullTask(null);
    }
  }, [task?.id, open]);

  useEffect(() => {
    getUsers().then(setUsers).catch(console.error);
    getTags().then(setAllTags).catch(console.error);
  }, []);

  // Buscar caso vinculado inicialmente
  useEffect(() => {
    if (displayTask?.case_id) {
      getCases({ search: String(displayTask.case_id), page_size: 1 }).then(res => {
        if (res.items.length > 0) setLinkedCase(res.items[0]);
      });
    } else {
      setLinkedCase(null);
    }
  }, [displayTask?.case_id]);

  // Búsqueda dinámica de casos
  useEffect(() => {
    const delay = setTimeout(() => {
      if (caseSearch.length > 3) {
        getCases({ search: caseSearch, page_size: 5 }).then(res => setCaseResults(res.items));
      } else {
        setCaseResults([]);
      }
    }, 400);
    return () => clearTimeout(delay);
  }, [caseSearch]);

  useEffect(() => {
    if (displayTask) {
      setEditedTitle(displayTask.title || '');
      setEditedDesc(displayTask.description || '');
    }
  }, [displayTask]);

  const getPriorityColor = (p: string | undefined) => {
    switch(p?.toLowerCase()) {
      case 'urgent': return 'text-red-500 bg-red-500/10 border-red-500/20';
      case 'high': return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
      case 'normal': return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
      case 'low': return 'text-slate-500 bg-slate-500/10 border-slate-500/20';
      default: return 'text-muted-foreground bg-muted/30 border-border/30';
    }
  };

  const getStatusColor = (s: string | undefined) => {
    switch(s?.toLowerCase()) {
      case 'complete': return 'bg-green-500 text-white';
      case 'in progress': return 'bg-blue-500 text-white';
      case 'to do': return 'bg-slate-500 text-white';
      default: return 'bg-primary text-white';
    }
  };

  const handleTagToggle = async (tagName: string) => {
    if (!displayTask) return;
    const currentTags = displayTask.tags?.map(t => t.name) || [];
    let nextTags: string[];
    if (currentTags.includes(tagName)) {
      nextTags = currentTags.filter(t => t !== tagName);
    } else {
      nextTags = [...currentTags, tagName];
    }
    
    try {
      const updated = await updateTask(displayTask.id, { tags: nextTags as any });
      const fullUpdated = await getTaskDetail(displayTask.id, clickupToken);
      setFullTask(fullUpdated);
      onTaskUpdate(fullUpdated);
    } catch (e) {
      toast({ title: "Error", description: "No se pudo actualizar etiquetas", variant: "destructive" });
    }
  };

  const handleSave = async (field: Partial<TaskType>) => {
    if (!displayTask) return;
    setIsLoading(true);
    try {
      const updated = await updateTask(displayTask.id, field);
      setFullTask(updated);
      onTaskUpdate(updated);
      toast({ title: 'Tarea actualizada', description: 'Cambios guardados.' });
    } catch (e: any) {
      toast({ title: 'Error', description: e.message || 'Error de servidor', variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddComment = async () => {
    if (!displayTask || !newComment.trim()) return;
    setIsLoading(true);
    try {
      await addComment(displayTask.id, newComment);
      setNewComment('');
      const updated = await getTaskDetail(displayTask.id, clickupToken);
      setFullTask(updated);
      onTaskUpdate(updated);
    } catch(e) {
      toast({ title: 'Error', description: 'No se pudo agregar el comentario' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddChecklist = async () => {
    if (!displayTask || !newChecklist.trim()) return;
    setIsLoading(true);
    try {
      await addChecklistItem(displayTask.id, newChecklist);
      setNewChecklist('');
      const updated = await getTaskDetail(displayTask.id, clickupToken);
      setFullTask(updated);
      onTaskUpdate(updated);
    } catch (e) {
      toast({ title: "Error", description: "No se pudo añadir el item", variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    if (!displayTask) return;
    try {
      await deleteComment(commentId);
      const updated = { ...displayTask, comments: displayTask.comments?.filter(c => c.id !== commentId) || [] };
      setFullTask(updated);
      onTaskUpdate(updated);
      toast({ title: "Comentario eliminado" });
    } catch (e) {
      toast({ title: "Error", description: "No se pudo eliminar el comentario", variant: "destructive" });
    }
  };

  const handleToggleChecklist = async (itemId: number, currentStatus: boolean) => {
    if (!displayTask) return;
    try {
      const res = await updateChecklistItem(itemId, { is_completed: !currentStatus });
      const updated = { ...displayTask, checklists: displayTask.checklists?.map(c => c.id === itemId ? res : c) || [] };
      setFullTask(updated);
      onTaskUpdate(updated);
    } catch (e) {
      toast({ title: "Error", description: "No se pudo actualizar el item", variant: "destructive" });
    }
  };

  const handleDeleteChecklist = async (itemId: number) => {
    if (!displayTask) return;
    try {
      await deleteChecklistItem(itemId);
      const updated = { ...displayTask, checklists: displayTask.checklists?.filter(c => c.id !== itemId) || [] };
      setFullTask(updated);
      onTaskUpdate(updated);
      toast({ title: "Item eliminado" });
    } catch (e) {
      toast({ title: "Error", description: "No se pudo eliminar el item", variant: "destructive" });
    }
  };

  const handleEditChecklist = async (itemId: number, newContent: string) => {
    if (!displayTask || !newContent.trim()) return;
    try {
      const res = await updateChecklistItem(itemId, { content: newContent });
      const updated = { ...displayTask, checklists: displayTask.checklists?.map(c => c.id === itemId ? res : c) || [] };
      setFullTask(updated);
      onTaskUpdate(updated);
    } catch (e) {
      toast({ title: "Error", description: "No se pudo editar el item", variant: "destructive" });
    }
  };

  const handleAddSubtask = async () => {
    if (!newSubtaskTitle.trim() || !displayTask?.id) return;
    setIsLoading(true);
    try {
      const res = await createTask({
        title: newSubtaskTitle,
        parent_id: displayTask.id,
        list_id: displayTask.list_id,
        case_id: displayTask.case_id,
        status: 'to do',
        priority: 'normal'
      });
      const updated = { ...displayTask, subtasks: [...(displayTask.subtasks || []), res] };
      setFullTask(updated);
      setNewSubtaskTitle("");
      onTaskUpdate(updated);
      toast({ title: "Subtarea creada", description: res.title });
    } catch (e) {
      toast({ title: "Error", description: "No se pudo crear la subtarea", variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  const parsedCustomFields = displayTask?.custom_fields ? (() => {
    try {
      return JSON.parse(displayTask.custom_fields);
    } catch(e) { return []; }
  })() : [];

  if (!displayTask) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[650px] p-0 border-l border-border/40 shadow-2xl overflow-hidden flex flex-col bg-background/95 backdrop-blur-xl">
        {/* HEADER BAR */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/40 bg-muted/20">
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="text-[10px] font-mono bg-background/50 border-border/40">
              ID: {displayTask.clickup_id || displayTask.id}
            </Badge>
            <div className="h-4 w-[1px] bg-border/40" />
            <span className="text-[10px] text-muted-foreground flex items-center gap-1 font-medium">
              <History className="h-3 w-3" /> Actualizado {displayTask.created_at ? format(new Date(displayTask.created_at), "d MMM, HH:mm", { locale: es }) : 'Reciente'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full hover:bg-primary/10 hover:text-primary">
                    <Share2 className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Compartir</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full" onClick={() => onOpenChange(false)}>
              <Plus className="h-4 w-4 rotate-45" />
            </Button>
          </div>
        </div>

        <ScrollArea className="flex-1 px-0">
          <div className="p-6 space-y-8">
            {/* HERO SECTION */}
            <div className="space-y-6">
              <div className="space-y-2">
                <Input 
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                  onBlur={() => editedTitle !== displayTask.title && handleSave({ title: editedTitle })}
                  className="text-2xl font-bold border-none bg-transparent hover:bg-muted/30 focus:bg-muted/40 transition-all p-0 h-auto placeholder:text-muted-foreground/30 shadow-none focus-visible:ring-0"
                  placeholder="Título de la tarea..."
                />
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <Select value={displayTask.status || 'to do'} onValueChange={(v) => handleSave({ status: v })}>
                  <SelectTrigger className={`w-auto h-8 px-3 rounded-full border-none font-bold text-[10px] uppercase tracking-wider transition-all shadow-sm ${getStatusColor(displayTask.status)} hover:brightness-110`}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="to do">To Do</SelectItem>
                    <SelectItem value="in progress">En Progreso</SelectItem>
                    <SelectItem value="complete">Completado</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={displayTask.priority || 'normal'} onValueChange={(v) => handleSave({ priority: v })}>
                  <SelectTrigger className={`w-auto h-8 px-3 rounded-full bg-background border border-border/40 font-bold text-[10px] uppercase tracking-wider transition-all shadow-sm ${getPriorityColor(displayTask.priority)}`}>
                    <div className="flex items-center gap-2">
                      <Flag className="h-3 w-3 fill-current" />
                      <SelectValue />
                    </div>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="urgent">Urgente</SelectItem>
                    <SelectItem value="high">Alta</SelectItem>
                    <SelectItem value="normal">Normal</SelectItem>
                    <SelectItem value="low">Baja</SelectItem>
                  </SelectContent>
                </Select>

                <div className="flex-1" />
                
                <div className="flex items-center gap-2 text-[10px] text-muted-foreground bg-muted/10 px-3 py-1.5 rounded-full border border-border/30">
                  <Zap className="h-3 w-3 text-yellow-500 fill-yellow-500" />
                  <span>Sincronización Automática Activa</span>
                </div>
              </div>
            </div>

            {/* PROPERTIES GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6 bg-muted/10 p-5 rounded-2xl border border-border/30 relative overflow-hidden">
               <div className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-2 tracking-widest"><UserIcon className="h-3 w-3"/> Responsable</label>
                    <Select value={displayTask.assignee_id?.toString() || 'unassigned'} onValueChange={(v) => handleSave({ assignee_id: v === 'unassigned' ? null : parseInt(v) })}>
                      <SelectTrigger className="h-9 bg-background border-border/40 hover:border-primary/40 rounded-lg shadow-sm transition-all">
                        <SelectValue placeholder="Sin asignar" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="unassigned">Sin asignar</SelectItem>
                        {users.map(u => (
                          <SelectItem key={u.id} value={u.id.toString()}>
                            <div className="flex items-center gap-2">
                              <div className="h-5 w-5 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-bold text-primary">
                                {u.nombre?.charAt(0) || u.username.charAt(0)}
                              </div>
                              {u.nombre || u.username}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-2 tracking-widest"><CalendarIcon className="h-3 w-3"/> Vencimiento</label>
                    <Input 
                      type="date"
                      className="h-9 bg-background border-border/40 hover:border-primary/40 rounded-lg shadow-sm"
                      value={displayTask.due_date ? displayTask.due_date.split('T')[0] : ''}
                      onChange={(e) => handleSave({ due_date: e.target.value })}
                    />
                  </div>
               </div>

               <div className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-2 tracking-widest"><Tag className="h-3 w-3"/> Etiquetas</label>
                    <div className="flex flex-wrap gap-1.5 items-center min-h-[36px] bg-background/50 p-1 rounded-lg border border-border/20">
                      {displayTask.tags?.map(tag => (
                        <Badge 
                          key={tag.id} 
                          style={{ backgroundColor: tag.color || '#3b82f6', color: 'white' }}
                          className="text-[9px] py-0 px-2 cursor-pointer hover:opacity-80 flex items-center gap-1 border-none shadow-sm"
                          onClick={() => handleTagToggle(tag.name)}
                        >
                          {tag.name}
                          <Plus className="h-3 w-3 rotate-45" />
                        </Badge>
                      ))}
                      <Select onValueChange={handleTagToggle}>
                        <SelectTrigger className="w-auto h-6 text-[9px] bg-primary/10 text-primary border-none rounded-full px-2 hover:bg-primary/20 transition-all font-bold">
                          <Plus className="h-3 w-3 mr-1" /> Añadir
                        </SelectTrigger>
                        <SelectContent>
                          {allTags.filter(t => !(displayTask.tags?.some(dt => dt.name === t.name))).map(t => (
                            <SelectItem key={t.id} value={t.name}>
                              <div className="flex items-center gap-2">
                                <div className="h-2 w-2 rounded-full" style={{ backgroundColor: t.color || '#3b82f6' }} />
                                {t.name}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-2 tracking-widest"><LayoutGrid className="h-3 w-3"/> Caso Vinculado</label>
                    <div className="space-y-2">
                      {linkedCase ? (
                        <div className="flex items-center justify-between p-2 rounded-lg bg-primary/5 border border-primary/20">
                          <div className="flex items-center gap-2 overflow-hidden">
                            <div className="h-6 w-6 rounded bg-primary/10 flex items-center justify-center text-primary"><Search className="h-3 w-3"/></div>
                            <span className="text-[11px] font-semibold truncate text-primary">{linkedCase.radicado}</span>
                          </div>
                          <Button variant="ghost" size="icon" className="h-6 w-6 hover:text-red-500" onClick={() => handleSave({ case_id: null })}><Trash2 className="h-3 w-3"/></Button>
                        </div>
                      ) : (
                        <div className="relative">
                          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/50" />
                          <Input 
                            placeholder="Buscar radicado..."
                            className="h-9 pl-9 bg-background border-border/40 rounded-lg text-xs"
                            value={caseSearch}
                            onChange={(e) => setCaseSearch(e.target.value)}
                          />
                          {caseResults.length > 0 && (
                            <div className="absolute top-full left-0 right-0 mt-1 bg-popover border border-border shadow-xl rounded-xl z-50 py-1 overflow-hidden">
                              {caseResults.map(c => (
                                <div 
                                  key={c.id} 
                                  onClick={() => handleSave({ case_id: c.id })}
                                  className="px-3 py-2 text-[11px] hover:bg-accent cursor-pointer flex justify-between items-center transition-colors border-b border-border/30 last:border-0"
                                >
                                  <span className="font-medium">{c.radicado}</span>
                                  <span className="text-[9px] text-muted-foreground">{c.clase_proceso}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
               </div>
            </div>

            {/* CUSTOM FIELDS */}
            {parsedCustomFields.length > 0 && (
              <div className="space-y-3">
                <label className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-2 tracking-widest"><AlertTriangle className="h-3 w-3"/> Campos de ClickUp</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {parsedCustomFields.filter((f: any) => f.value !== undefined).map((field: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-xl bg-muted/20 border border-border/30 hover:bg-muted/30 transition-all group">
                      <div className="text-[9px] text-muted-foreground font-bold uppercase truncate mb-1 group-hover:text-primary transition-colors">{field.name}</div>
                      <div className="text-xs font-semibold truncate">
                        {typeof field.value === 'object' ? JSON.stringify(field.value) : field.value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TABS */}
            <Tabs defaultValue="desc" className="w-full">
              <TabsList className="grid w-full grid-cols-4 bg-muted/30 p-1 rounded-xl h-11 border border-border/40">
                <TabsTrigger value="desc" className="text-[11px] font-bold gap-2 rounded-lg data-[state=active]:bg-background data-[state=active]:shadow-sm"><FileText className="h-3.5 w-3.5" /> Notas</TabsTrigger>
                <TabsTrigger value="subs" className="text-[11px] font-bold gap-2 rounded-lg data-[state=active]:bg-background data-[state=active]:shadow-sm"><LayoutGrid className="h-3.5 w-3.5" /> Subtareas</TabsTrigger>
                <TabsTrigger value="check" className="text-[11px] font-bold gap-2 rounded-lg data-[state=active]:bg-background data-[state=active]:shadow-sm"><CheckSquare className="h-3.5 w-3.5" /> Listas</TabsTrigger>
                <TabsTrigger value="docs" className="text-[11px] font-bold gap-2 rounded-lg data-[state=active]:bg-background data-[state=active]:shadow-sm"><Paperclip className="h-3.5 w-3.5" /> Docs</TabsTrigger>
              </TabsList>

              <TabsContent value="desc" className="mt-4">
                <Textarea 
                  placeholder="Añade una descripción detallada o notas aquí..."
                  className="min-h-[250px] bg-muted/10 border-border/30 rounded-2xl p-4 text-sm leading-relaxed focus-visible:ring-primary/20 resize-none transition-all"
                  value={editedDesc}
                  onChange={(e) => setEditedDesc(e.target.value)}
                  onBlur={() => editedDesc !== displayTask.description && handleSave({ description: editedDesc })}
                />
              </TabsContent>

              <TabsContent value="subs" className="mt-4 space-y-4">
                <div className="flex gap-2">
                  <Input 
                    placeholder="Escribe el nombre de la nueva subtarea..." 
                    className="h-10 text-xs bg-muted/20 rounded-xl" 
                    value={newSubtaskTitle}
                    onChange={(e) => setNewSubtaskTitle(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddSubtask()}
                  />
                  <Button size="icon" className="h-10 w-10 rounded-xl" onClick={handleAddSubtask}><Plus className="h-4 w-4" /></Button>
                </div>
                
                {displayTask.subtasks && displayTask.subtasks.length > 0 ? (
                  <div className="grid grid-cols-1 gap-3">
                    {displayTask.subtasks.map((sub, idx) => (
                      <div key={sub.id} className="flex items-center gap-4 p-4 rounded-xl bg-background border border-border/40 hover:border-primary/40 transition-all group cursor-pointer shadow-sm">
                         <div className={`h-8 w-8 rounded-full flex items-center justify-center ${sub.status === 'complete' ? 'bg-green-100 text-green-600' : 'bg-muted/80 text-muted-foreground'}`}>
                           <CheckCircle2 className="h-4 w-4" />
                         </div>
                         <div className="flex-1 overflow-hidden">
                           <div className="text-sm font-bold truncate text-foreground/80 group-hover:text-primary transition-colors">{sub.title}</div>
                           <div className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">{sub.status}</div>
                         </div>
                         <Badge variant="outline" className="text-[9px] border-border/40 font-mono">ST-{idx+1}</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 bg-muted/10 rounded-2xl border border-dashed border-border/50 text-muted-foreground">
                    <LayoutGrid className="h-8 w-8 mb-3 opacity-20" />
                    <p className="text-xs font-medium italic">Esta tarea principal aún no tiene ramificaciones.</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="check" className="mt-4 space-y-4">
                <div className="flex gap-2">
                  <Input 
                    placeholder="Añadir paso a seguir..." 
                    className="h-10 text-xs bg-muted/20 rounded-xl" 
                    value={newChecklist}
                    onChange={(e) => setNewChecklist(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddChecklist()}
                  />
                  <Button size="icon" className="h-10 w-10 rounded-xl" onClick={handleAddChecklist}><Plus className="h-4 w-4" /></Button>
                </div>

                <div className="space-y-2">
                  {displayTask.checklists && displayTask.checklists.length > 0 ? (
                    displayTask.checklists.map(item => (
                      <div key={item.id} className="flex items-center gap-4 p-4 rounded-xl bg-muted/5 border border-border/20 group hover:bg-muted/10 transition-all">
                        <div 
                          onClick={() => handleToggleChecklist(item.id, !!item.is_completed)}
                          className={`h-6 w-6 rounded-lg border-2 flex items-center justify-center cursor-pointer transition-all ${item.is_completed ? 'bg-primary border-primary text-white scale-110 shadow-lg shadow-primary/30' : 'border-border/60 hover:border-primary/40'}`}
                        >
                          {item.is_completed && <CheckCircle className="h-4 w-4" />}
                        </div>
                        <span 
                          className={`text-sm flex-1 font-medium ${item.is_completed ? 'text-muted-foreground/50 line-through' : 'text-foreground/80'}`}
                          onBlur={(e) => (e.target as HTMLElement).innerText !== item.content && handleEditChecklist(item.id, (e.target as HTMLElement).innerText)}
                          contentEditable={!item.is_completed}
                          suppressContentEditableWarning
                        >
                          {item.content}
                        </span>
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity hover:text-red-500 hover:bg-red-500/10 rounded-lg"
                          onClick={() => handleDeleteChecklist(item.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))
                  ) : (
                    <div className="flex flex-col items-center justify-center py-12 bg-muted/10 rounded-2xl border border-dashed border-border/50 text-muted-foreground">
                      <CheckSquare className="h-8 w-8 mb-3 opacity-20" />
                      <p className="text-xs font-medium italic">Define los pasos para completar esta tarea.</p>
                    </div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="docs" className="mt-4">
                <div className="space-y-4">
                   <div className="flex items-center justify-between">
                     <h5 className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">Documentos y Evidencias</h5>
                     <Button variant="outline" size="sm" className="text-[10px] h-7 gap-2 rounded-lg border-dashed border-primary/40 text-primary hover:bg-primary/5">
                        <Plus className="h-3 w-3"/> Subir Archivo
                     </Button>
                   </div>
                   
                   {displayTask.attachments && displayTask.attachments.length > 0 ? (
                     <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {displayTask.attachments.map(att => (
                          <a 
                            key={att.id} 
                            href={att.file_path} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="flex items-center gap-3 p-3 rounded-xl bg-background border border-border/40 hover:border-primary/40 hover:shadow-md transition-all group overflow-hidden"
                          >
                             <div className="h-10 w-10 rounded-lg bg-muted/40 flex items-center justify-center text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                               <Paperclip className="h-5 w-5" />
                             </div>
                             <div className="flex-1 overflow-hidden">
                               <div className="text-xs font-bold truncate text-foreground/80">{att.name}</div>
                               <div className="text-[9px] text-muted-foreground uppercase flex items-center gap-1">
                                 {att.file_type || 'Archivo'} <ExternalLink className="h-2 w-2"/>
                               </div>
                             </div>
                          </a>
                        ))}
                     </div>
                   ) : (
                     <div className="flex flex-col items-center justify-center py-12 bg-muted/10 rounded-2xl border border-dashed border-border/50 text-muted-foreground">
                        <Paperclip className="h-8 w-8 mb-3 opacity-20" />
                        <p className="text-xs font-medium italic">No se han detectado archivos adjuntos en ClickUp.</p>
                     </div>
                   )}
                </div>
              </TabsContent>
            </Tabs>

            {/* ACTIVITY FEED */}
            <div className="space-y-6 pt-6 border-t border-border/40">
              <label className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-2 tracking-widest"><MessageSquare className="h-3 w-3"/> Flujo de Actividad</label>
              
              <div className="flex gap-3">
                <Textarea 
                  placeholder="Escribe una actualización o comentario..." 
                  className="min-h-[100px] text-xs bg-muted/10 border-border/30 rounded-2xl p-4 focus-visible:ring-primary/20 resize-none"
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                />
                <Button 
                  className="h-auto w-12 rounded-2xl" 
                  onClick={handleAddComment}
                  disabled={isLoading || !newComment.trim()}
                >
                  <MessageSquare className="h-4 w-4" />
                </Button>
              </div>

              <div className="space-y-6">
                {displayTask.comments && displayTask.comments.length > 0 ? (
                  displayTask.comments.map(comm => (
                    <div key={comm.id} className="flex gap-4 group">
                      <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-primary to-primary/60 flex items-center justify-center text-[10px] font-bold text-white shadow-sm flex-shrink-0">
                        {comm.author_name?.charAt(0) || 'S'}
                      </div>
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center justify-between">
                           <div className="flex items-center gap-2">
                             <span className="text-xs font-bold text-foreground/90">{comm.author_name || 'Sistema / ClickUp'}</span>
                             <span className="text-[10px] text-muted-foreground font-medium">
                                {comm.created_at ? format(new Date(comm.created_at), "d MMM, HH:mm", { locale: es }) : 'Reciente'}
                             </span>
                           </div>
                           <Button 
                              variant="ghost" 
                              size="icon" 
                              className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity hover:text-red-500 hover:bg-red-500/10 rounded-lg"
                              onClick={() => handleDeleteComment(comm.id)}
                           >
                             <Trash2 className="h-3 w-3" />
                           </Button>
                        </div>
                        <div className="p-4 rounded-2xl rounded-tl-none bg-background border border-border/40 shadow-sm text-sm text-foreground/80 leading-relaxed">
                          {comm.content}
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-center text-[11px] text-muted-foreground italic py-8 border border-dashed border-border/30 rounded-2xl">Aún no hay mensajes en esta tarea.</p>
                )}
              </div>
            </div>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
