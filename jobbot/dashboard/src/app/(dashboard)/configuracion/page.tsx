'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Settings, 
  MessageCircle, 
  CreditCard, 
  FileText, 
  Trash2, 
  AlertTriangle,
  ExternalLink,
  Check,
  X,
  Zap,
  Shield
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { cn } from '@/components/ui/button';
import Link from 'next/link';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  },
};

const integrations = [
  {
    id: 'telegram',
    name: 'Telegram Bot',
    description: 'Recibe notificaciones instantáneas y controla JobBot desde Telegram',
    icon: MessageCircle,
    connected: true,
    status: 'active',
    color: 'bg-blue-500',
  },
  {
    id: 'linkedin',
    name: 'LinkedIn',
    description: 'Sincroniza tu perfil y aplica automáticamente a ofertas',
    icon: Zap,
    connected: false,
    status: 'coming_soon',
    color: 'bg-blue-700',
  },
  {
    id: 'github',
    name: 'GitHub',
    description: 'Importa tus repositorios para mejorar tu perfil',
    icon: Shield,
    connected: false,
    status: 'coming_soon',
    color: 'bg-slate-800',
  },
];

const invoices = [
  { id: 'inv_001', date: '2024-01-15', amount: 0, status: 'paid', plan: 'Free' },
  { id: 'inv_002', date: '2023-12-15', amount: 0, status: 'paid', plan: 'Free' },
];

export default function ConfiguracionPage() {
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDeleteAccount = async () => {
    if (deleteConfirm !== 'ELIMINAR') return;
    setIsDeleting(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    localStorage.removeItem('token');
    window.location.href = '/';
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6 max-w-4xl"
    >
      <motion.div variants={itemVariants}>
        <h1 className="text-2xl font-bold tracking-tight">Configuración</h1>
        <p className="text-muted-foreground">Gestiona integraciones, facturación y cuenta</p>
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              Integraciones
            </CardTitle>
            <CardDescription>Conecta JobBot con otras plataformas</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {integrations.map((integration) => (
                <div
                  key={integration.id}
                  className="flex items-start justify-between p-4 rounded-lg border bg-card"
                >
                  <div className="flex items-start gap-4">
                    <div className={cn('h-10 w-10 rounded-lg flex items-center justify-center', integration.color)}>
                      <integration.icon className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium">{integration.name}</h3>
                        {integration.status === 'active' ? (
                          <Badge variant="success" className="text-xs">Activo</Badge>
                        ) : (
                          <Badge variant="secondary" className="text-xs">Próximamente</Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{integration.description}</p>
                    </div>
                  </div>
                  <Button 
                    variant={integration.connected ? 'outline' : 'default'} 
                    size="sm"
                    disabled={integration.status === 'coming_soon'}
                  >
                    {integration.connected ? 'Configurar' : 'Conectar'}
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-primary" />
              Plan de Suscripción
            </CardTitle>
            <CardDescription>Tu plan actual y opciones de actualización</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30 border border-amber-200 dark:border-amber-800">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Zap className="h-4 w-4 text-amber-600" />
                  <span className="font-semibold">Plan Free</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  3 alertas/semana • 5 búsquedas/día • 2 análisis CV/mes
                </p>
              </div>
              <Button asChild>
                <Link href="/dashboard/suscripcion">
                  Ver planes
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Historial de Facturación
            </CardTitle>
            <CardDescription>Facturas y pagos de tu cuenta</CardDescription>
          </CardHeader>
          <CardContent>
            {invoices.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                No hay facturas para mostrar
              </p>
            ) : (
              <div className="space-y-2">
                {invoices.map((invoice) => (
                  <div
                    key={invoice.id}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent/50 transition-colors"
                  >
                    <div>
                      <p className="font-medium">{invoice.id.toUpperCase()}</p>
                      <p className="text-sm text-muted-foreground">
                        {new Date(invoice.date).toLocaleDateString('es-ES', {
                          day: 'numeric',
                          month: 'long',
                          year: 'numeric'
                        })} • {invoice.plan}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={invoice.status === 'paid' ? 'success' : 'secondary'}>
                        {invoice.status === 'paid' ? 'Pagado' : 'Pendiente'}
                      </Badge>
                      <span className="font-medium">${invoice.amount}</span>
                      <Button variant="ghost" size="sm">
                        <FileText className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card className="border-destructive/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <Trash2 className="h-5 w-5" />
              Zona de Peligro
            </CardTitle>
            <CardDescription>Acciones irreversibles para tu cuenta</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start justify-between p-4 rounded-lg border border-destructive/20 bg-destructive/5">
                <div>
                  <h3 className="font-medium text-destructive">Eliminar cuenta</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    Esto eliminará permanentemente tu cuenta y todos tus datos. Esta acción no se puede deshacer.
                  </p>
                </div>
                <Button 
                  variant="destructive" 
                  size="sm"
                  onClick={() => setIsDeleteModalOpen(true)}
                >
                  Eliminar cuenta
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <Dialog open={isDeleteModalOpen} onOpenChange={setIsDeleteModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              ¿Estás seguro?
            </DialogTitle>
            <DialogDescription>
              Esta acción eliminará permanentemente tu cuenta y todos tus datos incluyendo:
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4 space-y-2 text-sm">
            <div className="flex items-center gap-2 text-muted-foreground">
              <X className="h-4 w-4 text-destructive" />
              Todas tus postulaciones y seguimiento
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <X className="h-4 w-4 text-destructive" />
              Configuraciones de búsqueda y keywords
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <X className="h-4 w-4 text-destructive" />
              Historial de suscripción y facturación
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <X className="h-4 w-4 text-destructive" />
              Tu CV y documentos subidos
            </div>
          </div>
          <div className="mt-6">
            <p className="text-sm font-medium mb-2">
              Escribe <code className="bg-muted px-1 py-0.5 rounded">ELIMINAR</code> para confirmar:
            </p>
            <input
              type="text"
              value={deleteConfirm}
              onChange={(e) => setDeleteConfirm(e.target.value)}
              className="w-full px-3 py-2 rounded-md border border-input bg-background"
              placeholder="ELIMINAR"
            />
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="outline" onClick={() => setIsDeleteModalOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteAccount}
              disabled={deleteConfirm !== 'ELIMINAR' || isDeleting}
              isLoading={isDeleting}
            >
              Sí, eliminar mi cuenta
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
