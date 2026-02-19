-- Migration: Add richer data fields to leads table

ALTER TABLE public.leads 
ADD COLUMN IF NOT EXISTS managers_info JSONB DEFAULT '[]'::jsonb;
