import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-09', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-09.component.html'})
export class Screen09Component {
  api = inject(PortalApiService);
  screen = {"actions":["Cerrar sesion","Confiar dispositivo"],"fields":["Dispositivo","Ubicacion","Ultimo acceso"],"moduleName":"Seguridad","records":[["Notebook","Santiago","hoy"],["Movil","Valparaiso","ayer"]],"route":"/seguridad/sessions","summary":"Sesiones activas: implementa campos Dispositivo, Ubicacion, Ultimo acceso y acciones Cerrar sesion, Confiar dispositivo.","title":"Sesiones activas"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
