'use client';

import { useState } from 'react';
import {
  Browser,
  CheckCircle,
  Code,
  Funnel,
  MapTrifold,
  Mountains,
  Path,
  SlidersHorizontal,
  Truck,
  WarningCircle,
} from '@phosphor-icons/react';

const tabs = [
  { id: 'flota', label: 'Flota', icon: Truck },
  { id: 'rutas', label: 'Rutas', icon: Path },
  { id: 'incidencias', label: 'Incidencias', icon: WarningCircle },
];

const rows = [
  ['MM-E101', 'Donostia → Bilbao', 'En ruta', '72%'],
  ['MM-E087', 'Vitoria → Pamplona', 'En ruta', '64%'],
  ['MM-E056', 'Bilbao → Santander', 'En revisión', '58%'],
  ['MM-E043', 'Donostia → Irun', 'En parada', '45%'],
];

export function MendiaraDemo() {
  const [activeTab, setActiveTab] = useState('flota');
  const [annotation, setAnnotation] = useState(true);

  return (
    <div className="mendiara-demo">
      <div className="demo-toolbar">
        <span><Browser weight="duotone" /> Aplicación ejecutándose</span>
        <button type="button" onClick={() => setAnnotation((value) => !value)}>
          {annotation ? 'Ocultar anotación' : 'Anotar interfaz'}
        </button>
      </div>
      <div className="browser-frame">
        <div className="browser-bar" aria-hidden="true">
          <span className="browser-dot" /><span className="browser-dot" /><span className="browser-dot" />
          <span className="browser-address">app.mendiara.demo/operaciones/{activeTab}</span>
        </div>
        <div className="mendiara-app">
          <aside className="mendiara-sidebar">
            <div className="mendiara-brand">
              <Mountains weight="bold" />
              <span>MENDIARA<small>MOBILITY</small></span>
            </div>
            <p>Operaciones</p>
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                type="button"
                key={id}
                className={activeTab === id ? 'active' : ''}
                onClick={() => setActiveTab(id)}
              >
                <Icon weight={activeTab === id ? 'fill' : 'regular'} />{label}
              </button>
            ))}
            <button type="button"><SlidersHorizontal />Configuración</button>
          </aside>

          <div className="mendiara-workspace">
            <div className="mendiara-heading">
              <div>
                <span>DEMO · CLIENTE FICTICIO</span>
                <h3>{activeTab === 'incidencias' ? 'Gestión de incidencias' : activeTab === 'rutas' ? 'Planificación de rutas' : 'Operaciones de flota'}</h3>
              </div>
              <button type="button"><Funnel /> Filtros</button>
            </div>

            <div className="mendiara-photo">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/assets/mendiara-fleet.png" alt="Flota ficticia de vehículos eléctricos en un centro de movilidad de montaña" />
              <div className="photo-caption">
                <MapTrifold weight="duotone" />
                <span>Red operativa norte<small>Actualizado hace 2 min</small></span>
              </div>
            </div>

            <div className="fleet-metrics">
              <div><span>Vehículos activos</span><strong>128</strong><small>de 142</small></div>
              <div><span>En ruta</span><strong>89</strong><small>69,5%</small></div>
              <div className="critical-metric"><span>Incidencias abiertas</span><strong>12</strong><small>7 críticas</small></div>
              <div><span>Disponibilidad</span><strong>94,2%</strong><small>+2,1% vs. ayer</small></div>
            </div>

            <div className="fleet-table" role="table" aria-label="Vehículos en ruta">
              <div className="fleet-row fleet-head" role="row">
                <span>Vehículo</span><span>Ruta</span><span>Estado</span><span>Batería</span>
              </div>
              {rows.map((row) => (
                <div className="fleet-row" role="row" key={row[0]}>
                  {row.map((cell) => <span role="cell" key={cell}>{cell}</span>)}
                </div>
              ))}
            </div>

            {annotation ? (
              <div className="annotation-note" role="note">
                <span className="annotation-pin" />
                <strong>Dar más visibilidad a las incidencias críticas</strong>
                <small>Nuevo requisito → reconciliar spec</small>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="execution-strip" aria-label="Estado de ejecución">
        <span><Code weight="duotone" /> Código actualizado</span>
        <span><CheckCircle weight="fill" /> Tests OK · 3/3</span>
        <span><WarningCircle weight="duotone" /> Feedback pendiente de reconciliación</span>
      </div>
    </div>
  );
}
