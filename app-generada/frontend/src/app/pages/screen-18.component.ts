import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-18', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-18.component.html'})
export class Screen18Component {
  api = inject(PortalApiService);
  screen = {"actions":["Autorizar","Rechazar"],"fields":["Solicitante","Finalidad","Duracion"],"moduleName":"Autorizaciones","records":[["Servicio demo","validar domicilio","30 dias"],["Salud demo","contactabilidad","90 dias"]],"route":"/autorizaciones/consent-request","summary":"Solicitud de autorizacion: implementa campos Solicitante, Finalidad, Duracion y acciones Autorizar, Rechazar.","title":"Solicitud de autorizacion"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
