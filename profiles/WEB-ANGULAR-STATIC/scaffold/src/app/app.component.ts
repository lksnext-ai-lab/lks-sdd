import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-root',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main>
      <p class="eyebrow">LKS-SDD · perfil de referencia</p>
      <h1>{{ title }}</h1>
      <p>SPA Angular estática con contrato reproducible y verificable.</p>
      <button type="button" (click)="increment()">
        Verificación local: {{ count }}
      </button>
    </main>
  `,
})
export class AppComponent {
  readonly title = 'Angular listo para especificar';
  count = 0;

  increment(): void {
    this.count += 1;
  }
}
