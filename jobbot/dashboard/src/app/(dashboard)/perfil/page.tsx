'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Briefcase,
  Bell,
  Upload,
  FileText,
  Save,
  CheckCircle2
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/components/ui/button';

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

const keywordsList = [
  'Python', 'React', 'Node.js', 'TypeScript', 'AWS', 'Docker', 
  'Kubernetes', 'PostgreSQL', 'MongoDB', 'GraphQL', 'Next.js'
];

export default function PerfilPage() {
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [selectedKeywords, setSelectedKeywords] = useState<string[]>(['Python', 'React']);
  const [customKeyword, setCustomKeyword] = useState('');

  const [profile, setProfile] = useState({
    name: 'Usuario Demo',
    email: 'usuario@email.com',
    phone: '+54 11 1234-5678',
    location: 'Buenos Aires, Argentina',
    telegramId: '123456789',
    preferences: {
      searchKeywords: [] as string[],
      preferredLocation: 'Buenos Aires',
      modality: 'remote' as const,
      notifications: {
        email: true,
        telegram: true,
        browser: false,
        newJobs: true,
        interviewReminders: true,
        weeklyDigest: false,
      },
    },
  });

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsSaving(false);
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  const toggleKeyword = (keyword: string) => {
    setSelectedKeywords(prev => 
      prev.includes(keyword) 
        ? prev.filter(k => k !== keyword)
        : [...prev, keyword]
    );
  };

  const addCustomKeyword = () => {
    if (customKeyword && !selectedKeywords.includes(customKeyword)) {
      setSelectedKeywords([...selectedKeywords, customKeyword]);
      setCustomKeyword('');
    }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6 max-w-4xl"
    >
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Mi Perfil</h1>
          <p className="text-muted-foreground">Gestiona tu información y preferencias de búsqueda</p>
        </div>
        <Button 
          onClick={handleSave} 
          isLoading={isSaving}
          className={cn(isSaved && 'bg-success hover:bg-success/90')}
        >
          {isSaved ? (
            <>
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Guardado
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Guardar cambios
            </>
          )}
        </Button>
      </motion.div>

      <div className="grid gap-6 md:grid-cols-2">
        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5 text-primary" />
                Información Personal
              </CardTitle>
              <CardDescription>Datos básicos de tu cuenta</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nombre completo</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="name"
                    value={profile.name}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    className="pl-10"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                    className="pl-10"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="phone">Teléfono</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="phone"
                    value={profile.phone}
                    onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                    className="pl-10"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="telegram">ID de Telegram</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">@</span>
                  <Input
                    id="telegram"
                    value={profile.telegramId}
                    onChange={(e) => setProfile({ ...profile, telegramId: e.target.value })}
                    className="pl-8"
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Necesario para recibir notificaciones por Telegram
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-5 w-5 text-primary" />
                Ubicación y Modalidad
              </CardTitle>
              <CardDescription>Preferencias de trabajo</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="location">Ubicación preferida</Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="location"
                    value={profile.preferences.preferredLocation}
                    onChange={(e) => setProfile({
                      ...profile,
                      preferences: { ...profile.preferences, preferredLocation: e.target.value }
                    })}
                    className="pl-10"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="modality">Modalidad preferida</Label>
                <Select
                  id="modality"
                  value={profile.preferences.modality}
                  onChange={(e) => setProfile({
                    ...profile,
                    preferences: { ...profile.preferences, modality: e.target.value as any }
                  })}
                >
                  <option value="remote">Remoto</option>
                  <option value="hybrid">Híbrido</option>
                  <option value="onsite">Presencial</option>
                  <option value="any">Cualquiera</option>
                </Select>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants} className="md:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="h-5 w-5 text-primary" />
                Keywords de Búsqueda
              </CardTitle>
              <CardDescription>
                Selecciona las tecnologías y skills que quieres que busque JobBot automáticamente
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2 mb-4">
                {keywordsList.map((keyword) => (
                  <button
                    key={keyword}
                    onClick={() => toggleKeyword(keyword)}
                    className={cn(
                      'px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200',
                      selectedKeywords.includes(keyword)
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                    )}
                  >
                    {keyword}
                  </button>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  placeholder="Agregar keyword personalizado..."
                  value={customKeyword}
                  onChange={(e) => setCustomKeyword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomKeyword())}
                />
                <Button type="button" variant="outline" onClick={addCustomKeyword}>
                  Agregar
                </Button>
              </div>
              {selectedKeywords.length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm text-muted-foreground mb-2">Keywords seleccionados:</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedKeywords.map((keyword) => (
                      <Badge key={keyword} variant="secondary" className="cursor-pointer" onClick={() => toggleKeyword(keyword)}>
                        {keyword} ×
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants} className="md:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                Curriculum Vitae
              </CardTitle>
              <CardDescription>Sube tu CV para análisis y mejora de postulaciones</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-input rounded-xl p-8 text-center hover:bg-accent/50 transition-colors cursor-pointer">
                <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <Upload className="h-6 w-6 text-primary" />
                </div>
                <p className="font-medium text-foreground mb-1">Arrastra tu CV aquí o haz clic para seleccionar</p>
                <p className="text-sm text-muted-foreground">PDF, DOC o DOCX hasta 10MB</p>
                <Button variant="outline" className="mt-4">
                  Seleccionar archivo
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants} className="md:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-primary" />
                Notificaciones
              </CardTitle>
              <CardDescription>Configura cómo quieres recibir alertas</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { key: 'newJobs', label: 'Nuevos jobs que coincidan', description: 'Recibe alertas cuando encontramos nuevas oportunidades' },
                  { key: 'interviewReminders', label: 'Recordatorios de entrevistas', description: 'Te avisamos antes de tus entrevistas programadas' },
                  { key: 'weeklyDigest', label: 'Resumen semanal', description: 'Un email semanal con tu progreso y nuevas oportunidades' },
                ].map(({ key, label, description }) => (
                  <div key={key} className="flex items-start justify-between">
                    <div>
                      <p className="font-medium">{label}</p>
                      <p className="text-sm text-muted-foreground">{description}</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={profile.preferences.notifications[key as keyof typeof profile.preferences.notifications]}
                        onChange={(e) => setProfile({
                          ...profile,
                          preferences: {
                            ...profile.preferences,
                            notifications: {
                              ...profile.preferences.notifications,
                              [key]: e.target.checked
                            }
                          }
                        })}
                      />
                      <div className={cn(
                        'w-11 h-6 bg-muted peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full',
                        'peer peer-checked:after:translate-x-full peer-checked:after:border-white',
                        'after:content-[""] after:absolute after:top-[2px] after:left-[2px]',
                        'after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5',
                        'after:transition-all peer-checked:bg-primary'
                      )} />
                    </label>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  );
}
