import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-14', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-14.component.html'})
export class Screen14Component {
  api = inject(PortalApiService);
  screen = {"actions":["Marcar leida","Responder"],"fields":["Asunto","Prioridad","Acuse"],"moduleName":"Notificaciones","records":[["Vencimiento tramite","alta","pendiente"],["Actualizacion DDU","media","recibido"]],"route":"/notificaciones/inbox","summary":"Bandeja de notificaciones: implementa campos Asunto, Prioridad, Acuse y acciones Marcar leida, Responder.","title":"Bandeja de notificaciones"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
