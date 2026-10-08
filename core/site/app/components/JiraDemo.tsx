'use client';

import { useMemo, useState } from 'react';
import {
  ArrowsClockwise,
  Check,
  FileMd,
  Kanban,
  LockKey,
  MagnifyingGlass,
  UserCircle,
} from '@phosphor-icons/react';

const issues = [
  { id: 'MDM-42', title: 'Vista de disponibilidad de flota', column: 'Por hacer', owner: 'MR' },
  { id: 'MDM-43', title: 'Filtros por base operativa', column: 'Por hacer', owner: 'AL' },
  { id: 'MDM-44', title: 'Detalle de vehículo', column: 'En curso', owner: 'JC' },
  { id: 'MDM-41', title: 'Priorizar incidencias críticas', column: 'En revisión', owner: 'MM' },
  { id: 'MDM-45', title: 'Pruebas de accesibilidad', column: 'Hecho', owner: 'LG' },
];

const columns = ['Por hacer', 'En curso', 'En revisión', 'Hecho'];

export function JiraDemo() {
  const [selectedId, setSelectedId] = useState('MDM-41');
  const [done, setDone] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const selected = useMemo(() => issues.find((issue) => issue.id === selectedId) ?? issues[3], [selectedId]);

  const confirmTransition = () => {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    setDone(true);
    setConfirming(false);
  };

  return (
    <div className="jira-integration">
      <aside className="jira-source">
        <p>MARKDOWN DEL PROYECTO</p>
        <strong>Fuente de verdad</strong>
        {['01_intencion.md', '03_requisitos.md', '04_decisiones.md', '05_criterios_aceptacion.md'].map((file) => (
          <span key={file}><FileMd weight="duotone" />{file}</span>
        ))}
        <div className="rovo-peer">
          <ArrowsClockwise weight="duotone" />
          <span>ATLASSIAN ROVO<small>Peer externo</small></span>
        </div>
        <div className="receipt-row"><b>SYNC-014</b><b>RPT-008</b></div>
        <small className="reconcile-copy">Releer y reconciliar · sin sincronización automática</small>
      </aside>

      <div className="jira-surface">
        <div className="jira-topbar">
          <span className="jira-wordmark"><Kanban weight="fill" /> Jira</span>
          <span>Tu trabajo</span><span>Proyectos</span><span>Filtros</span>
          <label><MagnifyingGlass /><input aria-label="Buscar tickets" placeholder="Buscar" /></label>
        </div>
        <div className="jira-project-title">
          <div><small>Proyectos / Mendiara Mobility / Tablero</small><h3>Mendiara Mobility · Desarrollo de aplicación</h3></div>
          <span>PROYECTO FICTICIO</span>
        </div>
        <div className="jira-body">
          <div className="kanban-board">
            {columns.map((column) => (
              <section className="kanban-column" key={column} aria-label={column}>
                <h4>{column}<span>{issues.filter((issue) => (issue.id === 'MDM-41' && done ? 'Hecho' : issue.column) === column).length}</span></h4>
                {issues
                  .filter((issue) => (issue.id === 'MDM-41' && done ? 'Hecho' : issue.column) === column)
                  .map((issue) => (
                    <button
                      type="button"
                      className={`jira-card ${selectedId === issue.id ? 'selected' : ''}`}
                      key={issue.id}
                      onClick={() => setSelectedId(issue.id)}
                    >
                      <b>{issue.id}</b>
                      <span>{issue.title}</span>
                      <small><UserCircle weight="fill" />{issue.owner}</small>
                    </button>
                  ))}
              </section>
            ))}
          </div>

          <aside className="jira-ticket">
            <div className="ticket-code"><span>{selected.id}</span><LockKey /></div>
            <h3>{selected.title}</h3>
            <dl>
              <div><dt>Estado</dt><dd>{selected.id === 'MDM-41' ? (done ? 'HECHO' : 'EN REVISIÓN') : selected.column.toUpperCase()}</dd></div>
              <div><dt>Incremento</dt><dd>INC-001</dd></div>
              <div><dt>Requisito</dt><dd>FR-017</dd></div>
              <div><dt>Criterio</dt><dd>AC-021</dd></div>
              <div><dt>Tarea LKS-SDD</dt><dd>TASK-008</dd></div>
              <div><dt>Evidencia</dt><dd>EVID-005</dd></div>
            </dl>
            <div className="ticket-activity">
              <p><Check weight="bold" />Implementación iniciada</p>
              <p><Check weight="bold" />Tests superados</p>
              <p><Check weight="bold" />Verificación disponible</p>
            </div>
            {selected.id === 'MDM-41' && !done ? (
              <button type="button" className={confirming ? 'confirming' : ''} onClick={confirmTransition}>
                {confirming ? 'Confirmar transición humana' : 'Pasar a hecho'}
              </button>
            ) : selected.id === 'MDM-41' ? <p className="done-state"><Check weight="bold" /> Transición confirmada</p> : null}
            <span className="sr-only" aria-live="polite">{done ? 'MDM-41 se ha movido a Hecho' : ''}</span>
          </aside>
        </div>
      </div>
    </div>
  );
}
