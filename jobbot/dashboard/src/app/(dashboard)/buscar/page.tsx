'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Search, 
  Filter,
  MapPin,
  Briefcase,
  ExternalLink,
  Bookmark,
  Sparkles,
  SlidersHorizontal,
  Clock
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select } from '@/components/ui/select';
import { cn } from '@/components/ui/button';

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

const mockJobs = [
  {
    id: '1',
    title: 'Senior Python Developer',
    company: 'TechCorp',
    location: 'Remote',
    modality: 'remote',
    salary: '$80k - $120k',
    description: 'Buscamos un desarrollador Python senior con experiencia en Django y FastAPI...',
    skills: ['Python', 'Django', 'FastAPI', 'PostgreSQL'],
    postedAt: '2024-01-15',
    source: 'LinkedIn',
  },
  {
    id: '2',
    title: 'Full Stack Engineer',
    company: 'StartupXYZ',
    location: 'Buenos Aires',
    modality: 'hybrid',
    salary: '$40k - $60k',
    description: 'Startup en crecimiento busca Full Stack con React y Node.js...',
    skills: ['React', 'Node.js', 'MongoDB', 'TypeScript'],
    postedAt: '2024-01-14',
    source: 'Indeed',
  },
  {
    id: '3',
    title: 'Backend Developer',
    company: 'DevStudio',
    location: 'CABA',
    modality: 'onsite',
    salary: '$35k - $50k',
    description: 'Desarrollo de APIs REST y microservicios con Node.js...',
    skills: ['Node.js', 'Express', 'Redis', 'Docker'],
    postedAt: '2024-01-13',
    source: 'GetOnBoard',
  },
  {
    id: '4',
    title: 'Software Architect',
    company: 'Enterprise Solutions',
    location: 'Remote',
    modality: 'remote',
    salary: '$100k - $150k',
    description: 'Diseño de arquitectura de sistemas distribuidos...',
    skills: ['Architecture', 'AWS', 'Kubernetes', 'Microservices'],
    postedAt: '2024-01-12',
    source: 'LinkedIn',
  },
  {
    id: '5',
    title: 'React Developer',
    company: 'Digital Agency',
    location: 'Remote',
    modality: 'remote',
    salary: '$50k - $75k',
    description: 'Desarrollo frontend con React, Next.js y TypeScript...',
    skills: ['React', 'Next.js', 'TypeScript', 'Tailwind'],
    postedAt: '2024-01-11',
    source: 'Indeed',
  },
];

const getModalityLabel = (modality: string) => {
  const labels = { remote: 'Remoto', hybrid: 'Híbrido', onsite: 'Presencial' };
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

export default function BuscarPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [modalityFilter, setModalityFilter] = useState('');
  const [savedJobs, setSavedJobs] = useState<string[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const filteredJobs = mockJobs.filter(job => {
    const matchesSearch = 
      job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.skills.some(skill => skill.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesModality = !modalityFilter || job.modality === modalityFilter;
    return matchesSearch && matchesModality;
  });

  const handleSearch = () => {
    setIsSearching(true);
    setTimeout(() => setIsSearching(false), 500);
  };

  const toggleSaveJob = (jobId: string) => {
    setSavedJobs(prev => 
      prev.includes(jobId) 
        ? prev.filter(id => id !== jobId)
        : [...prev, jobId]
    );
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <motion.div variants={itemVariants}>
        <h1 className="text-2xl font-bold tracking-tight">Buscar Empleos</h1>
        <p className="text-muted-foreground">Encuentra y aplica a nuevas oportunidades</p>
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar por título, empresa o skill..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  className="pl-10"
                />
              </div>
              <div className="flex gap-2">
                <Select
                  value={modalityFilter}
                  onChange={(e) => setModalityFilter(e.target.value)}
                  className="w-[140px]"
                >
                  <option value="">Todas</option>
                  <option value="remote">Remoto</option>
                  <option value="hybrid">Híbrido</option>
                  <option value="onsite">Presencial</option>
                </Select>
                <Button onClick={handleSearch} isLoading={isSearching}>
                  <Search className="mr-2 h-4 w-4" />
                  Buscar
                </Button>
              </div>
            </div>
            
            <div className="flex flex-wrap items-center gap-2 mt-4 pt-4 border-t">
              <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Filtros rápidos:</span>
              {['Python', 'React', 'Remote', 'Senior'].map(filter => (
                <button
                  key={filter}
                  onClick={() => setSearchQuery(filter)}
                  className="px-2.5 py-1 rounded-full text-xs bg-secondary hover:bg-secondary/80 transition-colors"
                >
                  {filter}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={itemVariants}>
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-muted-foreground">
            {filteredJobs.length} {filteredJobs.length === 1 ? 'resultado' : 'resultados'} encontrados
          </p>
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-sm">JobBot está buscando automáticamente por ti</span>
          </div>
        </div>

        {filteredJobs.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Briefcase className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
              <h3 className="font-medium text-lg">No se encontraron jobs</h3>
              <p className="text-muted-foreground mt-1">
                Intenta con otros términos de búsqueda o filtros
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredJobs.map((job) => (
              <Card 
                key={job.id} 
                className="group hover:shadow-md transition-all duration-200"
              >
                <CardContent className="p-6">
                  <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-start gap-3 mb-2">
                        <h3 className="font-semibold text-lg group-hover:text-primary transition-colors">
                          {job.title}
                        </h3>
                        {job.salary && (
                          <Badge variant="success" className="shrink-0">
                            {job.salary}
                          </Badge>
                        )}
                      </div>
                      
                      <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mb-3">
                        <span className="flex items-center gap-1">
                          <Briefcase className="h-4 w-4" />
                          {job.company}
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin className="h-4 w-4" />
                          {job.location}
                        </span>
                        <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', getModalityColor(job.modality))}>
                          {getModalityLabel(job.modality)}
                        </span>
                      </div>

                      <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                        {job.description}
                      </p>

                      <div className="flex flex-wrap gap-2">
                        {job.skills.map(skill => (
                          <span 
                            key={skill}
                            className="px-2 py-1 rounded-md text-xs bg-secondary text-secondary-foreground"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="flex lg:flex-col items-center lg:items-end gap-2 shrink-0">
                      <div className="flex items-center gap-2 lg:mb-2">
                        <button
                          onClick={() => toggleSaveJob(job.id)}
                          className={cn(
                            'p-2 rounded-md transition-colors',
                            savedJobs.includes(job.id)
                              ? 'text-primary bg-primary/10'
                              : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                          )}
                          title={savedJobs.includes(job.id) ? 'Guardado' : 'Guardar'}
                        >
                          <Bookmark className={cn('h-4 w-4', savedJobs.includes(job.id) && 'fill-current')} />
                        </button>
                        <a
                          href="#"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
                          title="Ver oferta"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </div>
                      <Button size="sm">
                        Aplicar ahora
                      </Button>
                      <p className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {job.source} • {new Date(job.postedAt).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
