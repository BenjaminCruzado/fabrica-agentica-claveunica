import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-22', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-22.component.html'})
export class Screen22Component {
  api = inject(PortalApiService);
  screen = {"actions":["Ver evidencia","Descargar bitacora"],"fields":["Fecha","Evento","Resultado"],"moduleName":"Expedientes","records":[["2026-07-01","creacion","ok"],["2026-07-02","revision","observado"]],"route":"/expedientes/case-timeline","summary":"Linea de tiempo: implementa campos Fecha, Evento, Resultado y acciones Ver evidencia, Descargar bitacora.","title":"Linea de tiempo"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
