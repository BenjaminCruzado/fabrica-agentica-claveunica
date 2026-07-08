import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-26', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-26.component.html'})
export class Screen26Component {
  api = inject(PortalApiService);
  screen = {"actions":["Filtrar","Exportar"],"fields":["Fecha","IP","Resultado"],"moduleName":"Auditoria","records":[["2026-07-08","190.10.10.1","permitido"],["2026-07-07","181.20.20.2","bloqueado"]],"route":"/auditoria/access-log","summary":"Bitacora de accesos: implementa campos Fecha, IP, Resultado y acciones Filtrar, Exportar.","title":"Bitacora de accesos"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
