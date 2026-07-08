import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-10', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-10.component.html'})
export class Screen10Component {
  api = inject(PortalApiService);
  screen = {"actions":["Activar metodo","Regenerar respaldo"],"fields":["Metodo","Estado","Respaldo"],"moduleName":"Seguridad","records":[["SMS","activo","si"],["App autenticadora","pendiente","no"]],"route":"/seguridad/mfa","summary":"Dispositivos y MFA: implementa campos Metodo, Estado, Respaldo y acciones Activar metodo, Regenerar respaldo.","title":"Dispositivos y MFA"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
