-- Migration: Add richer data fields to leads table

ALTER TABLE public.leads 
ADD COLUMN IF NOT EXISTS employee_count TEXT,
ADD COLUMN IF NOT EXISTS funding_info TEXT,
ADD COLUMN IF NOT EXISTS industry_tags TEXT[],
ADD COLUMN IF NOT EXISTS sentiment_score DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS social_media_links JSONB DEFAULT '{}'::jsonb;

-- Update the full text search or other indexes if needed
CREATE INDEX IF NOT EXISTS idx_leads_industry_tags ON public.leads USING GIN (industry_tags);
