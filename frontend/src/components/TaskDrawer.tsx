import React, { useState, useEffect } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Calendar as CalendarIcon, CheckCircle2, Clock, Tag, User as UserIcon, CheckSquare, Plus, LayoutGrid, MessageSquare } from 'lucide-react';
import { Task as TaskType, updateTask, createTask, getUsers, User, getTaskDetail, getCases, addComment, addChecklistItem, type CaseRow } from '@/services/api';
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
import { Search, FileText, CheckCircle } from 'lucide-react';

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
  }, []);

  // Buscar caso vinculado inicialmente
  useEffect(() => {
    if (task?.case_id) {
      getCases({ search: String(task.case_id), page_size: 1 }).then(res => {
        if (res.items.length > 0) setLinkedCase(res.items[0]);
      });
    } else {
      setLinkedCase(null);
    }
  }, [task?.case_id]);

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
    if (fullTask || task) {
      const t = fullTask || task!;
      setEditedTitle(t.title || '');
      setEditedDesc(t.description || '');
    }
  }, [fullTask, task]);

  const handleSave = async (field: Partial<TaskType>) => {
    if (!task) return;
    setIsLoading(true);
    try {
      if (task.id) {
        const updated = await updateTask(task.id, field);
        onTaskUpdate(updated);
        toast({ title: 'Tarea actualizada', description: 'Cambios guardados.' });
      } else {
        // Es una tarea nueva
        if (!field.title && !editedTitle) return; // No crear si esta vacia
        const toCreate = { ...task, ...field, title: field.title || editedTitle };
        const created = await createTask(toCreate);
        onTaskUpdate(created);
        toast({ title: 'Tarea creada', description: 'Iniciaste un nuevo flujo.' });
      }
    } catch (e: any) {
      toast({ title: 'Error', description: e.message || 'Error de servidor', variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddComment = async () => {
    if (!task || !newComment.trim()) return;
    setIsLoading(true);
    try {
      await addComment(task.id, newComment);
      setNewComment('');
      const updated = await getTaskDetail(task.id, clickupToken);
      onTaskUpdate(updated);
      setFullTask(updated);
    } catch(e) {
      toast({ title: 'Error', description: 'No se pudo agregar el comentario' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddChecklist = async () => {
    if (!task || !newChecklist.trim()) return;
    setIsLoading(true);
    try {
      await addChecklistItem(task.id, newChecklist);
      setNewChecklist('');
      const updated = await getTaskDetail(task.id, clickupToken);
      onTaskUpdate(updated);
      setFullTask(updated);
    } catch(e) {
      toast({ title: 'Error', description: 'No se pudo agregar item' });
    } finally {
      setIsLoading(false);
    }
  };

  const displayTask = fullTask || task;
  const handleAddSubtask = async () => {
    if (!newSubtaskTitle.trim() || !displayTask.id) return;
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
      setDisplayTask(prev => ({
        ...prev!,
        subtasks: [...(prev?.subtasks || []), res]
      }));
      setNewSubtaskTitle("");
      toast({ title: "Subtarea creada", description: res.title });
      onTaskUpdate?.({ ...displayTask, subtasks: [...(displayTask.subtasks || []), res] });
    } catch (e) {
      toast({ title: "Error", description: "No se pudo crear la subtarea", variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  if (!displayTask) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[500px] bg-background/80 backdrop-blur-3xl overflow-y-auto border-l-border/50 shadow-2xl">
        <SheetHeader className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="outline" className="uppercase text-[10px] h-5 tracking-wider bg-primary/10 text-primary border-primary/20">
              {displayTask.status}
            </Badge>
            {displayTask.priority && (
              <Badge variant="secondary" className="uppercase text-[10px] h-5">
                {displayTask.priority}
              </Badge>
            )}
          </div>
          <Input 
            className="text-2xl font-bold px-0 bg-transparent border-0 focus-visible:ring-0 shadow-none h-auto py-1"
            value={editedTitle}
            onChange={(e) => setEditedTitle(e.target.value)}
            onBlur={() => (editedTitle && editedTitle !== displayTask.title) && handleSave({ title: editedTitle })}
            disabled={isLoading}
            placeholder="Nombra esta tarea..."
          />
        </SheetHeader>

        <div className="space-y-6">
          {/* Properties Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground flex items-center gap-1"><UserIcon className="h-3 w-3"/> Asignado</label>
              <Select 
                value={displayTask.assignee_name || "unassigned"} 
                onValueChange={(val) => handleSave({ assignee_name: val === "unassigned" ? undefined : val })}
                disabled={isLoading}
              >
                <SelectTrigger className="h-9 bg-muted/40 border-border/50 hover:bg-muted transition-colors rounded-lg">
                  <SelectValue placeholder="Sin asignar" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unassigned" className="text-muted-foreground">Sin asignar</SelectItem>
                  {Array.from(new Set([...allAssignees, displayTask.assignee_name].filter(Boolean))).map(name => (
                    <SelectItem key={name!} value={name!}>
                      <div className="flex items-center gap-2">
                        <div className="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center text-[8px] font-bold">
                          {name![0].toUpperCase()}
                        </div>
                        <span>{name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground flex items-center gap-1"><CalendarIcon className="h-3 w-3"/> Vencimiento</label>
              <Input 
                type="date"
                className="h-9 bg-muted/40 border-border/50 text-xs rounded-lg"
                value={displayTask.due_date ? displayTask.due_date.split('T')[0] : ''}
                onChange={(e) => handleSave({ due_date: e.target.value })}
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold flex items-center gap-2"><FileTextIcon /> Descripción</label>
            <Textarea 
              placeholder="Añade detalles a esta tarea..."
              className="resize-none min-h-[120px] bg-muted/40 border-border/50 focus-visible:bg-background"
              value={editedDesc}
              onChange={(e) => setEditedDesc(e.target.value)}
              onBlur={() => editedDesc !== displayTask.description && handleSave({ description: editedDesc })}
              disabled={isLoading}
            />
          </div>

          {/* VINCULACIÓN DE PROCESO (RADICADO) */}
          <div className="space-y-3 pt-4 border-t border-border/50">
             <label className="text-sm font-semibold flex items-center gap-2">
               <FileText className="h-4 w-4 text-primary" /> Proceso Judicial Vinculado
             </label>
             
             {linkedCase ? (
               <div className="p-4 rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border border-primary/20 flex flex-col gap-3 relative group shadow-sm">
                  <div className="flex justify-between items-start">
                    <div className="space-y-0.5">
                      <div className="text-[10px] uppercase tracking-wider text-primary font-bold">Radicado</div>
                      <div className="text-sm font-bold font-mono tracking-tight">{linkedCase.radicado}</div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-8 w-8 rounded-full hover:bg-red-500/10 hover:text-red-600 transition-colors"
                      onClick={() => handleSave({ case_id: null as any })}
                      title="Desvincular proceso"
                    >
                      <Plus className="h-4 w-4 rotate-45" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-2 gap-4 py-2 border-y border-primary/10">
                    <div className="space-y-0.5">
                       <div className="text-[10px] uppercase text-muted-foreground font-bold">Demandante</div>
                       <div className="text-xs font-semibold truncate">{linkedCase.demandante || 'No definido'}</div>
                    </div>
                    <div className="space-y-0.5">
                       <div className="text-[10px] uppercase text-muted-foreground font-bold">Demandado</div>
                       <div className="text-xs font-semibold truncate">{linkedCase.demandado || 'No definido'}</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-1">
                    <div className="flex items-center gap-2">
                       <Badge variant="outline" className="text-[9px] h-4 bg-background border-primary/20 text-primary">Sincronizado</Badge>
                       <span className="text-[10px] text-muted-foreground truncate max-w-[150px]">{linkedCase.juzgado}</span>
                    </div>
                    <Button 
                      variant="link" 
                      className="h-auto p-0 text-primary text-xs font-bold hover:no-underline hover:text-primary/80"
                      onClick={() => window.open(`/casos/${linkedCase.id}`, '_blank')}
                    >
                      Ver Proceso Completo →
                    </Button>
                  </div>
               </div>
             ) : (
               <div className="space-y-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input 
                      placeholder="Buscar por radicado o nombre..." 
                      className="pl-9 h-9 bg-muted/20 border-border/50 rounded-lg text-sm"
                      value={caseSearch}
                      onChange={(e) => setCaseSearch(e.target.value)}
                    />
                  </div>
                  {caseResults.length > 0 && (
                    <div className="border border-border/50 rounded-xl overflow-hidden bg-card/50 backdrop-blur shadow-xl animate-in fade-in slide-in-from-top-2">
                      {caseResults.map(c => (
                        <div 
                          key={c.id} 
                          className="p-3 hover:bg-primary/10 cursor-pointer border-b border-border/20 last:border-0 transition-colors"
                          onClick={() => {
                            setLinkedCase(c);
                            setCaseResults([]);
                            setCaseSearch('');
                            handleSave({ case_id: c.id });
                          }}
                        >
                          <div className="text-xs font-bold font-mono truncate">{c.radicado}</div>
                          <div className="text-[9px] text-muted-foreground truncate">{c.demandante} vs {c.demandado}</div>
                        </div>
                      ))}
                    </div>
                  )}
               </div>
             )}
          </div>

          {/* SUBTAREAS */}
          <div className="space-y-3 pt-4 border-t border-border/50">
            <label className="text-sm font-semibold flex items-center gap-2 justify-between">
              <span className="flex items-center gap-2"><LayoutGrid className="h-4 w-4 text-primary" /> Subtareas</span>
            </label>
            
            <div className="space-y-2">
              <div className="flex gap-2 mb-2">
                <Input 
                  placeholder="Nueva subtarea..." 
                  className="h-8 text-xs bg-muted/20" 
                  value={newSubtaskTitle}
                  onChange={(e) => setNewSubtaskTitle(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddSubtask()}
                />
                <Button size="sm" className="h-8 h-8 px-2" onClick={handleAddSubtask}><Plus className="h-3 w-3" /></Button>
              </div>

              {displayTask.subtasks && displayTask.subtasks.length > 0 ? (
                <div className="space-y-2">
                  {displayTask.subtasks.map(sub => (
                    <div key={sub.id} className="flex items-center gap-3 p-2 rounded-lg bg-muted/30 border border-border/30 hover:bg-muted/50 transition-colors cursor-pointer group/sub">
                      <CheckCircle2 className={`h-4 w-4 ${sub.status === 'complete' ? 'text-green-500' : 'text-muted-foreground'}`} />
                      <span className="text-xs font-medium truncate flex-1">{sub.title}</span>
                      <Badge variant="outline" className="text-[9px] uppercase">{sub.status}</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[10px] text-muted-foreground text-center py-2 bg-muted/10 rounded-lg border border-dashed">No hay subtareas.</p>
              )}
            </div>
          </div>

          {/* CHECKLISTS */}
          <div className="space-y-3 pt-4 border-t border-border/50">
            <label className="text-sm font-semibold flex items-center gap-2 justify-between">
              <span className="flex items-center gap-2"><CheckSquare className="h-4 w-4 text-primary"/> Listas de control</span>
              <Button variant="ghost" size="sm" className="h-6 px-2 text-xs hover:bg-primary/10 hover:text-primary" onClick={handleAddChecklist}><Plus className="h-3 w-3 mr-1"/> Añadir</Button>
            </label>
            
            <div className="space-y-2">
              <div className="flex gap-2 mb-2">
                <Input 
                  placeholder="Nuevo item..." 
                  className="h-8 text-xs bg-muted/20" 
                  value={newChecklist}
                  onChange={(e) => setNewChecklist(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddChecklist()}
                />
                <Button size="sm" className="h-8 h-8 px-2" onClick={handleAddChecklist}><Plus className="h-3 w-3" /></Button>
              </div>
              {displayTask.checklists && displayTask.checklists.length > 0 ? (
                displayTask.checklists.map(item => (
                  <div key={item.id} className="flex items-center gap-3 group">
                    <div className={`h-5 w-5 rounded border flex items-center justify-center transition-colors ${item.is_completed ? 'bg-primary border-primary text-white' : 'border-border group-hover:border-primary/50'}`}>
                      {item.is_completed && <CheckCircle className="h-3.5 w-3.5" />}
                    </div>
                    <span className={`text-sm ${item.is_completed ? 'text-muted-foreground line-through' : 'text-foreground'}`}>
                      {item.content}
                    </span>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 border border-dashed rounded-xl bg-muted/10">
                  <p className="text-xs text-muted-foreground">No hay items en la lista de control.</p>
                </div>
              )}
            </div>
          </div>

          {/* COMENTARIOS / ACTIVIDAD */}
          <div className="space-y-4 pt-4 border-t border-border/50">
            <label className="text-sm font-semibold flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-primary" /> Comentarios y Actividad
            </label>
            
            <div className="space-y-3">
              {displayTask.comments && displayTask.comments.length > 0 ? (
                displayTask.comments.map(comm => (
                  <div key={comm.id} className="p-3 rounded-xl bg-muted/20 border border-border/30 text-xs">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-primary">Sistema / ClickUp</span>
                      <span className="text-[10px] text-muted-foreground">
                        {comm.created_at ? (() => {
                          try {
                            const d = new Date(comm.created_at);
                            return isNaN(d.getTime()) ? 'Reciente' : format(d, "d MMM, HH:mm", { locale: es });
                          } catch(e) { return 'Reciente'; }
                        })() : 'Reciente'}
                      </span>
                    </div>
                    <p className="text-foreground/80 leading-relaxed">{comm.content}</p>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 border border-dashed rounded-xl bg-muted/10">
                  <p className="text-xs text-muted-foreground">No hay comentarios en esta tarea.</p>
                </div>
              )}
              
              <div className="flex gap-2 pt-2">
                <Input 
                  placeholder="Escribe un comentario..." 
                  className="h-9 text-xs bg-muted/20" 
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddComment()}
                />
                <Button size="sm" className="h-9 px-3" onClick={handleAddComment}><Plus className="h-4 w-4" /></Button>
              </div>
            </div>
          </div>

        </div>
      </SheetContent>
    </Sheet>
  );
}

function FileTextIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>
  );
}
