import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-15', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-15.component.html'})
export class Screen15Component {
  api = inject(PortalApiService);
  screen = {"actions":["Descargar adjunto","Acusar recibo"],"fields":["Remitente","Folio","Adjuntos"],"moduleName":"Notificaciones","records":[["Registro Civil","MSG-1001","1 archivo"],["Municipalidad","MSG-1002","sin adjuntos"]],"route":"/notificaciones/message-detail","summary":"Detalle de mensaje: implementa campos Remitente, Folio, Adjuntos y acciones Descargar adjunto, Acusar recibo.","title":"Detalle de mensaje"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
