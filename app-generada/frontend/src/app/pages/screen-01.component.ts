import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-01', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-01.component.html'})
export class Screen01Component {
  api = inject(PortalApiService);
  screen = {"actions":["Ingresar","Recuperar acceso"],"fields":["RUN","ClaveUnica","Codigo MFA"],"moduleName":"Seguridad","records":[["RUN demo","12.345.678-9","valido"],["MFA","SMS","pendiente"]],"route":"/seguridad/auth-login","summary":"Ingreso ClaveUnica: implementa campos RUN, ClaveUnica, Codigo MFA y acciones Ingresar, Recuperar acceso.","title":"Ingreso ClaveUnica"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
