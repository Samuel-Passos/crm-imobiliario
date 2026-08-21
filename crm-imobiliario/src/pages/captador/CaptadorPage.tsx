import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { Globe, Search, Link as LinkIcon, Database, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react';
import './CaptadorPage.css';

export function CaptadorPage() {
  const [fase1Url, setFase1Url] = useState('');
  const [fase1Loading, setFase1Loading] = useState(false);
  
  const [fase2Url, setFase2Url] = useState('');
  const [fase2Loading, setFase2Loading] = useState(false);

  // Endpoint local da API do Captador (que roda na porta 8768)
  const API_URL = 'http://localhost:8768';

  const handleIniciarFase1 = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fase1Url.includes('olx.com.br')) {
      toast.error('Por favor, insira uma URL válida da OLX.');
      return;
    }

    setFase1Loading(true);
    try {
      const response = await fetch(`${API_URL}/fase1`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: fase1Url })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        toast.success(data.mensagem || 'Fase 1 iniciada! O robô está varrendo os links em background.', { duration: 5000 });
        setFase1Url('');
      } else {
        toast.error(data.mensagem || 'Erro ao iniciar Fase 1');
      }
    } catch (error) {
      toast.error('Erro de conexão com o robô (porta 8768).');
      console.error(error);
    } finally {
      setFase1Loading(false);
    }
  };

  const handleIniciarFase2 = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fase2Url.includes('olx.com.br')) {
      toast.error('Por favor, insira uma URL válida de anúncio da OLX.');
      return;
    }

    setFase2Loading(true);
    toast.loading('Iniciando extração (isso pode levar alguns segundos)...', { id: 'fase2-toast' });
    
    try {
      const response = await fetch(`${API_URL}/fase2-unico`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: fase2Url })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        toast.success(data.mensagem || 'Imóvel extraído e salvo com sucesso!', { id: 'fase2-toast', duration: 5000 });
        setFase2Url('');
      } else {
        toast.error(data.mensagem || 'Erro ao extrair imóvel', { id: 'fase2-toast' });
      }
    } catch (error) {
      toast.error('Erro de conexão com o robô.', { id: 'fase2-toast' });
      console.error(error);
    } finally {
      setFase2Loading(false);
    }
  };

  return (
    <div className="captador-container">
      <header className="captador-header">
        <div>
          <h1>
            <Globe className="header-icon" />
            Captador OLX Avançado
          </h1>
          <p>Configure e dispare robôs para extração automática de anúncios imobiliários da OLX.</p>
        </div>
      </header>

      <div className="captador-grid">
        
        {/* CARD FASE 1 */}
        <div className="card captador-card">
          <div className="captador-card-header" style={{ borderBottom: '1px solid var(--border)', paddingBottom: '1rem', marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <div className="icon-wrapper" style={{ background: 'rgba(59, 130, 246, 0.15)', color: 'var(--brand-500)', padding: '0.6rem', borderRadius: 'var(--radius-md)' }}>
              <Search size={22} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.2rem', marginBottom: '0.2rem' }}>Fase 1: Coleta em Massa</h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Varre uma página de pesquisa para encontrar links novos</p>
            </div>
          </div>
          
          <form onSubmit={handleIniciarFase1} className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
            <div>
              <label className="form-label" style={{ display: 'block', marginBottom: '0.5rem' }}>URL da Pesquisa (OLX)</label>
              <div className="input-with-icon">
                <LinkIcon size={18} className="input-icon" />
                <input
                  type="url"
                  className="form-input"
                  value={fase1Url}
                  onChange={(e) => setFase1Url(e.target.value)}
                  placeholder="Ex: https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/aluguel..."
                  style={{ paddingLeft: '2.5rem' }}
                  required
                />
              </div>
              <p style={{ marginTop: '0.8rem', fontSize: '0.8rem', color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <AlertTriangle size={14} />
                Dica: Faça a pesquisa na OLX (filtros de bairro, aluguel), copie o link e cole aqui.
              </p>
            </div>

            <button type="submit" className="btn btn-primary" disabled={fase1Loading || !fase1Url} style={{ width: '100%', marginTop: '0.5rem' }}>
              {fase1Loading ? (
                <><Loader2 className="spinner-icon" size={18} /> Iniciando Robô...</>
              ) : (
                'Iniciar Varredura em Background'
              )}
            </button>
          </form>
        </div>


        {/* CARD FASE 2 */}
        <div className="card captador-card">
          <div className="captador-card-header" style={{ borderBottom: '1px solid var(--border)', paddingBottom: '1rem', marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <div className="icon-wrapper" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--success)', padding: '0.6rem', borderRadius: 'var(--radius-md)' }}>
              <Database size={22} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.2rem', marginBottom: '0.2rem' }}>Fase 2: Extração Específica</h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Extrai todos os dados de um único anúncio imediatamente</p>
            </div>
          </div>
          
          <form onSubmit={handleIniciarFase2} className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
            <div>
              <label className="form-label" style={{ display: 'block', marginBottom: '0.5rem' }}>URL do Anúncio (OLX)</label>
              <div className="input-with-icon">
                <LinkIcon size={18} className="input-icon" />
                <input
                  type="url"
                  className="form-input"
                  value={fase2Url}
                  onChange={(e) => setFase2Url(e.target.value)}
                  placeholder="Ex: https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/linda-casa..."
                  style={{ paddingLeft: '2.5rem' }}
                  required
                />
              </div>
              <p style={{ marginTop: '0.8rem', fontSize: '0.8rem', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <CheckCircle size={14} />
                O sistema irá raspar o anúncio e salvá-lo na tabela imoveis.
              </p>
            </div>

            <button type="submit" className="btn btn-primary" disabled={fase2Loading || !fase2Url} style={{ width: '100%', marginTop: '0.5rem' }}>
              {fase2Loading ? (
                <><Loader2 className="spinner-icon" size={18} /> Extraindo e Salvando...</>
              ) : (
                'Extrair e Salvar Imóvel'
              )}
            </button>
          </form>
        </div>

      </div>
      
      {/* CARD INFO */}
      <div className="card info-card" style={{ marginTop: '2rem', background: 'rgba(255, 255, 255, 0.02)', borderColor: 'rgba(255, 255, 255, 0.05)' }}>
        <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Database size={18} color="var(--brand-500)" />
          Como funciona a prevenção de duplicadas no banco?
        </h3>
        <ul style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.6, paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <li>
            <strong style={{ color: 'var(--text-primary)' }}>Fase 1 (Links):</strong> Antes de salvar na fila, o robô verifica se a URL exata já existe na tabela <code>links_anuncios</code>. Se já existir, ele simplesmente ignora.
          </li>
          <li>
            <strong style={{ color: 'var(--text-primary)' }}>Fase 2 (Imóveis):</strong> O salvamento usa a função de <i style={{ color: 'var(--brand-500)' }}>UPSERT</i> baseada no <code>list_id</code> (código do anúncio OLX). Se o imóvel já estiver na base, ele atualiza as informações (ex: se o preço baixou). Se não estiver, cria um novo.
          </li>
        </ul>
      </div>

    </div>
  );
}
