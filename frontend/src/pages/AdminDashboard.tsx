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
import { apiFetch } from '@/services/api';

export default function AdminDashboard() {
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [companies, setCompanies] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isCompanyModalOpen, setIsCompanyModalOpen] = useState(false);
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);

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
      const [compRes, usrRes] = await Promise.all([
        apiFetch<any[]>('/admin/companies'),
        apiFetch<any[]>('/admin/users')
      ]);
      setCompanies(compRes || []);
      setUsers(usrRes || []);
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
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {companies.map(c => (
                      <TableRow key={c.id}>
                        <TableCell>{c.id}</TableCell>
                        <TableCell className="font-semibold">{c.nombre}</TableCell>
                        <TableCell>{c.nit || '—'}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${c.estado === 'activo' ? 'bg-emerald-100 text-emerald-800' : 'bg-destructive/10 text-destructive'}`}>
                            {c.estado.toUpperCase()}
                          </span>
                        </TableCell>
                        <TableCell>{c.limite_usuarios}</TableCell>
                      </TableRow>
                    ))}
                    {companies.length === 0 && (
                      <TableRow><TableCell colSpan={5} className="text-center">No hay empresas registradas</TableCell></TableRow>
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
    </div>
  );
}
