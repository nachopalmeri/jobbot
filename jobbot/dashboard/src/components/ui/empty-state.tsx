'use client';

import { motion } from 'framer-motion';
import { Briefcase, Search, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: 'jobs' | 'search' | 'default';
  action?: {
    label: string;
    href: string;
  };
}

export function EmptyState({ title, description, icon = 'default', action }: EmptyStateProps) {
  const icons = {
    jobs: Briefcase,
    search: Search,
    default: Briefcase,
  };

  const Icon = icons[icon];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="flex flex-col items-center justify-center py-16 px-4 text-center"
    >
      <div className="h-20 w-20 rounded-full bg-muted/50 flex items-center justify-center mb-6">
        <Icon className="h-10 w-10 text-muted-foreground/50" />
      </div>
      <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
      <p className="text-muted-foreground max-w-sm mb-6">{description}</p>
      {action && (
        <Button asChild>
          <Link href={action.href}>
            <Plus className="mr-2 h-4 w-4" />
            {action.label}
          </Link>
        </Button>
      )}
    </motion.div>
  );
}
