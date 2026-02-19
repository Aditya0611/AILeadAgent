-- Create the leads table for storing lead generation data
CREATE TABLE IF NOT EXISTS public.leads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    company TEXT,
    website TEXT,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    twitter_url TEXT,
    source TEXT NOT NULL,
    description TEXT,
    qualification_score DECIMAL(3,1) DEFAULT 0.0 CHECK (qualification_score >= 0.0 AND qualification_score <= 10.0),
    qualification_reasoning TEXT,
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'qualified', 'contacted', 'interested', 'rejected')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on website for faster lookups
CREATE INDEX IF NOT EXISTS idx_leads_website ON public.leads(website);

-- Create index on created_at for sorting
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON public.leads(created_at DESC);

-- Create index on status for filtering
CREATE INDEX IF NOT EXISTS idx_leads_status ON public.leads(status);

-- Enable Row Level Security (RLS)
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;

-- Create policy to allow service role full access
CREATE POLICY "Service role has full access" ON public.leads
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON public.leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
