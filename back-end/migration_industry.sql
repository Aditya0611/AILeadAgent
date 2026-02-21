-- Migration: Add industry field to leads table
ALTER TABLE public.leads 
ADD COLUMN IF NOT EXISTS industry TEXT;

-- Create an index for industry filtering if needed
CREATE INDEX IF NOT EXISTS idx_leads_industry ON public.leads(industry);
