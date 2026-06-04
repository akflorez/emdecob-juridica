import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Plus, Users, Building2, ShieldAlert } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { apiFetch, getBillingTiers, getBillingSimulator, updateBillingTiers, BillingTier, BillingSimulatorResult } from '@/services/api';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { DollarSign, Save, RefreshCw, MoreHorizontal } from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';export default function AdminDashboard() {
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [companies, setCompanies] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [tiers, setTiers] = useState<BillingTier[]>([]);
  const [simulatorData, setSimulatorData] = useState<BillingSimulatorResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingTiers, setSavingTiers] = useState(false);

  // Modals
  const [isCompanyModalOpen, setIsCompanyModalOpen] = useState(false);
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const [suspendModalOpen, setSuspendModalOpen] = useState(false);
  const [suspendCompanyId, setSuspendCompanyId] = useState<number | null>(null);
  const [suspendReason, setSuspendReason] = useState("");
  const [suspendNotes, setSuspendNotes] = useState("");

  // Forms
  const [newCompany, setNewCompany] = useState({ nombre: '', nit: '', limite_usuarios: 5 });
  const [newUser, setNewUser] = useState({ username: '', password: '', nombre: '', company_id: '', email: '', is_admin: false });

  useEffect(() => {
    if (user?.is_admin && !user?.company_id) {
      fetchData();
    }
  }, [user]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [compRes, usrRes, tiersRes, simRes] = await Promise.all([
        apiFetch<any[]>('/admin/companies'),
        apiFetch<any[]>('/admin/users'),
        getBillingTiers().catch(() => ({ tiers: [] as BillingTier[] })),
        getBillingSimulator().catch(() => ({ simulator: [] as BillingSimulatorResult[] }))
      ]);
      setCompanies(compRes || []);
      setUsers(usrRes || []);
      if (tiersRes && 'tiers' in tiersRes) setTiers(tiersRes.tiers);
      if (simRes && 'simulator' in simRes) setSimulatorData(simRes.simulator);
    } catch (error: any) {
      toast({ title: "Error", description: "No se pudieron cargar los datos.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompany = async () => {
    try {
      const res = await apiFetch<any>('/admin/companies', {
        method: 'POST',
        body: JSON.stringify(newCompany)
      });
      setCompanies([...companies, res]);
      setIsCompanyModalOpen(false);
      setNewCompany({ nombre: '', nit: '', limite_usuarios: 5 });
      toast({ title: "Empresa creada", description: "La empresa se creó correctamente." });
    } catch (e: any) {
      toast({ title: "Error", description: e.message || "No se pudo crear la empresa", variant: "destructive" });
    }
  };

  const handleCreateUser = async () => {
    try {
      const res = await apiFetch<any>('/admin/users', {
        method: 'POST',
        body: JSON.stringify({
          ...newUser,
          company_id: parseInt(newUser.company_id)
        })
      });
      setUsers([...users, res]);
      setIsUserModalOpen(false);
      setNewUser({ username: '', password: '', nombre: '', company_id: '', email: '', is_admin: false });
      toast({ title: "Usuario creado", description: "El usuario se creó correctamente." });
    } catch (e: any) {
      toast({ title: "Error", description: e.message || "No se pudo crear el usuario", variant: "destructive" });
    }
  };

  const handleSaveTiers = async () => {
    setSavingTiers(true);
    try {
      await updateBillingTiers(tiers);
      toast({ title: "Rangos actualizados", description: "La configuración de facturación ha sido guardada." });
      
      // Refrescar el simulador con los nuevos rangos
      const simRes = await getBillingSimulator();
      if (simRes && 'simulator' in simRes) {
        setSimulatorData(simRes.simulator);
      }
    } catch (e: any) {
      toast({ title: "Error", description: e.message || "No se pudieron guardar los rangos", variant: "destructive" });
    } finally {
      setSavingTiers(false);
    }
  };

  const handleSuspendCompany = async () => {
    if (!suspendCompanyId || !suspendReason) {
      toast({ title: "Error", description: "El motivo es obligatorio", variant: "destructive" });
      return;
    }
    try {
      await apiFetch(`/admin/companies/${suspendCompanyId}/suspend`, {
        method: 'POST',
        body: JSON.stringify({ reason: suspendReason, notes: suspendNotes })
      });
      toast({ title: "Empresa Suspendida", description: "La empresa ha sido suspendida exitosamente." });
      setSuspendModalOpen(false);
      fetchData();
    } catch (e: any) {
      toast({ title: "Error", description: e.message || "No se pudo suspender la empresa", variant: "destructive" });
    }
  };

  const handleReactivateCompany = async (companyId: number) => {
    try {
      await apiFetch(`/admin/companies/${companyId}/reactivate`, {
        method: 'POST',
        body: JSON.stringify({ notes: 'Reactivado desde panel Admin' })
      });
      toast({ title: "Empresa Reactivada", description: "La empresa ha sido reactivada." });
      fetchData();
    } catch (e: any) {
      toast({ title: "Error", description: e.message || "No se pudo reactivar la empresa", variant: "destructive" });
    }
  };

  const handleMarkOverdue = async (companyId: number) => {
    try {
      await apiFetch(`/admin/companies/${companyId}/mark-overdue`, { method: 'POST' });
      toast({ title: "Marcada en Mora", description: "El estado de pago ha cambiado a en mora." });
      fetchData();
    } catch (e: any) {
      toast({ title: "Error", description: e.message || "No se pudo cambiar el estado", variant: "destructive" });
    }
  };

  const addTier = () => {
    const lastTier = tiers[tiers.length - 1];
    const newMin = lastTier ? (lastTier.max_cases ? lastTier.max_cases + 1 : lastTier.min_cases + 100) : 0;
    setTiers([...tiers, { min_cases: newMin, max_cases: null, price: 0 }]);
  };

  const updateTier = (index: number, field: keyof BillingTier, value: any) => {
    const newTiers = [...tiers];
    if (field === 'max_cases' && value === '') value = null;
    else if (value !== null) value = Number(value);
    newTiers[index] = { ...newTiers[index], [field]: value };
    setTiers(newTiers);
  };

  const removeTier = (index: number) => {
    setTiers(tiers.filter((_, i) => i !== index));
  };

  if (!user?.is_admin || user?.company_id) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <ShieldAlert className="h-16 w-16 text-destructive mb-4" />
        <h2 className="text-2xl font-bold">Acceso Denegado</h2>
        <p className="text-muted-foreground mt-2">No tienes privilegios de SuperAdmin para ver esta página.</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6 animate-fade-in">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Panel SuperAdmin (SaaS)</h1>
          <p className="text-muted-foreground mt-1">
            Administra los inquilinos (empresas) y usuarios globales.
          </p>
        </div>
      </div>

      <Tabs defaultValue="empresas" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="empresas" className="flex items-center gap-2">
            <Building2 className="w-4 h-4" /> Empresas
          </TabsTrigger>
          <TabsTrigger value="usuarios" className="flex items-center gap-2">
            <Users className="w-4 h-4" /> Usuarios Globales
          </TabsTrigger>
          <TabsTrigger value="facturacion" className="flex items-center gap-2">
            <DollarSign className="w-4 h-4" /> Facturación
          </TabsTrigger>
        </TabsList>

        <TabsContent value="empresas">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Empresas Inquilinas</CardTitle>
                <CardDescription>Gestión de las cuentas de clientes</CardDescription>
              </div>
              <Button onClick={() => setIsCompanyModalOpen(true)} size="sm">
                <Plus className="w-4 h-4 mr-1" /> Nueva Empresa
              </Button>
            </CardHeader>
            <CardContent>
              {loading ? <div className="p-4 text-center">Cargando...</div> : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>Nombre</TableHead>
                      <TableHead>NIT</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead>Límite Usr.</TableHead>
                      <TableHead>Est. Pago</TableHead>
                      <TableHead>Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {companies.map(c => (
                      <TableRow key={c.id}>
                        <TableCell>{c.id}</TableCell>
                        <TableCell className="font-semibold">{c.nombre}</TableCell>
                        <TableCell>{c.nit || '—'}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${c.estado === 'activo' ? 'bg-emerald-100 text-emerald-800' : c.estado === 'suspendida_pago' ? 'bg-red-100 text-red-800' : c.estado === 'en_mora' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'}`}>
                            {c.estado.toUpperCase()}
                          </span>
                        </TableCell>
                        <TableCell>{c.limite_usuarios}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${c.payment_status === 'al_dia' ? 'bg-emerald-100 text-emerald-800' : c.payment_status === 'en_mora' ? 'bg-yellow-100 text-yellow-800' : c.payment_status === 'suspendido' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}`}>
                            {c.payment_status?.toUpperCase() || 'AL_DIA'}
                          </span>
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" className="h-8 w-8 p-0">
                                <span className="sr-only">Abrir menú</span>
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              {c.estado !== 'suspendida_pago' && (
                                <>
                                  <DropdownMenuItem onClick={() => {
                                    setSuspendCompanyId(c.id);
                                    setSuspendReason("");
                                    setSuspendNotes("");
                                    setSuspendModalOpen(true);
                                  }}>
                                    Suspender por falta de pago
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => handleMarkOverdue(c.id)}>
                                    Marcar en mora
                                  </DropdownMenuItem>
                                </>
                              )}
                              {c.estado === 'suspendida_pago' && (
                                <DropdownMenuItem onClick={() => handleReactivateCompany(c.id)}>
                                  Reactivar
                                </DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                    {companies.length === 0 && (
                      <TableRow><TableCell colSpan={7} className="text-center">No hay empresas registradas</TableCell></TableRow>
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="usuarios">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Usuarios del Sistema</CardTitle>
                <CardDescription>Todos los usuarios de todas las empresas</CardDescription>
              </div>
              <Button onClick={() => setIsUserModalOpen(true)} size="sm">
                <Plus className="w-4 h-4 mr-1" /> Nuevo Usuario
              </Button>
            </CardHeader>
            <CardContent>
              {loading ? <div className="p-4 text-center">Cargando...</div> : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>Username</TableHead>
                      <TableHead>Nombre</TableHead>
                      <TableHead>Empresa ID</TableHead>
                      <TableHead>Rol</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map(u => (
                      <TableRow key={u.id}>
                        <TableCell>{u.id}</TableCell>
                        <TableCell>{u.username}</TableCell>
                        <TableCell>{u.nombre}</TableCell>
                        <TableCell>{u.company_id || 'Global'}</TableCell>
                        <TableCell>
                          {u.is_admin && !u.company_id ? (
                            <span className="bg-purple-100 text-purple-800 px-2 py-0.5 rounded-full text-xs font-semibold">SuperAdmin</span>
                          ) : (
                            <span className="bg-slate-100 text-slate-800 px-2 py-0.5 rounded-full text-xs">Standard</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="facturacion">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Configurar Tarifas</CardTitle>
                  <CardDescription>Define los rangos de cobro por radicados activos</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {tiers.map((tier, idx) => (
                    <div key={idx} className="flex flex-col gap-2 p-3 bg-muted/30 rounded-lg border">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-semibold">Rango {idx + 1}</span>
                        <Button variant="ghost" size="sm" onClick={() => removeTier(idx)} className="h-6 w-6 p-0 text-red-500 hover:text-red-700">X</Button>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div className="space-y-1">
                          <Label className="text-xs">Mínimo</Label>
                          <Input type="number" value={tier.min_cases} onChange={(e) => updateTier(idx, 'min_cases', e.target.value)} className="h-8 text-sm" />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Máximo (vacío = ∞)</Label>
                          <Input type="number" value={tier.max_cases ?? ''} onChange={(e) => updateTier(idx, 'max_cases', e.target.value)} className="h-8 text-sm" />
                        </div>
                        <div className="col-span-2 space-y-1">
                          <Label className="text-xs">Tarifa Fija (COP)</Label>
                          <Input type="number" value={tier.price} onChange={(e) => updateTier(idx, 'price', e.target.value)} className="h-8 text-sm font-semibold text-emerald-600" />
                        </div>
                      </div>
                    </div>
                  ))}
                  <Button variant="outline" className="w-full border-dashed" onClick={addTier}>
                    <Plus className="w-4 h-4 mr-2" /> Agregar Rango
                  </Button>
                  <Button className="w-full mt-4 bg-emerald-600 hover:bg-emerald-500 text-white" onClick={handleSaveTiers} disabled={savingTiers}>
                    {savingTiers ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                    Guardar y Simular
                  </Button>
                </CardContent>
              </Card>
            </div>

            <div className="lg:col-span-2">
              <Card className="h-full">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>Simulador de Facturación</CardTitle>
                    <CardDescription>Impacto de los rangos actuales en las empresas registradas</CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={fetchData}>
                    <RefreshCw className="w-4 h-4 mr-2" /> Actualizar
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-slate-50">
                          <TableHead>Empresa</TableHead>
                          <TableHead className="text-center">Usuarios</TableHead>
                          <TableHead className="text-center">Rad. Activos</TableHead>
                          <TableHead>Rango Aplicado</TableHead>
                          <TableHead className="text-right">A Cobrar</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {simulatorData.map((d, i) => (
                          <TableRow key={i}>
                            <TableCell className="font-medium">{d.company_name}</TableCell>
                            <TableCell className="text-center">{d.users_count}</TableCell>
                            <TableCell className="text-center font-bold">{d.active_cases}</TableCell>
                            <TableCell className="text-xs text-muted-foreground">{d.applicable_tier}</TableCell>
                            <TableCell className="text-right font-bold text-emerald-600">
                              ${d.total_cost.toLocaleString('es-CO')}
                            </TableCell>
                          </TableRow>
                        ))}
                        {simulatorData.length === 0 && (
                          <TableRow><TableCell colSpan={5} className="text-center py-8">No hay datos para simular</TableCell></TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Modal Crear Empresa */}
      <Dialog open={isCompanyModalOpen} onOpenChange={setIsCompanyModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nueva Empresa</DialogTitle>
            <DialogDescription>Crea un nuevo inquilino para el modelo SaaS.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>Nombre</Label>
              <Input value={newCompany.nombre} onChange={e => setNewCompany({...newCompany, nombre: e.target.value})} />
            </div>
            <div>
              <Label>NIT</Label>
              <Input value={newCompany.nit} onChange={e => setNewCompany({...newCompany, nit: e.target.value})} />
            </div>
            <div>
              <Label>Límite Usuarios</Label>
              <Input type="number" value={newCompany.limite_usuarios} onChange={e => setNewCompany({...newCompany, limite_usuarios: parseInt(e.target.value)})} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCompanyModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleCreateCompany} disabled={!newCompany.nombre}>Crear Empresa</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Crear Usuario */}
      <Dialog open={isUserModalOpen} onOpenChange={setIsUserModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nuevo Usuario</DialogTitle>
            <DialogDescription>Crea un usuario y asígnalo a una empresa.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>Username</Label>
              <Input value={newUser.username} onChange={e => setNewUser({...newUser, username: e.target.value})} />
            </div>
            <div>
              <Label>Contraseña</Label>
              <Input type="password" value={newUser.password} onChange={e => setNewUser({...newUser, password: e.target.value})} />
            </div>
            <div>
              <Label>Nombre Completo</Label>
              <Input value={newUser.nombre} onChange={e => setNewUser({...newUser, nombre: e.target.value})} />
            </div>
            <div>
              <Label>Empresa ID</Label>
              <Input type="number" placeholder="ID de la empresa (Ej: 1)" value={newUser.company_id} onChange={e => setNewUser({...newUser, company_id: e.target.value})} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsUserModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleCreateUser} disabled={!newUser.username || !newUser.password || !newUser.company_id}>Crear Usuario</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Suspender Empresa */}
      <Dialog open={suspendModalOpen} onOpenChange={setSuspendModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-destructive">Suspender Empresa</DialogTitle>
            <DialogDescription>
              Esta acción bloqueará el acceso de todos los usuarios de esta empresa, pero no eliminará sus datos.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>Motivo de suspensión <span className="text-destructive">*</span></Label>
              <Input 
                value={suspendReason} 
                onChange={e => setSuspendReason(e.target.value)} 
                placeholder="Ej. Falta de pago" 
              />
            </div>
            <div>
              <Label>Observación interna</Label>
              <Textarea 
                value={suspendNotes} 
                onChange={e => setSuspendNotes(e.target.value)} 
                placeholder="Detalles adicionales para uso interno..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSuspendModalOpen(false)}>Cancelar</Button>
            <Button variant="destructive" onClick={handleSuspendCompany} disabled={!suspendReason}>Confirmar Suspensión</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
