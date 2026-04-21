import React, { useState, useEffect } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Calendar as CalendarIcon, CheckCircle2, Clock, Tag, User as UserIcon, CheckSquare, Plus } from 'lucide-react';
import { Task as TaskType, updateTask } from '@/services/api';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

interface TaskDrawerProps {
  task: TaskType | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskUpdate: (updatedTask: TaskType) => void;
}

export function TaskDrawer({ task, open, onOpenChange, onTaskUpdate }: TaskDrawerProps) {
  const { toast } = useToast();
  const [editedTitle, setEditedTitle] = useState('');
  const [editedDesc, setEditedDesc] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (task) {
      setEditedTitle(task.title || '');
      setEditedDesc(task.description || '');
    }
  }, [task]);

  const handleSave = async (field: Partial<TaskType>) => {
    if (!task) return;
    setIsLoading(true);
    try {
      const updated = await updateTask(task.id, field);
      onTaskUpdate(updated);
      toast({ title: 'Tarea actualizada', description: 'Los cambios han sido guardados.' });
    } catch (e: any) {
      toast({ title: 'Error', description: e.message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  if (!task) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[500px] bg-background/80 backdrop-blur-3xl overflow-y-auto border-l-border/50 shadow-2xl">
        <SheetHeader className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="outline" className="uppercase text-[10px] h-5 tracking-wider bg-primary/10 text-primary border-primary/20">
              {task.status}
            </Badge>
            {task.priority && (
              <Badge variant="secondary" className="uppercase text-[10px] h-5">
                {task.priority}
              </Badge>
            )}
          </div>
          <Input 
            className="text-2xl font-bold px-0 bg-transparent border-0 focus-visible:ring-0 shadow-none h-auto py-1"
            value={editedTitle}
            onChange={(e) => setEditedTitle(e.target.value)}
            onBlur={() => editedTitle !== task.title && handleSave({ title: editedTitle })}
            disabled={isLoading}
          />
        </SheetHeader>

        <div className="space-y-6">
          {/* Properties Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground flex items-center gap-1"><UserIcon className="h-3 w-3"/> Asignado</label>
              <div className="flex items-center gap-2 text-sm font-medium">
                <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-[10px]">
                  {task.assignee_id ? 'AB' : '--'}
                </div>
                {task.assignee_id ? `Usuario ID: ${task.assignee_id}` : 'Sin asignar'}
              </div>
            </div>
            
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground flex items-center gap-1"><CalendarIcon className="h-3 w-3"/> Vencimiento</label>
              <div className="text-sm font-medium">
                {task.due_date ? format(new Date(task.due_date), "d 'de' MMMM, yyyy", { locale: es }) : 'No definida'}
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold flex items-center gap-2"><FileTextIcon /> Descripción</label>
            <Textarea 
              placeholder="Añade detalles a esta tarea..."
              className="resize-none min-h-[120px] bg-muted/40 border-border/50 focus-visible:bg-background"
              value={editedDesc}
              onChange={(e) => setEditedDesc(e.target.value)}
              onBlur={() => editedDesc !== task.description && handleSave({ description: editedDesc })}
              disabled={isLoading}
            />
          </div>

          {/* Subtasks / Checklists Stub */}
          <div className="space-y-3 pt-4 border-t border-border/50">
            <label className="text-sm font-semibold flex items-center gap-2 justify-between">
              <span className="flex items-center gap-2"><CheckSquare className="h-4 w-4"/> Checklists</span>
              <Button variant="ghost" size="sm" className="h-6 px-2 text-xs"><Plus className="h-3 w-3 mr-1"/> Añadir</Button>
            </label>
            <div className="text-center py-6 border border-dashed rounded-lg bg-muted/20">
              <p className="text-xs text-muted-foreground">No hay items de checklist.</p>
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
