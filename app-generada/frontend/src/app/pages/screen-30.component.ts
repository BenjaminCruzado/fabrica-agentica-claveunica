import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-30', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-30.component.html'})
export class Screen30Component {
  api = inject(PortalApiService);
  screen = {"actions":["Ver control","Descargar reporte"],"fields":["Control","Cobertura","Riesgo"],"moduleName":"Auditoria","records":[["Proteccion de datos","100%","bajo"],["Permisos ciudadanos","96%","medio"]],"route":"/auditoria/compliance","summary":"Panel de seguridad: implementa campos Control, Cobertura, Riesgo y acciones Ver control, Descargar reporte.","title":"Panel de seguridad"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
