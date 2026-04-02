'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { 
  Search, 
  Plus, 
  Filter,
  MoreHorizontal,
  ExternalLink,
  Trash2,
  Edit3,
  Calendar,
  Building2,
  MapPin,
  Briefcase
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { cn } from '@/components/ui/button';
import type { Job, JobStatus } from '@/types';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: [0.22, 1, 0.36, 1] },
  },
};

const mockJobs: Job[] = [
  { 
    id: '1', title: 'Senior Python Developer', company: 'TechCorp', location: 'Remote', 
    modality: 'remote', status: 'interview', appliedAt: '2024-01-15', url: '#', 
    createdAt: '2024-01-15', updatedAt: '2024-01-15', salary: '$80k - $120k'
  },
  { 
    id: '2', title: 'Full Stack Engineer', company: 'StartupXYZ', location: 'Buenos Aires', 
    modality: 'hybrid', status: 'applied', appliedAt: '2024-01-14', url: '#', 
    createdAt: '2024-01-14', updatedAt: '2024-01-14', salary: '$40k - $60k'
  },
  { 
    id: '3', title: 'Backend Developer', company: 'DevStudio', location: 'CABA', 
    modality: 'onsite', status: 'rejected', appliedAt: '2024-01-10', url: '#', 
    createdAt: '2024-01-10', updatedAt: '2024-01-11'
  },
  { 
    id: '4', title: 'Software Architect', company: 'Enterprise Solutions', location: 'Remote', 
    modality: 'remote', status: 'offer', appliedAt: '2024-01-08', url: '#', 
    createdAt: '2024-01-08', updatedAt: '2024-01-09', salary: '$100k - $150k'
  },
  { 
    id: '5', title: 'React Developer', company: 'Digital Agency', location: 'Remote', 
    modality: 'remote', status: 'saved', appliedAt: '', url: '#', 
    createdAt: '2024-01-05', updatedAt: '2024-01-05'
  },
  { 
    id: '6', title: 'DevOps Engineer', company: 'CloudTech', location: 'Mendoza', 
    modality: 'hybrid', status: 'applied', appliedAt: '2024-01-03', url: '#', 
    createdAt: '2024-01-03', updatedAt: '2024-01-03'
  },
];

const statusOptions = [
  { value: '', label: 'Todos los estados' },
  { value: 'applied', label: 'Aplicado' },
  { value: 'interview', label: 'Entrevista' },
  { value: 'offer', label: 'Oferta' },
  { value: 'rejected', label: 'Rechazado' },
  { value: 'saved', label: 'Guardado' },
];

const getStatusConfig = (status: JobStatus) => {
  const configs = {
    applied: { 
      badge: 'secondary' as const, 
      label: 'Aplicado',
      color: 'bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400'
    },
    interview: { 
      badge: 'warning' as const, 
      label: 'Entrevista',
      color: 'bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400'
    },
    offer: { 
      badge: 'success' as const, 
      label: 'Oferta',
      color: 'bg-green-100 text-green-700 dark:bg-green-950/50 dark:text-green-400'
    },
    rejected: { 
      badge: 'destructive' as const, 
      label: 'Rechazado',
      color: 'bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-400'
    },
    saved: { 
      badge: 'outline' as const, 
      label: 'Guardado',
      color: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400'
    },
  };
  return configs[status] || configs.applied;
};

const getModalityLabel = (modality: string) => {
  const labels = { remote: 'Remoto', hybrid: 'Híbrido', onsite: 'Presencial' };
  return labels[modality as keyof typeof labels] || modality;
};

