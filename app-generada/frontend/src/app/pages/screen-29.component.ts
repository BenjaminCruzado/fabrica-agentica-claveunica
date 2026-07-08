import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-29', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-29.component.html'})
export class Screen29Component {
  api = inject(PortalApiService);
  screen = {"actions":["Reintentar","Ver detalle"],"fields":["Servicio","Estado","Latencia"],"moduleName":"Portal ciudadano","records":[["ClaveUnica","operativo","120ms"],["DDU","degradado","650ms"]],"route":"/portal/integration-status","summary":"Estado de integraciones: implementa campos Servicio, Estado, Latencia y acciones Reintentar, Ver detalle.","title":"Estado de integraciones"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
