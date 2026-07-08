import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-05', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-05.component.html'})
export class Screen05Component {
  api = inject(PortalApiService);
  screen = {"actions":["Continuar solicitud","Descargar requisitos"],"fields":["Requisitos","Costo","Tiempo estimado"],"moduleName":"Portal ciudadano","records":[["Identidad","ClaveUnica","obligatorio"],["Documento","Comprobante","opcional"]],"route":"/portal/service-detail","summary":"Detalle de tramite: implementa campos Requisitos, Costo, Tiempo estimado y acciones Continuar solicitud, Descargar requisitos.","title":"Detalle de tramite"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
