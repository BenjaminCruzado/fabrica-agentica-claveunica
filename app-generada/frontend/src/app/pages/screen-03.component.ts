import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-03', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-03.component.html'})
export class Screen03Component {
  api = inject(PortalApiService);
  screen = {"actions":["Abrir tramite","Ver avisos"],"fields":["Tramites activos","Mensajes","Alertas"],"moduleName":"Portal ciudadano","records":[["Tramites","6","en curso"],["Alertas","2","criticas"],["Mensajes","11","sin leer"]],"route":"/portal/dashboard","summary":"Dashboard ciudadano: implementa campos Tramites activos, Mensajes, Alertas y acciones Abrir tramite, Ver avisos.","title":"Dashboard ciudadano"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
