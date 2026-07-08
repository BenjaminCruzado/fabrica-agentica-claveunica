import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-28', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-28.component.html'})
export class Screen28Component {
  api = inject(PortalApiService);
  screen = {"actions":["Generar CSV","Generar PDF"],"fields":["Rango","Formato","Estado"],"moduleName":"Auditoria","records":[["Ultimos 30 dias","CSV","listo"],["Ultimos 90 dias","PDF","pendiente"]],"route":"/auditoria/audit-export","summary":"Exportacion de auditoria: implementa campos Rango, Formato, Estado y acciones Generar CSV, Generar PDF.","title":"Exportacion de auditoria"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
