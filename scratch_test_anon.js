const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: 'crm-imobiliario/.env' });

const supabase = createClient(process.env.VITE_SUPABASE_URL, process.env.VITE_SUPABASE_ANON_KEY);

async function test() {
    const { data, error } = await supabase.from('configuracoes_scraper').select('*');
    console.log("Data:", data, "Error:", error);
}
test();
