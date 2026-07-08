import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-19', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-19.component.html'})
export class Screen19Component {
  api = inject(PortalApiService);
  screen = {"actions":["Exportar historial","Ver detalle"],"fields":["Fecha","Accion","Actor"],"moduleName":"Autorizaciones","records":[["2026-07-01","revocar","ciudadano"],["2026-06-20","autorizar","ciudadano"]],"route":"/autorizaciones/consent-history","summary":"Historial de autorizaciones: implementa campos Fecha, Accion, Actor y acciones Exportar historial, Ver detalle.","title":"Historial de autorizaciones"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
