import { describe, it, expect, beforeEach } from 'vitest';
import type { Job, JobStatus } from '../src/types';

const mockJob: Job = {
  id: '1',
  title: 'Senior Developer',
  company: 'TechCorp',
  location: 'Remote',
  modality: 'remote',
  status: 'applied',
  url: 'https://example.com/job',
  createdAt: '2024-01-15',
  updatedAt: '2024-01-15',
  salary: '$80k - $120k',
};

describe('Job Types', () => {
  it('should have valid job status values', () => {
    const validStatuses: JobStatus[] = ['applied', 'interview', 'offer', 'rejected', 'saved'];
    expect(validStatuses).toContain(mockJob.status);
  });

  it('should have required fields', () => {
    expect(mockJob.id).toBeDefined();
    expect(mockJob.title).toBeDefined();
    expect(mockJob.company).toBeDefined();
    expect(mockJob.url).toBeDefined();
  });

  it('should have valid modality', () => {
    const validModalities = ['remote', 'hybrid', 'onsite'];
    expect(validModalities).toContain(mockJob.modality);
  });
});

describe('Job Filtering', () => {
  const mockJobs: Job[] = [
    { ...mockJob, title: 'Python Developer', company: 'TechCorp' },
    { ...mockJob, id: '2', title: 'React Developer', company: 'StartupXYZ' },
    { ...mockJob, id: '3', title: 'Full Stack', company: 'TechCorp', status: 'interview' },
  ];

  it('should filter by search query', () => {
    const filtered = mockJobs.filter(j => 
      j.title.toLowerCase().includes('python') ||
      j.company.toLowerCase().includes('python')
    );
    expect(filtered).toHaveLength(1);
    expect(filtered[0].title).toBe('Python Developer');
  });

  it('should filter by status', () => {
    const filtered = mockJobs.filter(j => j.status === 'interview');
    expect(filtered).toHaveLength(1);
    expect(filtered[0].id).toBe('3');
  });

  it('should filter by company', () => {
    const filtered = mockJobs.filter(j => j.company === 'TechCorp');
    expect(filtered).toHaveLength(2);
  });
});

describe('Job Status Configuration', () => {
  const getStatusConfig = (status: JobStatus) => {
    const configs = {
      applied: { label: 'Aplicado', color: 'blue' },
      interview: { label: 'Entrevista', color: 'amber' },
      offer: { label: 'Oferta', color: 'green' },
      rejected: { label: 'Rechazado', color: 'red' },
      saved: { label: 'Guardado', color: 'gray' },
    };
    return configs[status];
  };

  it('should return correct config for each status', () => {
    expect(getStatusConfig('applied').label).toBe('Aplicado');
    expect(getStatusConfig('interview').color).toBe('amber');
    expect(getStatusConfig('offer').label).toBe('Oferta');
    expect(getStatusConfig('rejected').color).toBe('red');
    expect(getStatusConfig('saved').label).toBe('Guardado');
  });
});
