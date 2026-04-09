'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Search, 
  FileText, 
  TrendingUp, 
  Bell, 
  Briefcase,
  Clock,
  CheckCircle2,
  XCircle,
  Plus
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/components/ui/button';
import Link from 'next/link';
import type { JobStats } from '@/types';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.22, 1, 0.36, 1],
    },
  },
};

const statsData = [
  { 
    title: 'Jobs Aplicados', 
    value: '12', 
    change: '+3 esta semana', 
    icon: FileText, 
    trend: 'up',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 dark:bg-blue-950/30',
  },
  { 
    title: 'Entrevistas', 
    value: '4', 
    change: '2 próximas', 
    icon: Clock, 
    trend: 'up',
    color: 'text-amber-600',
    bgColor: 'bg-amber-50 dark:bg-amber-950/30',
  },
  { 
    title: 'Tasa de Respuesta', 
    value: '33%', 
    change: '+5% vs mes anterior', 
    icon: TrendingUp, 
    trend: 'up',
    color: 'text-green-600',
    bgColor: 'bg-green-50 dark:bg-green-950/30',
  },
  { 
    title: 'Alertas Activas', 
    value: '3', 
    change: 'Buscando automáticamente', 
    icon: Bell, 
    trend: 'neutral',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 dark:bg-purple-950/30',
  },
];

const recentJobs = [
  { 
    id: '1',
    title: 'Senior Python Developer', 
    company: 'TechCorp', 
    location: 'Remote', 
    modality: 'remote' as const, 
    status: 'interview' as const,
    appliedAt: '2024-01-15',
  },
  { 
    id: '2',
    title: 'Full Stack Engineer', 
    company: 'StartupXYZ', 
    location: 'Buenos Aires', 
    modality: 'hybrid' as const, 
    status: 'applied' as const,
    appliedAt: '2024-01-14',
  },
  { 
    id: '3',
    title: 'Backend Developer', 
    company: 'DevStudio', 
    location: 'CABA', 
    modality: 'onsite' as const, 
    status: 'rejected' as const,
    appliedAt: '2024-01-10',
  },
  { 
    id: '4',
    title: 'Software Architect', 
    company: 'Enterprise Solutions', 
    location: 'Remote', 
    modality: 'remote' as const, 
    status: 'offer' as const,
    appliedAt: '2024-01-08',
  },
];

const getStatusBadge = (status: string) => {
  const variants = {
    applied: { variant: 'secondary' as const, label: 'Aplicado', icon: FileText },
    interview: { variant: 'warning' as const, label: 'Entrevista', icon: Clock },
    offer: { variant: 'success' as const, label: 'Oferta', icon: CheckCircle2 },
    rejected: { variant: 'destructive' as const, label: 'Rechazado', icon: XCircle },
    saved: { variant: 'outline' as const, label: 'Guardado', icon: Briefcase },
  };
  return variants[status as keyof typeof variants] || variants.applied;
};

const getModalityLabel = (modality: string) => {
  const labels = {
    remote: 'Remoto',
    hybrid: 'Híbrido',
    onsite: 'Presencial',
  };
  return labels[modality as keyof typeof labels] || modality;
};

const getModalityColor = (modality: string) => {
  const colors = {
    remote: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400',
    hybrid: 'bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400',
    onsite: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400',
  };
  return colors[modality as keyof typeof colors] || colors.onsite;
};

export default function DashboardPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-muted animate-pulse rounded-xl" />
          ))}
        </div>
        <div className="h-96 bg-muted animate-pulse rounded-xl" />
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <motion.div variants={itemVariants} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">¡Bienvenido de nuevo!</h1>
          <p className="text-muted-foreground">Aquí está el resumen de tu búsqueda de empleo</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href="/dashboard/buscar">
              <Search className="mr-2 h-4 w-4" />
              Buscar jobs
            </Link>
          </Button>
          <Button asChild>
            <Link href="/dashboard/postulaciones">
              <Plus className="mr-2 h-4 w-4" />
              Nueva postulación
            </Link>
          </Button>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsData.map((stat, index) => (
          <motion.div key={stat.title} variants={itemVariants}>
            <Card className="hover:shadow-md transition-shadow duration-200">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">{stat.title}</p>
                    <p className="text-3xl font-bold tracking-tight">{stat.value}</p>
                    <p className={cn(
                      'text-sm',
                      stat.trend === 'up' ? 'text-green-600' : 
                      stat.trend === 'down' ? 'text-red-600' : 'text-muted-foreground'
                    )}>
                      {stat.change}
                    </p>
                  </div>
                  <div className={cn('h-12 w-12 rounded-xl flex items-center justify-center', stat.bgColor)}>
                    <stat.icon className={cn('h-6 w-6', stat.color)} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Postulaciones recientes</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Tus últimas aplicaciones y su estado
              </p>
            </div>
            <Button variant="ghost" asChild>
              <Link href="/dashboard/postulaciones">Ver todas</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentJobs.map((job) => {
                const statusBadge = getStatusBadge(job.status);
                return (
                  <div
                    key={job.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors cursor-pointer group"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <h3 className="font-medium text-foreground group-hover:text-primary transition-colors truncate">
                          {job.title}
                        </h3>
                        <Badge variant={statusBadge.variant} className="shrink-0">
                          <statusBadge.icon className="h-3 w-3 mr-1" />
                          {statusBadge.label}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        {job.company} • {job.location}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 mt-3 sm:mt-0">
                      <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-medium', getModalityColor(job.modality))}>
                        {getModalityLabel(job.modality)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(job.appliedAt).toLocaleDateString('es-ES', { 
                          day: 'numeric', 
                          month: 'short' 
                        })}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-gradient-to-br from-primary/5 to-purple-500/5 border-primary/20">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                <Briefcase className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold">Conecta tu búsqueda</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Configura alertas automáticas para recibir notificaciones de nuevos jobs que coincidan con tu perfil.
                </p>
                <Button variant="outline" size="sm" className="mt-4" asChild>
                  <Link href="/dashboard/configuracion">Configurar alertas</Link>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-500/5 to-orange-500/5 border-amber-500/20">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="h-10 w-10 rounded-lg bg-amber-500/10 flex items-center justify-center shrink-0">
                <TrendingUp className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <h3 className="font-semibold">Mejora tus resultados</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Actualiza a Premium para aplicaciones automáticas, análisis de CV ilimitados y más.
                </p>
                <Button variant="outline" size="sm" className="mt-4" asChild>
                  <Link href="/dashboard/suscripcion">Ver planes</Link>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
