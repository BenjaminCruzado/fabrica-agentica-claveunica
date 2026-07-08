import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-21', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-21.component.html'})
export class Screen21Component {
  api = inject(PortalApiService);
  screen = {"actions":["Adjuntar documento","Enviar comentario"],"fields":["Folio","Hito","Documento"],"moduleName":"Expedientes","records":[["EXP-1001","subsanacion","pendiente"],["EXP-1001","recepcion","completa"]],"route":"/expedientes/case-detail","summary":"Detalle de expediente: implementa campos Folio, Hito, Documento y acciones Adjuntar documento, Enviar comentario.","title":"Detalle de expediente"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