export default function PostulacionesPage() {
  const [jobs, setJobs] = useState<Job[]>(mockJobs);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  const [newJob, setNewJob] = useState({
    title: '',
    company: '',
    location: '',
    modality: 'remote' as const,
    status: 'applied' as JobStatus,
    url: '',
    salary: '',
  });

  const filteredJobs = useMemo(() => {
    return jobs.filter(job => {
      const matchesSearch = 
        job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        job.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
        job.location.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = !statusFilter || job.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [jobs, searchQuery, statusFilter]);

  const paginatedJobs = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredJobs.slice(start, start + itemsPerPage);
  }, [filteredJobs, currentPage]);

  const totalPages = Math.ceil(filteredJobs.length / itemsPerPage);

  const handleAddJob = (e: React.FormEvent) => {
    e.preventDefault();
    const job: Job = {
      ...newJob,
      id: Date.now().toString(),
      appliedAt: newJob.status === 'applied' ? new Date().toISOString() : '',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setJobs([job, ...jobs]);
    setIsAddModalOpen(false);
    setNewJob({
      title: '', company: '', location: '', modality: 'remote', 
      status: 'applied', url: '', salary: ''
    });
  };

  const handleDeleteJob = (id: string) => {
    setJobs(jobs.filter(j => j.id !== id));
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <motion.div variants={itemVariants} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Mis Postulaciones</h1>
          <p className="text-muted-foreground">Gestiona tus aplicaciones y seguimiento</p>
        </div>
        <Button onClick={() => setIsAddModalOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Agregar job
        </Button>
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader className="pb-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar por título, empresa o ubicación..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-[180px]"
                >
                  {statusOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {filteredJobs.length === 0 ? (
              <div className="text-center py-12">
                <Briefcase className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
                <p className="text-muted-foreground">No se encontraron postulaciones</p>
                <Button variant="outline" className="mt-4" onClick={() => setIsAddModalOpen(true)}>
                  Agregar tu primera postulación
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {paginatedJobs.map((job) => {
                  const statusConfig = getStatusConfig(job.status);
                  return (
                    <div
                      key={job.id}
                      className="flex flex-col lg:flex-row lg:items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/30 transition-all duration-200 group"
                    >
                      <div className="flex-1 min-w-0 space-y-2 lg:space-y-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-medium text-foreground group-hover:text-primary transition-colors">
                            {job.title}
                          </h3>
                          <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', statusConfig.color)}>
                            {statusConfig.label}
                          </span>
                        </div>
                        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Building2 className="h-3.5 w-3.5" />
                            {job.company}
                          </span>
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3.5 w-3.5" />
                            {job.location}
                          </span>
                          <span className="flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/50" />
                            {getModalityLabel(job.modality)}
                          </span>
                          {job.salary && (
                            <span className="text-green-600 font-medium">{job.salary}</span>
                          )}
                        </div>
                        {job.appliedAt && (
                          <p className="text-xs text-muted-foreground">
                            Aplicado el {new Date(job.appliedAt).toLocaleDateString('es-ES', {
                              day: 'numeric', month: 'long', year: 'numeric'
                            })}
                          </p>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-2 mt-4 lg:mt-0 pt-4 lg:pt-0 border-t lg:border-t-0">
                        <a
                          href={job.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={cn(
                            'p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent',
                            'transition-colors'
                          )}
                          title="Ver oferta"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                        <button
                          className={cn(
                            'p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent',
                            'transition-colors'
                          )}
                          title="Editar"
                        >
                          <Edit3 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteJob(job.id)}
                          className={cn(
                            'p-2 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10',
                            'transition-colors'
                          )}
                          title="Eliminar"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-4 border-t">
                <p className="text-sm text-muted-foreground">
                  Mostrando {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, filteredJobs.length)} de {filteredJobs.length}
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                  >
                    Anterior
                  </Button>
                  <span className="text-sm text-muted-foreground px-2">
                    {currentPage} / {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                  >
                    Siguiente
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      <Dialog open={isAddModalOpen} onOpenChange={setIsAddModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Agregar nueva postulación</DialogTitle>
            <DialogDescription>
              Registra manualmente una aplicación a un job
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddJob} className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="title">Título del puesto</Label>
                <Input
                  id="title"
                  value={newJob.title}
                  onChange={(e) => setNewJob({ ...newJob, title: e.target.value })}
                  placeholder="Senior Developer"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company">Empresa</Label>
                <Input
                  id="company"
                  value={newJob.company}
                  onChange={(e) => setNewJob({ ...newJob, company: e.target.value })}
                  placeholder="TechCorp"
                  required
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="location">Ubicación</Label>
                <Input
                  id="location"
                  value={newJob.location}
                  onChange={(e) => setNewJob({ ...newJob, location: e.target.value })}
                  placeholder="Remote"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="modality">Modalidad</Label>
                <Select
                  id="modality"
                  value={newJob.modality}
                  onChange={(e) => setNewJob({ ...newJob, modality: e.target.value as any })}
                >
                  <option value="remote">Remoto</option>
                  <option value="hybrid">Híbrido</option>
                  <option value="onsite">Presencial</option>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="status">Estado</Label>
                <Select
                  id="status"
                  value={newJob.status}
                  onChange={(e) => setNewJob({ ...newJob, status: e.target.value as JobStatus })}
                >
                  <option value="applied">Aplicado</option>
                  <option value="interview">Entrevista</option>
                  <option value="offer">Oferta</option>
                  <option value="rejected">Rechazado</option>
                  <option value="saved">Guardado</option>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="salary">Salario (opcional)</Label>
                <Input
                  id="salary"
                  value={newJob.salary}
                  onChange={(e) => setNewJob({ ...newJob, salary: e.target.value })}
                  placeholder="$50k - $80k"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="url">URL de la oferta</Label>
              <Input
                id="url"
                type="url"
                value={newJob.url}
                onChange={(e) => setNewJob({ ...newJob, url: e.target.value })}
                placeholder="https://..."
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsAddModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit">Guardar postulación</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
